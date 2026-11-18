"""Replay the public intent benchmark against the frozen application."""
import json
import tempfile
from pathlib import Path
from pilot import ROOT, run

expected = [
    'merge_m1','merge_1m','merge_11','merge_null','merge_keys','csv_na_text',
    'csv_ids','csv_columns','csv_dates','numeric_coerce','numeric_raise','infer_objects',
    'merge_m1','csv_ids','csv_columns','merge_m1','merge_1m','merge_null','numeric_coerce','merge_11',
]

def evaluate(cases, contracts):
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'run'
        run(ROOT / cases, output)
        rows = json.loads((output / 'responses.json').read_text(encoding='utf8'))['rows']
    for row in rows:
        case, response = row['case'], row['response']
        wanted = contracts.get(case['id'], case['expected_action'])
        observed = response.get('contract_id') or response['action']
        yield dict(id=case['id'], expected=wanted, observed=observed, passed=wanted == observed)

if __name__ == '__main__':
    public = dict(zip((f'A{i}' for i in range(1,21)), expected))
    rows = list(evaluate('evaluation/auditoria_publica/casos.jsonl', public))
    rows.extend(evaluate('evaluation/inversao_v5.jsonl', {'I1':'merge_1m','I2':'merge_m1'}))
    rows.extend(evaluate('evaluation/identificadores_v52.jsonl', {'Z1':'csv_ids','Z2':'csv_ids'}))
    print(json.dumps(rows, indent=2))
    raise SystemExit(0 if all(row['passed'] for row in rows) else 1)
