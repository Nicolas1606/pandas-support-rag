"""Verificações de integridade da distribuição; não certifica qualidade do modelo."""
import json, gzip, hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
required = [
 'README.md','LICENSE','THIRD_PARTY_NOTICES.md','config.json',
 'assets/corpus.json.gz','assets/vectors.json.gz','assets/raw_markdown.json.gz',
 'evaluation/cases.json','reports/RESULTADOS.md','reports/semantic_review.csv',
 'reports/semantic_summary.json','reports/test_all.txt','reports/clean_installation.json',
 'reports/release_evaluation/test/results.json','notebooks/01_crisp_dm.ipynb',
]
missing = [name for name in required if not (ROOT/name).is_file()]
checks = {'missing_files':missing}
if not missing:
 for name in ['corpus','vectors','raw_markdown']:
  with gzip.open(ROOT/'assets'/f'{name}.json.gz','rt',encoding='utf-8') as f: json.load(f)
 cases=json.loads((ROOT/'evaluation/cases.json').read_text(encoding='utf-8'))
 groups={s:{c['family'] for c in cases if c['split']==s} for s in ['development','test']}
 checks['families_disjoint']=not bool(groups['development'] & groups['test'])
 checks['case_count']=len(cases)
 results=json.loads((ROOT/'reports/release_evaluation/test/results.json').read_text(encoding='utf-8'))
 checks['test_cases_executed']=results['n']
 checks['clean_installation_passed']=json.loads((ROOT/'reports/clean_installation.json').read_text(encoding='utf-8'))['passed']
 log=(ROOT/'reports/test_all.txt').read_text(encoding='utf-8')
 checks['unit_and_integration_passed']='Ran 73 tests' in log and log.strip().endswith('OK')
 checks['package_complete']=checks['families_disjoint'] and results['n']==60 and checks['clean_installation_passed'] and checks['unit_and_integration_passed']
else: checks['package_complete']=False
checks['autonomous_production_approved']=False
checks['reason']='Release local para portfólio e revisão pelo atendente; falhas factuais e ausência de validação humana externa estão documentadas.'
print(json.dumps(checks,ensure_ascii=False,indent=2))
sys.exit(0 if checks['package_complete'] else 1)
