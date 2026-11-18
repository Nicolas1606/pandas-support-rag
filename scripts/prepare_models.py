import json,sys
from pathlib import Path
from urllib.request import urlopen,Request
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from support_rag.settings import settings
c=settings()
try:
    with urlopen(c['ollama_url']+'/api/tags',timeout=3) as r:tags=json.load(r)
except Exception:
    raise SystemExit('Inicie Ollama para Windows. Download: https://ollama.com/download/windows')
available={m['name'] for m in tags.get('models',[])}
for model in [c['model'],c['embedding_model']]:
    if model in available:
        print('Disponível:',model,flush=True);continue
    print('Baixando:',model,flush=True)
    req=Request(c['ollama_url']+'/api/pull',data=json.dumps({'model':model,'stream':False}).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=600) as r:print(json.load(r),flush=True)
print('Modelos prontos.')
