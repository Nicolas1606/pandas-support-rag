import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from support_rag.settings import settings
from support_rag.pipeline import Pipeline
from support_rag.utils.io import save
p=Pipeline(settings())
q='Como validar um merge muitos para um usando validate?'
out=p.answer(q,method='bm25')
save(ROOT/'reports/real_smoke.json',{'question':q,'output':out})
print(json.dumps(out,ensure_ascii=False,indent=2))
