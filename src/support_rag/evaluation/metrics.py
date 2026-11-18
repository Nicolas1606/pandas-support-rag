import math, random, statistics

def retrieval_metrics(hits, evidence):
    if not evidence:
        return {'hit_at_k': None, 'evidence_recall': None, 'sufficient': None, 'mrr': None}
    covered = []
    ranks = []
    for group in evidence:
        positions = []
        for i, hit in enumerate(hits, 1):
            for option in group:
                if hit['document_url'].endswith(option['url_suffix']) and all((t.casefold() in hit['text'].casefold() for t in option.get('terms', []))):
                    positions.append(i)
                    break
        covered.append(bool(positions))
        if positions:
            ranks.append(min(positions))
    return {'hit_at_k': any(covered), 'evidence_recall': sum(covered) / len(covered), 'sufficient': all(covered), 'mrr': 1 / min(ranks) if ranks else 0}

def percentile(values, p):
    if not values:
        return None
    x = sorted(values)
    i = (len(x) - 1) * p
    lo = math.floor(i)
    hi = math.ceil(i)
    return x[lo] + (x[hi] - x[lo]) * (i - lo)

def wilson(success, n):
    if not n:
        return None
    z = 1.96
    p = success / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    delta = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0, center - delta), min(1, center + delta)]

def paired_bootstrap(deltas, seed=42, repeats=2000):
    if not deltas:
        return None
    rng = random.Random(seed)
    means = [statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(repeats)]
    return [percentile(means, 0.025), percentile(means, 0.975)]
