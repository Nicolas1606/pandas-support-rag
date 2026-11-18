import re
QUOTE={'type':'object','additionalProperties':False,'required':['source_id','quote'],
       'properties':{'source_id':{'type':'string'},'quote':{'type':'string','minLength':20,'maxLength':1000}}}
CLAIM={'type':'object','additionalProperties':False,'required':['text','evidence_ids','evidence_quotes'],
       'properties':{'text':{'type':'string'},'evidence_ids':{'type':'array','minItems':1,'maxItems':3,'items':{'type':'string'}},
                     'evidence_quotes':{'type':'array','minItems':1,'maxItems':2,'items':QUOTE}}}
SCHEMA={'type':'object','additionalProperties':False,'required':['action','message','claims'],
        'properties':{'action':{'type':'string','enum':['answer','clarify','handoff']},
                      'message':{'type':'string'},'claims':{'type':'array','maxItems':2,'items':CLAIM}}}
AUDIT_SCHEMA={'type':'object','additionalProperties':False,
              'required':['supported','answers_question','portuguese','reason'],
              'properties':{**{k:{'type':'boolean'} for k in ['supported','answers_question','portuguese']},
                            'reason':{'type':'string'}}}
PLAN_SCHEMA={'type':'object','additionalProperties':False,'required':['scope','english_question','message'],
             'properties':{'scope':{'type':'string','enum':['inside','outside','unclear']},
                           'english_question':{'type':'string'},'message':{'type':'string'}}}
DRAFT_SCHEMA={'type':'object','additionalProperties':False,'required':['answer','source_ids'],
              'properties':{'answer':{'type':'string','maxLength':1500},
                            'source_ids':{'type':'array','maxItems':2,'items':{'type':'string'}}}}
def adapt_draft(value):
    if isinstance(value,dict) and set(value)=={'answer','source_ids'}:
        if not isinstance(value['answer'],str) or not isinstance(value['source_ids'],list):
            raise ValueError('Resposta inválida')
        if not value['answer'].strip() or not value['source_ids']:
            return {'action':'handoff','message':'Não encontrei suporte suficiente para formular uma orientação.','claims':[]}
        return {'action':'answer','message':'','claims':[{'text':value['answer'],'evidence_ids':value['source_ids']}]}
    return value

def attach_quotes(value,sources):
    lookup={s['id']:s['text'] for s in sources}
    for claim in value.get('claims',[]):
        if not isinstance(claim,dict):raise ValueError('Afirmação inválida')
        ids=claim.get('evidence_ids',[])
        if not isinstance(ids,list) or not all(isinstance(i,str) and i in lookup for i in ids):raise ValueError('Citação desconhecida')
        # O modelo escolhe IDs; o programa insere o trecho real, sem copiá-lo por geração.
        claim['evidence_quotes']=[{'source_id':i,'quote':lookup[i]} for i in ids]
    return value
def normalize(s):
    # Equivalência tipográfica, sem alterar palavras, números ou negações.
    s=s.translate(str.maketrans('', '', '“”‘’"\'`'))
    return re.sub(r'\s+',' ',s).strip()
def validate(value,hits):
    if not isinstance(value,dict) or set(value)!={'action','message','claims'}:raise ValueError('Estrutura inválida')
    if value['action'] not in ('answer','clarify','handoff'):raise ValueError('Ação inválida')
    if not isinstance(value['message'],str) or len(value['message'])>3000:raise ValueError('Mensagem inválida')
    claims=value['claims']
    if not isinstance(claims,list) or len(claims)>3:raise ValueError('Afirmações inválidas')
    if value['action']=='answer' and (not claims or value['message']):raise ValueError('Resposta exige afirmações e mensagem vazia')
    if value['action']!='answer' and (claims or not value['message'].strip()):raise ValueError('Motivo obrigatório')
    allowed={h['id']:h for h in hits}
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!={'text','evidence_ids','evidence_quotes'}:raise ValueError('Afirmação inválida')
        if not isinstance(claim['text'],str) or not 3<=len(claim['text'])<=2000:raise ValueError('Texto inválido')
        ids=claim['evidence_ids']
        if not isinstance(ids,list) or not 1<=len(ids)<=3 or not all(isinstance(x,str) for x in ids) or len(set(ids))!=len(ids) or not set(ids)<=set(allowed):raise ValueError('Citação inválida')
        quotes=claim['evidence_quotes']
        if not isinstance(quotes,list) or not 1<=len(quotes)<=4:raise ValueError('Trecho citado obrigatório')
        quoted_ids=set()
        for q in quotes:
            if not isinstance(q,dict) or set(q)!={'source_id','quote'}:raise ValueError('Trecho inválido')
            if q['source_id'] not in ids or not isinstance(q['quote'],str) or not 15<=len(q['quote'])<=1000:raise ValueError('Citação incompleta')
            if normalize(q['quote']) not in normalize(allowed[q['source_id']]['text']):raise ValueError('Trecho não pertence à fonte')
            quoted_ids.add(q['source_id'])
        if quoted_ids!=set(ids):raise ValueError('Fonte citada sem trecho de apoio')
    return value
def validate_audit(audit):
    if not isinstance(audit,dict) or set(audit)!={'supported','answers_question','portuguese','reason'}:raise ValueError('Auditoria inválida')
    if not all(type(audit[k]) is bool for k in ['supported','answers_question','portuguese']):raise ValueError('Auditoria deve usar booleanos')
    if not isinstance(audit['reason'],str):raise ValueError('Motivo inválido')
    return audit
