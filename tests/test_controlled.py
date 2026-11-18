import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from support_rag.controlled import ControlledAnswers
from support_rag.utils.io import sha


class ControlledTests(unittest.TestCase):
    def test_binding_rejects_changed_passage_even_if_id_matches(self):
        source = dict(id='id', text='New text has a different meaning.')
        contract = dict(id='demo', patterns=['demo'], answer='Texto de teste.',
                        evidence=[dict(id='id', sha256=sha('The original definition.'))])
        result = ControlledAnswers([contract], [source], '2.2.3').answer('demo', '', '')
        self.assertEqual(result['action'], 'handoff')
        self.assertEqual(result['decision_reason'], 'missing_evidence')
        self.assertEqual(result['claims'], [])
