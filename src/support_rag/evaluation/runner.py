import csv, time
from pathlib import Path
from support_rag.utils.io import read, save, sha, canonical
from support_rag.evaluation.metrics import retrieval_metrics, percentile
from support_rag.pipeline import Pipeline

def run(config, cases_path, split, method, generate=False, allow_unreviewed=False):
    cases = read(cases_path)
    chosen = [c for c in cases if c['split'] == split]
    if not chosen:
        raise ValueError('Conjunto vazio')
    if any((c.get('review_status') not in ('approved','assistant_source_review') for c in chosen)) and (not allow_unreviewed):
        raise ValueError('Referências não aprovadas. Revise ou use --allow-unreviewed para diagnóstico explícito.')
    pipeline = Pipeline(config)
    rows = []
    for case in chosen:
        started = time.perf_counter()
        row = {'case_id': case['id'], 'family': case['family'], 'topic': case['topic'], 'expected_action': case['expected_action']}
        try:
            hits = pipeline.search(case['question'], case.get('context', ''), method)
            row.update(retrieval_metrics(hits, case['evidence']))
            row['hits'] = hits
            if generate:
                row['output'] = pipeline.answer(case['question'], case.get('context', ''), case.get('version'), method)
                row['action_match'] = row['output']['action'] in case.get('acceptable_actions', [case['expected_action']])
        except Exception as exc:
            row['error'] = type(exc).__name__
        row['elapsed_ms'] = (time.perf_counter() - started) * 1000
        rows.append(row)
    summary = {'split': split, 'method': method, 'generation': generate, 'cases_sha256': sha(canonical(chosen)), 'reviewed': all((c.get('review_status') == 'approved' for c in chosen)), 'corpus_id': pipeline.manifest['corpus_id'], 'n': len(rows), 'errors': sum(('error' in r for r in rows)), 'latency_median_ms': percentile([r['elapsed_ms'] for r in rows], 0.5), 'latency_p95_ms': percentile([r['elapsed_ms'] for r in rows], 0.95), 'cold_first_ms': rows[0]['elapsed_ms'], 'rows': rows}
    for metric in ['hit_at_k', 'evidence_recall', 'sufficient', 'mrr']:
        values = [r[metric] for r in rows if r.get(metric) is not None]
        summary[metric] = {'mean': sum(values) / len(values) if values else None, 'denominator': len(values)}
    folder = Path(config['root']) / 'reports/runs' / str(time.time_ns())
    save(folder / 'results.json', summary)
    with (folder / 'manual_review.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['case_id', 'correctness_0_2', 'grounding_0_2', 'critical_error_0_1', 'citations_supported', 'citations_total', 'claims_cited', 'claims_requiring_citation', 'error_category', 'notes'])
        for c in chosen:
            writer.writerow([c['id']] + [''] * 9)
    return folder
