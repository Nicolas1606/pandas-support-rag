import json
from urllib.request import Request,urlopen
from urllib.parse import urlsplit

class Ollama:
    def __init__(self,url,model,timeout=90,options=None):
        if urlsplit(url).hostname not in ('localhost','127.0.0.1','::1'):raise ValueError('Servidor deve ser local')
        self.url=url.rstrip('/');self.model=model;self.timeout=timeout
        self.options=options or {'temperature':0,'seed':42,'num_ctx':8192,'num_predict':650}
    def ready(self):
        with urlopen(self.url+'/api/tags',timeout=3) as response:models=json.load(response).get('models',[])
        return any(m.get('name')==self.model for m in models)
    def generate(self,system,payload,schema):
        body={'model':self.model,'stream':False,'think':False,'format':schema,'keep_alive':'15m','options':self.options,
              'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]}
        req=Request(self.url+'/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=self.timeout) as response:data=json.load(response)
        if data.get('done_reason')=='length':raise ValueError('Saída truncada pelo limite de tokens')
        usage={k:data.get(k) for k in ['eval_count','prompt_eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration']}
        return json.loads(data['message']['content']),usage
