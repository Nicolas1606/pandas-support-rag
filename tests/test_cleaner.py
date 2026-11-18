import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from support_rag.ingestion.cleaner import inline,clean_document
from support_rag.retrieval.retriever import tokenize,Retriever
from support_rag.chunking.chunker import chunk_document
class CleanerTests(unittest.TestCase):
 def test_underscore(self):
  self.assertEqual(inline(r'many\_to\_one'),'many_to_one')
 def test_link_label(self):
  self.assertEqual(inline('[merge](https://example.test/merge.html)'),'merge')
 def test_header(self):
  self.assertEqual(inline('pandas.merge [\\#](https://example.test/#merge "Link to this heading")'),'pandas.merge')
 def test_preamble_removed(self):
  d={'url':'x','title':'Title','version':'2.2.3','blocks':[{'section':'api.html','text':'Back to top','kind':'markdown'},{'section':'Params','text':'validate many_to_one checks right keys','kind':'markdown'}]}
  cleaned=clean_document(d)
  self.assertEqual(len(cleaned['blocks']),1)
  self.assertIn('many_to_one',cleaned['blocks'][0]['text'])
 def test_source_action_removed(self):
  d={'url':'x','title':'Title','version':'2.2.3','blocks':[{'section':'Params','text':'[Show Source](https://example.test/src)\n\nvalidate controls cardinality','kind':'markdown'}]}
  self.assertNotIn('Show Source',clean_document(d)['blocks'][0]['text'])
 def test_no_destructive_original_mutation(self):
  d={'url':'x','title':'[merge](https://example.test)','blocks':[]}
  clean_document(d)
  self.assertEqual(d['title'],'[merge](https://example.test)')
if __name__=='__main__':unittest.main()
