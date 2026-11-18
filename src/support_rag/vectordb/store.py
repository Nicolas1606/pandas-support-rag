import re, time
from pathlib import Path
from support_rag.utils.io import read, save, sha, canonical

class Store:

    def __init__(self, root):
        self.root = Path(root)

    def path(self, corpus):
        if not re.fullmatch('[a-f0-9]{16}', corpus):
            raise ValueError('Identificador inválido')
        return self.root / 'corpora' / corpus

    def create(self, chunks, sources, metadata=None):
        if not chunks:
            raise ValueError('Corpus vazio')
        checksum = sha(canonical(chunks))
        corpus = checksum[:16]
        folder = self.path(corpus)
        if folder.exists():
            self.load(corpus)
            return corpus
        save(folder / 'chunks.json', chunks)
        save(folder / 'manifest.json', {'corpus_id': corpus, 'chunks_sha256': checksum, 'sources': sources, 'metadata': metadata or {}})
        return corpus

    def load(self, corpus=None):
        corpus = corpus or read(self.root / 'active.json')['corpus_id']
        folder = self.path(corpus)
        manifest = read(folder / 'manifest.json')
        chunks = read(folder / 'chunks.json')
        if sha(canonical(chunks)) != manifest['chunks_sha256']:
            raise ValueError('Integridade inválida')
        if len({x['id'] for x in chunks}) != len(chunks):
            raise ValueError('IDs duplicados')
        return (manifest, chunks)

    def activate(self, corpus, reason):
        self.load(corpus)
        if not reason.strip():
            raise ValueError('Motivo obrigatório')
        previous = read(self.root / 'active.json')['corpus_id'] if (self.root / 'active.json').exists() else None
        event = {'previous': previous, 'corpus_id': corpus, 'reason': reason, 'time': time.time()}
        save(self.root / 'promotions' / f'{time.time_ns()}.json', event)
        save(self.root / 'active.json', event)
        return event
