"""SynaxAI harness resilience, reset, and offline evolution tests."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from synax_chat import SynaxChatAgent


class TestSynaxAssistantHarness(unittest.TestCase):
    def test_missing_weights_gracefully_routes_without_crash(self) -> None:
        os.environ.pop("SYNAX_MODEL_PATH", None)
        result = SynaxChatAgent().process_message("Merhaba, nasılsın?")
        self.assertIn(result.action, ("llm_response", "general_chat"))
        self.assertNotIn("ağırlıkları seçilmedi", result.text)

    def test_reset_clears_session(self) -> None:
        agent = SynaxChatAgent()
        if agent.conversation:
            agent.conversation.history = [{"role": "user", "content": "private"}]
        result = agent.process_message("/reset")
        self.assertEqual(result.action, "conversation_reset")
        if agent.conversation:
            self.assertEqual(agent.conversation.history, [])

    def test_json_rpc_editor_transport_without_weights(self) -> None:
        env = os.environ.copy()
        env.pop("SYNAX_MODEL_PATH", None)
        payload = json.dumps({"id": 7, "method": "chat", "params": {"message": "Merhaba"}})
        result = subprocess.run(
            [sys.executable, "synax_chat.py", "--json-rpc"],
            input=payload + "\n",
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
            timeout=15,
            check=True,
        )
        reply = json.loads(result.stdout)
        self.assertEqual(reply["id"], 7)
        self.assertIn("Merhaba", reply["result"]["text"])

    def test_evolution_never_implicitly_calls_provider(self) -> None:
        from synax.evolution.synthesizer import NeuroSymbolicSynthesizer

        synthesizer = NeuroSymbolicSynthesizer()
        candidates = synthesizer.synthesize_variants("difference", "difference", ["a", "b"])
        self.assertEqual(len(candidates), 4)


if __name__ == "__main__":
    unittest.main()
