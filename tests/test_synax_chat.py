#!/usr/bin/env python3
"""
SYNAX Code AI Chat & Autopoiesis Engine Tests (`tests/test_synax_chat.py`)
========================================================================
Verifies conversational understanding, autopoietic skill teaching,
algebraic simplification of acquired skills, and JSON-RPC dispatch.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from synax_chat import SynaxChatAgent


class TestSynaxChatAndAutopoiesis(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = SynaxChatAgent()

    def test_01_autopoietic_skill_acquisition(self) -> None:
        """User can teach new skills to Synax, and Synax seals them into brain memory."""
        res = self.agent.teach_skill("test_serebral_indeks", "relu(a - b) * 0.85 + bias")
        self.assertEqual(res["concept"], "test_serebral_indeks")
        self.assertIn("relu", res["human_formula"].lower())
        self.assertIn("a", res["c_scalar"])
        self.assertGreaterEqual(res["generation"], 1)

        # Verify brain has it
        self.assertIn("test_serebral_indeks", self.agent.model.brain["learned_concepts"])

    def test_02_natural_language_chat_intents(self) -> None:
        """Agent correctly classifies conversational prompts and produces code or status."""
        # 1. Autopoiesis via conversational chat
        resp1 = self.agent.process_message("kendine şu beceriyi edin: my_perfusion = (a + b) * bias")
        self.assertEqual(resp1.action, "skill_learned")
        self.assertIn("AUTOPOIESIS", resp1.text)

        # 2. Status inspection
        resp2 = self.agent.process_message("durum")
        self.assertEqual(resp2.action, "status")
        self.assertIn("Active", resp2.text)
        self.assertIn("Experimental", resp2.text)
        self.assertIn("Planned", resp2.text)

        # 3. Memory inspection
        resp3 = self.agent.process_message("hafızanı göster")
        self.assertEqual(resp3.action, "list_skills")
        self.assertIn("Sinaptik Bellek", resp3.text)

        # 4. Kernel generation
        resp4 = self.agent.process_message("kan basıncı farkı için kernel üret")
        self.assertEqual(resp4.action, "code_generated")
        self.assertIsNotNone(resp4.code)
        self.assertIn("kernel auto_generated_kernel", resp4.code)

    def test_03_hemodynamic_medical_reasoning(self) -> None:
        """Agent recognizes hemodynamic clinical prompts and provides physiological analysis."""
        resp = self.agent.process_message("kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al")
        self.assertIn("Fizyolojik Yorum", resp.text)
        self.assertIn("ReLU", resp.text)

    def test_04_conversational_greetings_and_activity(self) -> None:
        """Agent recognizes natural language conversational queries and responds coherently."""
        resp1 = self.agent.process_message("synax artık çalışıyor musun")
        self.assertEqual(resp1.action, "llm_response")
        self.assertIn("Evet", resp1.text)
        self.assertIn("Active", resp1.text)
        self.assertNotIn("ipotizle", resp1.text)  # No gibberish!

        resp2 = self.agent.process_message("merhaba")
        self.assertEqual(resp2.action, "llm_response")
        self.assertIn("Merhaba", resp2.text)

    def test_05_ecc_skills_and_search(self) -> None:
        """Agent searches and lists ECC engineering skills."""
        resp = self.agent.process_message("ecc ara: tdd")
        self.assertEqual(resp.action, "ecc_search")
        self.assertIn("ECC Becerisi Arama Sonuçları", resp.text)

    def test_06_conversation_fallback_without_weights(self) -> None:
        """Conversation harness gracefully falls back to HybridLLMRouter without fatal ModelError."""
        from synax.assistant.conversation import Conversation
        conv = Conversation()
        answer, action = conv.reply("synax artık çalışıyor musun")
        self.assertEqual(action, "general_chat")
        self.assertIn("Evet", answer)
        self.assertNotIn("ağırlıkları seçilmedi", answer)

    def test_07_live_7_stage_pipeline(self) -> None:
        """Agent executes the live 7-stage silicon pipeline from natural language intent to hardware winner."""
        resp = self.agent.process_message("/pipeline kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al")
        self.assertEqual(resp.action, "pipeline_executed")
        self.assertIn("Intent", resp.text)
        self.assertIn("Canonical SYNAX", resp.text)
        self.assertIn("Symbolic AST", resp.text)
        self.assertIn("Reference & IMMUNE", resp.text)
        self.assertIn("Semantic Lock", resp.text)
        self.assertIn("Silicon Winner", resp.text)
        self.assertIn("SHA-256", resp.text)


if __name__ == "__main__":
    unittest.main()
