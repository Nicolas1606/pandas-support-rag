import argparse, json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from support_rag.utils.io import read
from support_rag.evaluation.metrics import paired_bootstrap
p = argparse.ArgumentParser()
p.add_argument('a')
p.add_argument('b')
args = p.parse_args()
a, b = (read(args.a), read(args.b))
for key in ['corpus_id', 'cases_sha256', 'split']:
    if a[key] != b[key]:
        raise ValueError('Comparação incompatível: ' + key)
left = {r['case_id']: r for r in a['rows']}
groups = defaultdict(list)
for row in b['rows']:
    previous = left[row['case_id']]
    if previous.get('mrr') is not None and row.get('mrr') is not None:
        groups[row['family']].append(row['mrr'] - previous['mrr'])
deltas = [sum(x) / len(x) for x in groups.values()]
print(json.dumps({'families': len(deltas), 'delta_mrr': sum(deltas) / len(deltas) if deltas else None, 'bootstrap_family_95': paired_bootstrap(deltas), 'warning': 'Diagnóstico pareado; não prova ganho de negócio.'}, indent=2))
