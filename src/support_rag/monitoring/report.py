from collections import Counter
from pathlib import Path
from support_rag.utils.io import read
from support_rag.evaluation.metrics import percentile

def report(data_dir):
    rows = [read(p) for p in (Path(data_dir) / 'logs').glob('*.json')]
    return {'requests': len(rows), 'actions': dict(Counter((r['action'] for r in rows))), 'errors': dict(Counter((r.get('error_type') for r in rows if r.get('error_type')))), 'latency_median_ms': percentile([r['total_ms'] for r in rows], 0.5), 'latency_p95_ms': percentile([r['total_ms'] for r in rows], 0.95), 'warning': 'Logs não medem correção factual. Revisão humana é necessária.'}
