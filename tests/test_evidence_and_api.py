import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from support_rag.pipeline import select_context
from support_rag.llm.contracts import validate,validate_audit
class EvidenceTests(unittest.TestCase):
    def source(self,id='a',text='Parameter foo is supported only when the right key is unique.'):
        return {'id':id,'text':text,'title':'pandas.function','section':'API','document_url':'/reference/api/function.html'}
    def answer(self,quote):
        return {'action':'answer','message':'','claims':[{'text':'Uma orientação verificável.',
                'evidence_ids':['a'],'evidence_quotes':[{'source_id':'a','quote':quote}]}]}
    def test_existing_id_but_fabricated_quote_rejected(self):
        with self.assertRaises(ValueError):
            validate(self.answer('This sentence is completely invented.'),[self.source()])
    def test_typographic_quotes_equivalent(self):
        source=self.source(text='The option “example” requires a unique right key.')
        self.assertEqual(validate(self.answer('The option "example" requires a unique right key.'),[source])['action'],'answer')
    def test_negation_not_removed(self):
        with self.assertRaises(ValueError):
            validate(self.answer('Parameter foo is NOT supported only when the right key is unique.'),[self.source()])
    def test_no_claim_without_quote(self):
        value=self.answer('Parameter foo is supported only when the right key is unique.')
        value['claims'][0]['evidence_quotes']=[]
        with self.assertRaises(ValueError):validate(value,[self.source()])
    def test_context_deduplicates(self):
        sources=[self.source(),self.source('b')]
        self.assertEqual(len(select_context(sources)),1)
    def test_context_budget(self):
        self.assertEqual(select_context([self.source()],budget=5),[])
    def test_named_api_parameter_priority(self):
        a=self.source();a['section']='API — option str';a['title']='pandas.function'
        b=self.source('b',text='A guide example.');b['document_url']='/user_guide/example.html'
        self.assertEqual(select_context([b,a],question='How does option work in function?')[0]['id'],'a')
    def test_audit_rejects_string_boolean(self):
        with self.assertRaises(ValueError):
            validate_audit({'supported':'true','answers_question':True,'portuguese':True,'reason':'x'})
class OptionalFastAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
            from support_rag.api.routes import app
        except ImportError:raise unittest.SkipTest('Instale requirements-api.lock.txt para validar o adaptador FastAPI.')
        cls.client=TestClient(app)
    def test_health(self):self.assertEqual(self.client.get('/health').status_code,200)
    def test_bad_input(self):self.assertEqual(self.client.post('/answer',json={}).status_code,422)
    def test_home(self):self.assertIn('Suporte pandas',self.client.get('/').text)
    def test_unknown_feedback(self):self.assertEqual(self.client.post('/feedback',json={'request_id':'a'*32,'rating':'useful'}).status_code,422)
if __name__=='__main__':unittest.main()
