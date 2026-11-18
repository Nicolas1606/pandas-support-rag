from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from support_rag.settings import settings
from support_rag.evaluation.runner import run
from support_rag.utils.io import read,save
results=[]
for method in ['bm25','dense','hybrid']:
    print('Recuperação:',method,flush=True)
    folder=run(settings(),ROOT/'evaluation/cases.json','development',method,False,True)
    d=read(folder/'results.json')
    results.append({k:d[k] for k in ['method','hit_at_k','evidence_recall','mrr','errors','latency_median_ms','latency_p95_ms']})
    save(ROOT/'reports/development_retrieval.json',results)
    print(json.dumps(results[-1]),flush=True)
