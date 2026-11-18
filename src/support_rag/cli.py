import argparse, json, platform, sys, time
from pathlib import Path
from support_rag.settings import settings, ROOT
from support_rag.utils.io import read, save
from support_rag.vectordb.store import Store
from support_rag.ingestion.loader import fetch
from support_rag.chunking.chunker import chunk_document
from support_rag.ingestion.cleaner import clean_document

def main():
    p = argparse.ArgumentParser(description='Assistente pandas: CRISP-DM e operação local')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('doctor')
    sub.add_parser('setup')
    sub.add_parser('rebuild')
    sub.add_parser('ingest')
    fixture = sub.add_parser('fixture', help='Corpus artificial apenas para teste de integração')
    activate = sub.add_parser('activate')
    activate.add_argument('corpus')
    activate.add_argument('--reason', required=True)
    index = sub.add_parser('index')
    index.add_argument('--corpus')
    server = sub.add_parser('serve')
    server.add_argument('--port', type=int, default=8000)
    search = sub.add_parser('search')
    search.add_argument('question')
    search.add_argument('--method', choices=['bm25', 'dense', 'hybrid'], default='bm25')
    ev = sub.add_parser('evaluate')
    ev.add_argument('--split', choices=['development', 'test'], default='development')
    ev.add_argument('--method', choices=['bm25', 'dense', 'hybrid'], default='bm25')
    ev.add_argument('--generate', action='store_true')
    ev.add_argument('--allow-unreviewed', action='store_true')
    sub.add_parser('monitor')
    args = p.parse_args()
    c = settings()
    store = Store(c['data_dir'])
    if args.cmd == 'setup':
        from support_rag.bootstrap import bootstrap
        bootstrap(c)
        print('Snapshot e índice preparados. Execute serve.')
    elif args.cmd == 'rebuild':
        import gzip
        from support_rag.ingestion.markdown import parse_snapshot
        with gzip.open(ROOT/'assets/raw_markdown.json.gz','rt',encoding='utf-8') as f:pages=json.load(f)
        chunks=[]
        for page in pages:
            chunks.extend(chunk_document(clean_document(parse_snapshot(page['path'],page['markdown'])),c['chunk_chars']))
        source_manifest=read(ROOT/'assets/manifest.json')
        corpus=store.create(chunks,source_manifest['sources'],{'kind':'rebuild_from_bundled_sources','parser':'markdown-heading-v1'})
        if corpus!=source_manifest['corpus_id']:raise ValueError('Reconstrução divergiu do snapshot. Não ativado.')
        print('Snapshot reconstruído e verificado:',corpus)
    elif args.cmd == 'doctor':
        print(json.dumps({'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(), 'data_dir': c['data_dir']}, indent=2))
    elif args.cmd == 'ingest':
        chunks = []
        sources = []
        for path in read(ROOT / 'configs/sources.json'):
            doc = clean_document(fetch(path))
            chunks.extend(chunk_document(doc, c['chunk_chars']))
            raw = doc.pop('raw_html')
            save(Path(c['data_dir']) / 'snapshots' / (doc['sha256'] + '.json'), dict(doc, raw_html=raw))
            sources.append({k: doc[k] for k in ['url', 'sha256', 'retrieved_at', 'version']})
        corpus = store.create(chunks, sources, {'kind': 'official_snapshot', 'parser': 'v2', 'chunk_chars': c['chunk_chars']})
        print('Candidato criado:', corpus, '— inspecione antes de activate')
    elif args.cmd == 'fixture':
        docs = read(ROOT / 'tests/fixtures/documents.json')
        chunks = [x for d in docs for x in chunk_document(d, c['chunk_chars'])]
        corpus = store.create(chunks, [], {'kind': 'synthetic_fixture', 'not_for_quality_claims': True})
        store.activate(corpus, 'Fixture artificial para testes')
        print(corpus)
    elif args.cmd == 'activate':
        print(json.dumps(store.activate(args.corpus, args.reason), indent=2))
    elif args.cmd == 'index':
        from support_rag.embeddings.embedder import Embedder
        manifest, chunks = store.load(args.corpus)
        e = Embedder(c['embedding_model'])
        texts = [x['title'] + ' ' + x['section'] + ' ' + x['text'] for x in chunks]
        vectors = e.encode(texts)
        save(store.path(manifest['corpus_id']) / 'vectors.json', {'model': c['embedding_model'], 'model_digest': e.digest, 'corpus_hash': manifest['chunks_sha256'], 'vectors': vectors})
        print('Índice pronto')
    elif args.cmd == 'serve':
        from support_rag.api.server import serve
        serve(args.port)
    elif args.cmd == 'search':
        from support_rag.pipeline import Pipeline
        print(json.dumps(Pipeline(c).search(args.question, method=args.method), ensure_ascii=False, indent=2))
    elif args.cmd == 'evaluate':
        from support_rag.evaluation.runner import run
        print(run(c, ROOT / 'evaluation/cases.json', args.split, args.method, args.generate, args.allow_unreviewed))
    else:
        from support_rag.monitoring.report import report
        print(json.dumps(report(c['data_dir']), ensure_ascii=False, indent=2))
