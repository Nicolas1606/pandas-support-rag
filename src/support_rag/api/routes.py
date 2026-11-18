"""API FastAPI opcional; usa o mesmo pipeline e interface do servidor básico."""
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse,Response
from pydantic import BaseModel,Field
from support_rag.pipeline import Pipeline
from support_rag.settings import settings,ROOT
from support_rag.utils.io import save
from support_rag.bootstrap import bootstrap
from support_rag.monitoring.report import report

app=FastAPI(title='Pandas Support — RAG com evidências',version='3.0.0')
@lru_cache
def pipeline():
    c=settings();bootstrap(c);return Pipeline(c)
class Query(BaseModel):
    question:str=Field(min_length=3,max_length=3000)
    context:str=Field(default='',max_length=3000)
    version:str|None=Field(default=None,max_length=30)
    method:Literal['bm25','dense','hybrid']|None=None
class Feedback(BaseModel):
    request_id:str=Field(pattern='^[a-f0-9]{32}$')
    rating:Literal['useful','incorrect','incomplete']
@app.get('/',response_class=HTMLResponse)
def home():return (ROOT/'ui/index.html').read_text(encoding='utf-8')
@app.get('/favicon.ico',status_code=204)
def favicon():return Response(status_code=204)
@app.get('/health')
def health():return {'status':'alive'}
@app.get('/ready')
def ready():
    try:
        p=pipeline()
        try:llm=p.controlled is None and p.llm.ready()
        except Exception:llm=False
        return {'retrieval':True,'generation':llm,'answer_mode':p.config.get('answer_mode','experimental_llm'),'semantic':(p.store.path(p.manifest['corpus_id'])/'vectors.json').exists(),
                'corpus_id':p.manifest['corpus_id'],'default_method':p.config['default_method']}
    except Exception:raise HTTPException(503,'Corpus indisponível')
@app.get('/stats')
def stats():return report(settings()['data_dir'])
@app.post('/search')
def search(q:Query):
    try:return {'sources':pipeline().search(q.question,q.context,q.method)}
    except ValueError as exc:raise HTTPException(422,str(exc))
    except Exception:raise HTTPException(503,'Recuperação indisponível')
@app.post('/answer')
def answer(q:Query):
    try:return pipeline().answer(q.question,q.context,q.version,q.method)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except Exception:raise HTTPException(503,'Serviço indisponível')
@app.post('/feedback',status_code=201)
def feedback(f:Feedback):
    c=settings()
    if not (Path(c['data_dir'])/'logs'/f'{f.request_id}.json').exists():raise HTTPException(422,'Execução desconhecida')
    save(Path(c['data_dir'])/'feedback'/f'{uuid.uuid4().hex}.json',f.model_dump())
    return {'saved':True}
