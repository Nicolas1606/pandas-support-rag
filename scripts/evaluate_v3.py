"""Run public regressions and a labeled, replay-only legacy comparison."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from support_rag.bootstrap import bootstrap
from support_rag.pipeline import Pipeline
from support_rag.settings import settings
from support_rag.utils.io import read, save
from support_rag.evaluation.metrics import percentile


def main():
    config = settings()
    if config['answer_mode'] != 'controlled':
        raise SystemExit('Selecione o modo controlado.')
    bootstrap(config)
    engine = Pipeline(config)
    rows = []
    for q, context, version, action, contract in read(ROOT / 'evaluation/regression_v3.json'):
        output = engine.answer(q, context, version)
        passed = output['action'] == action and output.get('contract_id') == contract
        rows.append(dict(question=q, expected_action=action, expected_contract=contract,
                         passed=passed, output=output))

    cases = {r['id']: r for r in read(ROOT / 'evaluation/cases.json')}
    legacy = read(ROOT / 'reports/release_evaluation/test/results.json')
    replay = []
    for row in legacy['rows']:
        case = cases[row['case_id']]
        out = engine.answer(case['question'], case.get('context', ''), case.get('version'))
        replay.append(dict(case_id=case['id'], expected=case['expected_action'],
                           historical=row['output']['action'], observed=out['action'],
                           contract=out.get('contract_id')))
    totals = dict(public_cases=len(rows), public_passed=sum(r['passed'] for r in rows),
                  p95_pipeline_ms=percentile([r['output']['total_ms'] for r in rows], .95),
                  historical_n=len(replay),
                  historical_action_matches=sum(r['expected'] == r['historical'] for r in replay),
                  controlled_action_matches=sum(r['expected'] == r['observed'] for r in replay),
                  controlled_actions=dict(Counter(r['observed'] for r in replay)),
                  historical_is_independent=False, external_review='pending', user_study='pending')
    save(ROOT / 'reports/validation_v3.json', dict(summary=totals, public=rows, replay=replay))
    print(json.dumps(totals, indent=2))
    return int(not all(r['passed'] for r in rows))


if __name__ == '__main__':
    sys.exit(main())
