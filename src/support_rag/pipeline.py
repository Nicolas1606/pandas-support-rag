import threading,time,uuid
from pathlib import Path
from support_rag.utils.io import read,save,sha
from support_rag.vectordb.store import Store
from support_rag.retrieval.retriever import Retriever
from support_rag.llm.client import Ollama
from support_rag.llm.contracts import DRAFT_SCHEMA,AUDIT_SCHEMA,PLAN_SCHEMA,adapt_draft,attach_quotes,validate,validate_audit

def select_context(hits,budget=6000,max_sources=3,question=''):
    import re
    # Se a pergunta nomeia um parâmetro, prioriza sua definição de API.
    # Não traduz cardinalidades nem codifica respostas particulares.
    words=set(re.findall(r'\w+',question.casefold()))
    definitions=[]
    for hit in hits:
        label=hit['section'].split(' — ')[-1]
        match=re.match(r'([a-zA-Z_]\w*)\s+(?:str|bool|int|float|dict|list|tuple|scalar|array|label|object|callable)',label)
        if '/reference/api/' in hit['document_url'] and match and match.group(1).casefold() in words:
            definitions.append(hit)
    if definitions:
        named=[h for h in definitions if h['title'].split('.')[-1].casefold() in words]
        hits=named or definitions
    selected=[];seen=set();used=0
    for hit in hits:
        signature=sha(' '.join(hit['text'].split()))
        if signature in seen:continue
        if len(hit['text'])+used>budget:continue
        selected.append(hit);seen.add(signature);used+=len(hit['text'])
        if len(selected)>=max_sources:break
    return selected

class Pipeline:
    def __init__(self,config,llm=None):
        self.config=config;self.store=Store(config['data_dir'])
        self.manifest,self.chunks=self.store.load()
        self.controlled = None
        if config.get('answer_mode') == 'controlled':
            from support_rag.controlled import ControlledAnswers
            catalog = read(Path(config['root']) / 'configs/answer_contracts.json')
            self.controlled = ControlledAnswers(catalog, self.chunks, config['pandas_version'])
        self.retriever=Retriever(self.chunks);self.lock=threading.Lock();self.dense_lock=threading.Lock()
        self.llm=llm or Ollama(config['ollama_url'],config['model'],config['timeout'],config.get('generation_options'))
        self.prompt=(Path(__file__).parent/'prompts/template.txt').read_text(encoding='utf-8')
        self.verifier_prompt=(Path(__file__).parent/'prompts/verifier.txt').read_text(encoding='utf-8')
        self.planner_prompt=(Path(__file__).parent/'prompts/planner.txt').read_text(encoding='utf-8')
    def ensure_dense(self):
        with self.dense_lock:
            if self.retriever.embedder is not None:return
            from support_rag.embeddings.embedder import Embedder
            cache=read(self.store.path(self.manifest['corpus_id'])/'vectors.json')
            if cache['corpus_hash']!=self.manifest['chunks_sha256'] or cache['model']!=self.config['embedding_model']:raise ValueError('Índice incompatível')
            if len(cache['vectors'])!=len(self.chunks):raise ValueError('Índice incompleto')
            self.retriever.embedder=Embedder(self.config['embedding_model'],self.config['ollama_url'])
            if cache.get('model_digest') and cache['model_digest']!=self.retriever.embedder.digest:
                self.retriever.embedder=None
                raise ValueError('Pesos de embeddings mudaram. Reconstrua o índice.')
            self.retriever.vectors=cache['vectors']
    def check(self,question,context='',version=None,method=None):
        if not isinstance(question,str) or not 3<=len(question.strip())<=3000:raise ValueError('Pergunta deve ter 3–3000 caracteres')
        if not isinstance(context,str) or len(context)>3000:raise ValueError('Contexto inválido')
        if version is not None and (not isinstance(version,str) or len(version)>30):raise ValueError('Versão inválida')
        if method is not None and method not in ('bm25','dense','hybrid'):raise ValueError('Método inválido')
    def search(self,question,context='',method=None):
        method=method or self.config.get('default_method','bm25');self.check(question,context,method=method)
        if method!='bm25':self.ensure_dense()
        return self.retriever.search(question+' '+context,method,self.config['top_k'])
    def answer(self,question,context='',version=None,method=None):
        from support_rag.policy import clarification_needed
        method=method or self.config.get('default_method','bm25')
        self.check(question,context,version,method);started=time.perf_counter();rid=uuid.uuid4().hex
        result={'request_id':rid,'action':'handoff','message':'','claims':[],'sources':[],
                'corpus_id':self.manifest['corpus_id'],'method':method,'model':self.config['model'],
                'prompt_sha256':sha(self.prompt),'verifier_sha256':sha(self.verifier_prompt),
                'planner_sha256':sha(self.planner_prompt),
                'version':self.config['pandas_version'],'time':time.time(),'audit':None}
        if self.controlled is not None:
            result.update(self.controlled.answer(question, context, version))
            for key in ('prompt_sha256', 'verifier_sha256', 'planner_sha256'):
                result.pop(key)
            return self._finish(result, started)
        try:
            if version and version.strip()!=self.config['pandas_version']:
                result['message']='Versão não coberta. Encaminhe para revisão com a documentação correspondente.'
            elif clarification_needed(question,context):
                result.update(action='clarify',message=clarification_needed(question,context),policy_rule='missing_reproduction_context')
            elif not self.lock.acquire(blocking=False):
                result.update(action='error',message='Há uma geração em andamento. Aguarde sua conclusão.',error_type='busy')
            else:
                try:
                    plan=None
                    if self.config.get('use_planner',False):
                        self.llm.timeout=max(1,min(self.config['timeout'],120-(time.perf_counter()-started)))
                        plan,plan_usage=self.llm.generate(self.planner_prompt,{'question':question,'context':context},PLAN_SCHEMA)
                        if not isinstance(plan,dict) or plan.get('scope') not in ('inside','outside','unclear') or not isinstance(plan.get('english_question'),str) or len(plan['english_question'])>3000 or not isinstance(plan.get('message'),str):
                            raise ValueError('Interpretação inválida')
                        result['interpretation']=plan;result['planning_usage']=plan_usage
                    if plan and plan['scope']!='inside':
                        result.update(action='clarify' if plan['scope']=='unclear' else 'handoff',message=plan['message'] or 'Informe o contexto para revisão.')
                        return self._finish(result,started)
                    english=plan['english_question'] if plan else question
                    hits=self.search(english,context,method)
                    result['retrieval_ms']=(time.perf_counter()-started)*1000
                    sources=select_context(hits,self.config['context_chars'],self.config.get('max_sources',3),english)
                    result['sources']=sources;result['context_chars']=sum(len(s['text']) for s in sources)
                    if not sources or (method=='bm25' and hits[0]['score']<=0):
                        result['message']='Não encontrei evidência suficiente. Informe a função e o comportamento esperado.'
                    else:
                        payload={'question':english,'context':context,'version':self.config['pandas_version'],'evidence':sources}
                        generated=time.perf_counter()
                        self.llm.timeout=max(1,min(self.config['timeout'],120-(time.perf_counter()-started)))
                        value,usage=self.llm.generate(self.prompt,payload,DRAFT_SCHEMA)
                        result['generation_ms']=(time.perf_counter()-generated)*1000;result['usage']=usage
                        try:
                            value=adapt_draft(value)
                            validate(attach_quotes(value,sources),sources)
                        except ValueError as exc:
                            result.update(message='A resposta não passou pela verificação das citações. Consulte as fontes ou encaminhe para revisão.',validation_issue=str(exc),withheld_draft=value)
                        else:
                            if value['action']=='answer' and self.config.get('verify_answers',True):
                                audit_started=time.perf_counter()
                                self.llm.timeout=max(1,min(self.config['timeout'],120-(time.perf_counter()-started)))
                                audit,audit_usage=self.llm.generate(self.verifier_prompt,dict(payload,draft=value),AUDIT_SCHEMA)
                                validate_audit(audit)
                                result['audit']=audit;result['audit_usage']=audit_usage
                                result['audit_ms']=(time.perf_counter()-audit_started)*1000
                                if all(audit[k] for k in ['supported','answers_question','portuguese']):
                                    result.update(value)
                                else:
                                    result.update(message='Não foi possível confirmar uma orientação segura para este caso. Confira as fontes e encaminhe para revisão.',withheld_draft=value)
                            else:result.update(value)
                finally:self.lock.release()
        except Exception as exc:
            result.update(action='error',message='Não foi possível concluir. Verifique o modelo e o índice em Diagnóstico.',error_type=type(exc).__name__)
        return self._finish(result,started)
    def _finish(self,result,started):
        result['total_ms']=(time.perf_counter()-started)*1000
        save(Path(self.config['data_dir'])/'logs'/f"{result['request_id']}.json",result)
        return result
