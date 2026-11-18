"""Agrega revisão registrada sem transformar campos ausentes em acertos."""
import csv
from collections import Counter
from support_rag.utils.io import read
from support_rag.evaluation.metrics import wilson

def summarize(results_path, review_path):
    results = read(results_path)
    with open(review_path, encoding='utf-8', newline='') as f:
        reviews = list(csv.DictReader(f))
    by_id = {r['case_id']: r for r in reviews}
    if len(by_id) != len(reviews):
        raise ValueError('Revisões duplicadas')
    rows = results['rows']
    known = {r['case_id'] for r in rows}
    if not set(by_id) <= known:
        raise ValueError('Revisão contém caso desconhecido')
    approved = reviewed = emitted = correct_resolved = 0
    categories = Counter()
    confusion = Counter()
    supported = total_citations = cited = required = 0
    for row in rows:
        output = row.get('output', {})
        action = output.get('action', 'not_generated')
        confusion[row['expected_action'], action] += 1
        if action == 'answer':
            emitted += 1
        r = by_id.get(row['case_id'], {})
        fields = ['correctness_0_2', 'grounding_0_2', 'critical_error_0_1']
        if not all((str(r.get(k, '')).strip() for k in fields)):
            continue
        correctness, grounding, critical = [int(r[k]) for k in fields]
        if correctness not in (0, 1, 2) or grounding not in (0, 1, 2) or critical not in (0, 1):
            raise ValueError('Nota inválida')
        if action == 'answer':
            reviewed += 1
            ok = correctness == 2 and grounding == 2 and (critical == 0)
            approved += ok
            if row['expected_action'] == 'answer':
                correct_resolved += ok
        if r.get('error_category'):
            categories[r['error_category']] += 1
        for numerator, denominator in [('citations_supported', 'citations_total'), ('claims_cited', 'claims_requiring_citation')]:
            if r.get(numerator, '').strip() and r.get(denominator, '').strip():
                a, b = (int(r[numerator]), int(r[denominator]))
                if not 0 <= a <= b:
                    raise ValueError('Contagem inválida')
                if numerator == 'citations_supported':
                    supported += a
                    total_citations += b
                else:
                    cited += a
                    required += b
    answerable = sum((r['expected_action'] == 'answer' for r in rows))
    return {'emitted_answers': emitted, 'reviewed_answers': reviewed, 'approved_answers': approved, 'approved_fraction_reviewed': approved / reviewed if reviewed else None, 'wilson_95': wilson(approved, reviewed), 'correct_resolution_lower_bound': correct_resolved / answerable if answerable else None, 'review_incomplete': reviewed < emitted, 'citation_precision': supported / total_citations if total_citations else None, 'citation_coverage': cited / required if required else None, 'error_categories': dict(categories), 'action_confusion': [{'expected': a, 'observed': b, 'count': n} for (a, b), n in confusion.items()], 'warning': 'Wilson descritivo: paráfrases da mesma família são dependentes; não interpretar como cobertura garantida.'}
