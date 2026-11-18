import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from support_rag.evaluation.review import summarize
p = argparse.ArgumentParser()
p.add_argument('results')
p.add_argument('review')
a = p.parse_args()
print(json.dumps(summarize(a.results, a.review), ensure_ascii=False, indent=2))
