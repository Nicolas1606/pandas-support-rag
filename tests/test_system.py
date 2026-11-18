import copy, json, sys, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from support_rag.settings import settings, ROOT
from support_rag.utils.io import read, save
from support_rag.ingestion.loader import parse_html, fetch
from support_rag.chunking.chunker import chunk_document, split_text
from support_rag.vectordb.store import Store
from support_rag.retrieval.retriever import BM25, Retriever, cosine, rrf
from support_rag.llm.contracts import validate
from support_rag.llm.client import Ollama
from support_rag.pipeline import Pipeline
from support_rag.evaluation.metrics import retrieval_metrics, wilson, percentile
from support_rag.evaluation.runner import run
from support_rag.api.server import make_server

class FakeLLM:

    def __init__(self, mode='valid'):
        self.mode = mode

    def generate(self, system, payload, schema):
        if self.mode == 'timeout':
            raise TimeoutError()
        source = payload['evidence'][0]['id']
        if 'supported' in schema.get('required', []):
            return ({'supported': True, 'answers_question': True, 'portuguese': True, 'reason': 'Simulado'}, {})
        return ({'action': 'answer', 'message': '', 'claims': [{'text': 'Resposta de teste.', 'evidence_ids': ['fake' if self.mode == 'invalid' else source], 'evidence_quotes': [{'source_id': source, 'quote': payload['evidence'][0]['text']}]}]}, {})

class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.c = settings()
        self.c['data_dir'] = self.tmp.name
        self.c['default_method'] = 'bm25'
        self.c['use_planner'] = False
        self.c['answer_mode'] = 'experimental_llm'
        self.store = Store(self.tmp.name)
        docs = read(ROOT / 'tests/fixtures/documents.json')
        self.chunks = [x for d in docs for x in chunk_document(d)]
        self.cid = self.store.create(self.chunks, [], {'kind': 'fixture'})
        self.store.activate(self.cid, 'test')

    def tearDown(self):
        self.tmp.cleanup()

class ParseTests(unittest.TestCase):

    def test_preserve_code(self):
        title, b = parse_html('<main><h1>Title</h1><section id="a"><h2>Warning</h2><p>Null keys match.</p><pre>x = 1\ny = 2</pre></section></main>')
        self.assertEqual(title, 'Title')
        self.assertIn('x = 1\ny = 2', b[-1]['text'])

    def test_remove_script(self):
        _, b = parse_html('<main><h1>X</h1><script>bad</script><p>good</p></main>')
        self.assertEqual(b[0]['text'], 'good')

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            parse_html('<nav>only navigation</nav>')

    def test_path_escape(self):
        with self.assertRaises(ValueError):
            fetch('../outside')

    def test_table(self):
        _, b = parse_html('<main><table><tr><td>a</td><td>b</td></tr></table></main>')
        self.assertIn('a | b', b[0]['text'])

    def test_chunk_bound(self):
        pieces = list(split_text('word ' * 1000, 900))
        self.assertTrue(all((len(x) <= 900 for x in pieces)))
        self.assertGreater(len(pieces), 1)

class StoreTests(Base):

    def test_idempotent(self):
        self.assertEqual(self.cid, self.store.create(self.chunks, []))

    def test_integrity(self):
        path = self.store.path(self.cid) / 'chunks.json'
        x = read(path)
        x[0]['text'] = 'corrupted'
        save(path, x)
        with self.assertRaises(ValueError):
            self.store.load()

    def test_path_traversal(self):
        with self.assertRaises(ValueError):
            self.store.path('../foo')

    def test_failed_promotion_keeps_active(self):
        with self.assertRaises(FileNotFoundError):
            self.store.activate('0' * 16, 'test')
        self.assertEqual(read(Path(self.tmp.name) / 'active.json')['corpus_id'], self.cid)

    def test_rollback(self):
        changed = copy.deepcopy(self.chunks)
        changed[0]['text'] = 'modified'
        cid2 = self.store.create(changed, [])
        self.store.activate(cid2, 'candidate')
        self.store.activate(self.cid, 'rollback')
        self.assertEqual(self.store.load()[0]['corpus_id'], self.cid)

class RetrievalTests(Base):

    def test_bm25(self):
        self.assertIn('merge', Retriever(self.chunks).search('merge validate')[0]['document_url'])

    def test_unknown_terms(self):
        self.assertEqual(max(BM25(self.chunks).scores('zzzzz')), 0)

    def test_dense_requires_index(self):
        with self.assertRaises(RuntimeError):
            Retriever(self.chunks).search('hello', 'dense')

    def test_cosine(self):
        self.assertAlmostEqual(cosine([1, 0], [1, 0]), 1)

    def test_cosine_zero(self):
        self.assertEqual(cosine([0, 0], [1, 0]), 0)

    def test_dimensions(self):
        with self.assertRaises(ValueError):
            cosine([1], [1, 2])

    def test_rrf(self):
        self.assertGreater(rrf([[0, 1], [0, 1]], 2)[0], rrf([[0, 1], [0, 1]], 2)[1])

class ContractTests(unittest.TestCase):

    def test_fake_citation(self):
        with self.assertRaises(ValueError):
            validate({'action': 'answer', 'message': '', 'claims': [{'text': 'x', 'evidence_ids': ['fake']}]}, [{'id': 'real'}])

    def test_answer_needs_claims(self):
        with self.assertRaises(ValueError):
            validate({'action': 'answer', 'message': '', 'claims': []}, [])

    def test_clarify_valid(self):
        self.assertEqual(validate({'action': 'clarify', 'message': 'Qual tipo?', 'claims': []}, [])['action'], 'clarify')

    def test_extra_fields(self):
        with self.assertRaises(ValueError):
            validate({'action': 'handoff', 'message': 'x', 'claims': [], 'secret': 'x'}, [])

    def test_remote_llm_rejected(self):
        with self.assertRaises(ValueError):
            Ollama('https://example.com', 'model')

class PipelineTests(Base):

    def test_valid_generation(self):
        output = Pipeline(self.c, FakeLLM()).answer('merge validate')
        self.assertEqual(output['action'], 'answer')
        self.assertTrue((Path(self.tmp.name) / 'logs' / (output['request_id'] + '.json')).exists())

    def test_invalid_citation_error(self):
        self.assertEqual(Pipeline(self.c, FakeLLM('invalid')).answer('merge')['action'], 'handoff')

    def test_timeout_error(self):
        self.assertEqual(Pipeline(self.c, FakeLLM('timeout')).answer('merge')['error_type'], 'TimeoutError')

    def test_version_handoff(self):
        self.assertEqual(Pipeline(self.c, FakeLLM()).answer('merge', version='1.0')['action'], 'handoff')

    def test_zero_evidence(self):
        self.assertEqual(Pipeline(self.c, FakeLLM()).answer('zzzzzz')['action'], 'handoff')

    def test_long_question(self):
        with self.assertRaises(ValueError):
            Pipeline(self.c, FakeLLM()).answer('x' * 3001)

    def test_busy(self):
        p = Pipeline(self.c, FakeLLM())
        p.lock.acquire()
        try:
            self.assertEqual(p.answer('merge')['error_type'], 'busy')
        finally:
            p.lock.release()

class EvaluationTests(Base):

    def test_family_disjoint(self):
        cases = read(ROOT / 'evaluation/cases.json')
        a = {c['family'] for c in cases if c['split'] == 'development'}
        b = {c['family'] for c in cases if c['split'] == 'test'}
        self.assertFalse(a & b)
        self.assertEqual(len(cases), 120)

    def test_unreviewed_blocked(self):
        cases=read(ROOT/'evaluation/cases.json')
        for case in cases:case['review_status']='draft'
        draft=Path(self.tmp.name)/'draft.json'
        save(draft,cases)
        with self.assertRaises(ValueError):
            run(self.c, draft, 'test', 'bm25')

    def test_metrics(self):
        evidence = [[{'url_suffix': 'pandas.merge.html', 'terms': ['validate']}]]
        m = retrieval_metrics(self.chunks, evidence)
        self.assertEqual(m['evidence_recall'], 1)

    def test_missing_evidence(self):
        m = retrieval_metrics(self.chunks, [[{'url_suffix': 'missing', 'terms': []}]])
        self.assertFalse(m['hit_at_k'])

    def test_wilson(self):
        low, high = wilson(10, 10)
        self.assertLess(low, 1)
        self.assertAlmostEqual(high, 1)

    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3], 0.5), 2)

class APITests(Base):

    def setUp(self):
        super().setUp()
        self.server = make_server(self.c, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])
        try:
            with urlopen(self.url + '/health', timeout=2):
                pass
        except URLError as e:
            if isinstance(e.reason, PermissionError):
                self.server.shutdown()
                self.server.server_close()
                self.thread.join()
                self.tmp.cleanup()
                self.skipTest('Sandbox bloqueia conexão TCP local (WinError 10013)')
            raise

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        super().tearDown()

    def test_health(self):
        with urlopen(self.url + '/health') as r:
            self.assertEqual(json.load(r)['status'], 'alive')

    def test_search(self):
        req = Request(self.url + '/search', data=json.dumps({'question': 'merge validate'}).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(req) as r:
            self.assertTrue(json.load(r)['sources'])

    def test_invalid_input(self):
        req = Request(self.url + '/search', data=b'{}', headers={'Content-Type': 'application/json'})
        with self.assertRaises(HTTPError) as caught:
            urlopen(req)
        self.assertEqual(caught.exception.code, 422)
        caught.exception.close()

    def test_ui(self):
        with urlopen(self.url) as r:
            self.assertIn('Suporte pandas', r.read().decode())
if __name__ == '__main__':
    unittest.main()
