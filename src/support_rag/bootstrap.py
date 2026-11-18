"""Preparação reproduzível a partir dos artefatos distribuídos."""
import gzip,json
from pathlib import Path
from support_rag.utils.io import save,read,sha,canonical
from support_rag.vectordb.store import Store
def bootstrap(config):
    data=Path(config['data_dir']);root=Path(config['root'])
    if (data/'active.json').exists():
        Store(data).load()
        return
    seed=root/'assets/corpus.json.gz'
    if not seed.exists():raise FileNotFoundError('Snapshot não encontrado. Execute ingest ou use o pacote de release.')
    with gzip.open(seed,'rt',encoding='utf-8') as f:bundle=json.load(f)
    store=Store(data);m=bundle['manifest']
    cid=store.create(bundle['chunks'],m['sources'],m.get('metadata',{}))
    if cid!=m['corpus_id']:raise ValueError('Snapshot inconsistente')
    vectors=root/'assets/vectors.json.gz'
    if vectors.exists():
        with gzip.open(vectors,'rt',encoding='utf-8') as f:v=json.load(f)
        if v['corpus_hash']!=m['chunks_sha256']:raise ValueError('Índice incompatível')
        save(store.path(cid)/'vectors.json',v)
    store.activate(cid,'Bootstrap do snapshot distribuído; consulte relatório de qualidade')
