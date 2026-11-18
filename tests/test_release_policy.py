import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from support_rag.policy import clarification_needed
from support_rag.llm.contracts import adapt_draft, attach_quotes, validate

class ReleasePolicyTests(unittest.TestCase):
    def test_symptom_without_example_requires_context(self):
        self.assertIsNotNone(clarification_needed('Meu merge duplicou linhas. Como resolver?'))

    def test_specific_question_is_not_forced_to_clarify(self):
        self.assertIsNone(clarification_needed('Como validar um merge muitos para um usando validate?'))

    def test_supplied_context_is_considered(self):
        self.assertIsNone(clarification_needed('Meu merge duplicou linhas.', 'Entrada e resultado esperado: ' + 'x' * 40))

    def test_quote_is_attached_from_source(self):
        sources = [{'id': 'a', 'text': 'An exact passage from the versioned documentation.'}]
        answer = attach_quotes(adapt_draft({'answer': 'Uma resposta verificável.', 'source_ids': ['a']}), sources)
        self.assertEqual(answer['claims'][0]['evidence_quotes'][0]['quote'], sources[0]['text'])
        self.assertEqual(validate(answer, sources)['action'], 'answer')

    def test_unknown_id_rejected_before_publication(self):
        with self.assertRaises(ValueError):
            attach_quotes(adapt_draft({'answer': 'Uma resposta.', 'source_ids': ['invented']}), [])

    def test_empty_draft_is_handoff(self):
        self.assertEqual(adapt_draft({'answer': '', 'source_ids': []})['action'], 'handoff')

if __name__ == '__main__':
    unittest.main()
