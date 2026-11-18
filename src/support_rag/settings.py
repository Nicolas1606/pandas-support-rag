import os
from pathlib import Path
from support_rag.utils.io import read
ROOT = Path(__file__).resolve().parents[2]

def settings():
    c = read(ROOT / 'config.json')
    c['root'] = str(ROOT)
    c['data_dir'] = os.environ.get('RAG_DATA_DIR', str(ROOT / 'data'))
    c['ollama_url'] = os.environ.get('OLLAMA_URL', c['ollama_url'])
    c['answer_mode'] = os.environ.get('RAG_ANSWER_MODE', c.get('answer_mode', 'experimental_llm'))
    if c['answer_mode'] not in ('controlled', 'experimental_llm'):
        raise ValueError('RAG_ANSWER_MODE inválido')
    if c['answer_mode'] == 'controlled':
        c['default_method'] = 'bm25'
    return c
