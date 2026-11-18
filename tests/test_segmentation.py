import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from support_rag.chunking.chunker import chunk_document,trim_tracebacks
from support_rag.utils.io import read
from support_rag.vectordb.store import Store
from support_rag.retrieval.retriever import Retriever
from support_rag.settings import ROOT
class SegmentationTests(unittest.TestCase):
 def test_parameter_stays_together(self):
  text='indicator bool, default False\n\n'+('Description of origin. '*50)+'\n\nvalidate str, optional\n\nChecks cardinality.\n\n- one_to_many: unique left\n\n- many_to_one: unique right\n\nReturns\n\nDataFrame'
  doc={'url':'official','title':'Merge','version':'2.2.3','blocks':[{'text':text,'section':'API','kind':'markdown'}]}
  chunks=chunk_document(doc,900)
  param=[c for c in chunks if 'validate str' in c['text']]
  self.assertTrue(any('one_to_many' in c['text'] and 'many_to_one' in c['text'] for c in param))
 def test_traceback_condensed(self):
  text='An explanation.\n\n```\nTraceback (most recent call last)\nFile x.py, line 10\nValueError: example\n```\nMore context.'
  clean=trim_tracebacks(text)
  self.assertNotIn('File x.py',clean);self.assertIn('ValueError: example',clean)
  self.assertIn('More context.',clean)
 def test_regular_code_retained(self):
  text='```python\nx = 1\n```'
  self.assertEqual(trim_tracebacks(text),text)
 def test_real_corpus_portuguese_query(self):
  # Teste de regressão de desenvolvimento: evidência, não qualidade do LLM.
  store=Store(ROOT/'data')
  if not (ROOT/'data/active.json').exists():self.skipTest('Snapshot não disponível')
  manifest,chunks=store.load()
  if manifest.get('metadata',{}).get('cleaner')!='v4-parameter-boundaries':self.skipTest('Corpus de outra versão')
  hit=Retriever(chunks).search('Como validar um merge muitos para um usando validate?')[0]
  self.assertIn('many_to_one',hit['text'])
  self.assertIn('right',hit['text'])
  self.assertIn('validate',hit['section'])
if __name__=='__main__':unittest.main()
