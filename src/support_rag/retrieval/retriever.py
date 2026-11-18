import math, re
from collections import Counter

def tokenize(text):
    return re.findall('\\w+', text.casefold())

class BM25:

    def __init__(self, chunks, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs = [Counter(tokenize(c['title'] + ' ' + c['section'] + ' ' + c['text'])) for c in chunks]
        self.lengths = [sum(x.values()) for x in self.docs]
        self.avg = sum(self.lengths) / max(len(chunks), 1)
        self.df = Counter((t for d in self.docs for t in d))

    def scores(self, query):
        result = []
        n = len(self.docs)
        for d, length in zip(self.docs, self.lengths):
            score = 0.0
            for t in set(tokenize(query)):
                tf = d.get(t, 0)
                if tf:
                    score += math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5)) * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / max(self.avg, 1)))
            result.append(score)
        return result

def cosine(a, b):
    if len(a) != len(b):
        raise ValueError('Dimensões incompatíveis')
    denominator = math.sqrt(sum((x * x for x in a)) * sum((x * x for x in b)))
    return sum((x * y for x, y in zip(a, b))) / denominator if denominator else 0.0

def rank(scores):
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))

def rrf(rankings, size, constant=60):
    scores = [0.0] * size
    for ranking in rankings:
        for position, index in enumerate(ranking, 1):
            scores[index] += 1 / (constant + position)
    return scores

class Retriever:

    def __init__(self, chunks, embedder=None, vectors=None):
        self.chunks = chunks
        self.lexical = BM25(chunks)
        self.embedder = embedder
        self.vectors = vectors

    def search(self, question, method='bm25', k=5):
        if method not in ('bm25', 'dense', 'hybrid'):
            raise ValueError('Método inválido')
        lexical = self.lexical.scores(question)
        scores = lexical
        if method != 'bm25':
            if self.embedder is None or self.vectors is None:
                raise RuntimeError('Índice semântico indisponível')
            query = self.embedder.encode([question], query=True)[0]
            semantic = [cosine(query, v) for v in self.vectors]
            scores = semantic if method == 'dense' else rrf([rank(lexical)[:30], rank(semantic)[:30]], len(lexical))
        return [dict(self.chunks[i], score=scores[i]) for i in rank(scores)[:k]]
