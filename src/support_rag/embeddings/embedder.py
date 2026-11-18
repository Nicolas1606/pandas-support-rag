"""Embeddings locais via Ollama; sem instalação de PyTorch no projeto."""
import json, math
from urllib.request import Request, urlopen

class Embedder:
    def __init__(self, model='embeddinggemma:latest', url='http://127.0.0.1:11434', timeout=120):
        from urllib.parse import urlsplit
        if urlsplit(url).hostname not in ('localhost','127.0.0.1','::1'):
            raise ValueError('Servidor de embeddings deve ser local')
        self.model_name=model
        self.url=url.rstrip('/')
        self.timeout=timeout
        with urlopen(self.url+'/api/tags',timeout=5) as response:models=json.load(response).get('models',[])
        self.digest=next((m['digest'] for m in models if m['name']==model),None)
        if self.digest is None:raise ValueError('Modelo de embeddings não instalado')

    def encode(self, texts, query=False):
        if len(texts)>16:
            vectors=[]
            for start in range(0,len(texts),16):
                vectors.extend(self.encode(texts[start:start+16],query=query))
                print(f'Embeddings {min(start+16,len(texts))}/{len(texts)}',flush=True)
            return vectors
        prepared = [('task: search result | query: '+t) if query else ('title: pandas documentation | text: '+t) for t in texts]
        req=Request(self.url+'/api/embed',data=json.dumps({'model':self.model_name,'input':prepared,'truncate':False,'keep_alive':'15m'}).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=self.timeout) as response:
            values=json.load(response)['embeddings']
        if len(values)!=len(texts):raise ValueError('Número de embeddings incompatível')
        for vector in values:
            norm=math.sqrt(sum(v*v for v in vector))
            if not norm or not all(math.isfinite(v) for v in vector):raise ValueError('Vetor inválido')
            for i in range(len(vector)):vector[i]/=norm
        return values
