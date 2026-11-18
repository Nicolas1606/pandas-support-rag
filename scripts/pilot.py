"""Run private external cases and aggregate evidence entered by people."""
import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from support_rag.bootstrap import bootstrap
from support_rag.pipeline import Pipeline
from support_rag.settings import settings
from support_rag.utils.io import read, save


def fingerprint():
    paths = [*ROOT.joinpath('src').rglob('*.py'), *ROOT.joinpath('src').rglob('*.txt'),
             *ROOT.joinpath('configs').glob('*.json'), *ROOT.joinpath('assets').glob('*.gz'),
             ROOT/'ui/index.html', ROOT/'config.json', Path(__file__), ROOT/'docs/PILOTO.md']
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def run(cases_path, output):
    frozen = read(ROOT/'evaluation/pilot_freeze.json')
    if fingerprint() != frozen['sha256']:
        raise ValueError('A versão diverge do congelamento do piloto.')
    cases = [json.loads(line) for line in cases_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if not cases or len({r['id'] for r in cases}) != len(cases):
        raise ValueError('Informe casos com IDs exclusivos.')
    for row in cases:
        if row['expected_action'] not in ('answer', 'clarify', 'handoff') or not row['reference'].strip():
            raise ValueError('Ação esperada e referência são obrigatórias.')
    config = settings()
    if config['answer_mode'] != 'controlled':
        raise ValueError('Use o modo controlado para o piloto.')
    # Use the bundled corpus even when the operator has a different active corpus.
    import tempfile
    with tempfile.TemporaryDirectory() as path:
        config['data_dir'] = path
        bootstrap(config)
        engine = Pipeline(config)
        responses = [dict(case=r, response=engine.answer(r['question'], r.get('context', ''), r.get('version')))
                     for r in cases]
    output.mkdir(parents=True, exist_ok=False)
    save(output/'responses.json', dict(freeze=frozen, cases_sha256=hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                                      rows=responses))
    with (output/'review.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'reviewer', 'correct', 'supported', 'critical', 'notes'])
        writer.writerows([case['id'], '', '', '', '', ''] for case in cases)


def quality(directory):
    payload = read(directory/'responses.json')
    if payload['freeze'] != read(ROOT/'evaluation/pilot_freeze.json') or fingerprint() != payload['freeze']['sha256']:
        raise ValueError('A análise exige a versão congelada que produziu as respostas.')
    rows = payload['rows']
    reviews = load_csv(directory/'review.csv')
    by_id = {r['id']: r for r in reviews}
    if len(by_id) != len(reviews) or set(by_id) != {r['case']['id'] for r in rows}:
        raise ValueError('A revisão deve conter uma linha por caso.')
    if any(not r['reviewer'].strip() or any(r[k] not in ('0', '1') for k in ('correct', 'supported', 'critical'))
           for r in reviews):
        return {'status': 'pending_review'}
    answerable = emitted = approved = resolved = correct_triage = triage = critical = 0
    for row in rows:
        case, response = row['case'], row['response']
        review = by_id[case['id']]
        correct = review['correct'] == '1'
        is_critical = review['critical'] == '1'
        approved_answer = correct and review['supported'] == '1' and not is_critical
        critical += is_critical
        answerable += case['expected_action'] == 'answer'
        triage += case['expected_action'] != 'answer'
        if response['action'] == 'answer':
            emitted += 1
            approved += approved_answer and case['expected_action'] == 'answer'
            resolved += approved_answer and case['expected_action'] == 'answer'
        elif case['expected_action'] != 'answer':
            correct_triage += correct and not is_critical and response['action'] == case['expected_action']
    precision = approved/emitted if emitted else 0
    coverage = resolved/answerable if answerable else 0
    triage_accuracy = correct_triage/triage if triage else 0
    return dict(status='recorded', cases=len(rows), answerable=answerable, triage_cases=triage,
                emitted=emitted, approved=approved, resolved=resolved, correct_triage=correct_triage,
                critical=critical, precision=precision, resolution=coverage, triage_accuracy=triage_accuracy,
                pilot_gate=(answerable >= 20 and triage >= 10 and precision >= .95 and
                            coverage >= .7 and triage_accuracy >= .9 and critical == 0))


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))


def utility(path):
    pairs = {}
    for row in load_csv(path):
        method = row['method']
        seconds = float(row['seconds'])
        if (method not in ('manual', 'assisted') or row['correct'] not in ('0', '1')
                or not math.isfinite(seconds) or seconds <= 0 or not row['participant'] or not row['task_pair']):
            raise ValueError('Medição inválida.')
        pair = pairs.setdefault((row['participant'], row['task_pair']), {})
        if method in pair:
            raise ValueError('Medição duplicada.')
        pair[method] = (seconds, int(row['correct']))
    if not pairs or any(len(pair) != 2 for pair in pairs.values()):
        return {'status': 'pending_pairs', 'pairs_recorded': len(pairs)}
    participants = {participant for participant, _ in pairs}
    ratios = [p['assisted'][0]/p['manual'][0] for p in pairs.values()]
    scores = {m: sum(p[m][1] for p in pairs.values())/len(pairs) for m in ('manual', 'assisted')}
    ratio = statistics.median(ratios)
    return dict(status='recorded', participants=len(participants), pairs=len(pairs),
                median_time_ratio=ratio, correctness=scores,
                pilot_gate=len(participants) >= 5 and len(pairs) >= 10 and ratio <= .8
                           and scores['assisted'] >= scores['manual'])


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze')
    execute = sub.add_parser('run')
    execute.add_argument('cases', type=Path)
    execute.add_argument('output', type=Path)
    analyze = sub.add_parser('analyze')
    analyze.add_argument('--run', type=Path)
    analyze.add_argument('--study', type=Path, default=ROOT/'evaluation/user_study.csv')
    args = parser.parse_args()
    if args.command == 'freeze':
        with (ROOT/'evaluation/pilot_freeze.json').open('x', encoding='utf-8') as file:
            json.dump({'sha256': fingerprint()}, file, indent=2)
    elif args.command == 'run':
        run(args.cases, args.output)
    else:
        report = dict(review=quality(args.run) if args.run else {'status': 'pending_cases'},
                      utility=utility(args.study))
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
