"""Causal model, training artifact and local API behavior tests (`tests/test_synaxllm.py`)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from synax.llm.tokenizer import decode
from synax.assistant.server import parse_completion, RequestError


class TestSynaxLLMAndServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.trained_output = None
        cls.trained_report = None
        if HAS_TORCH:
            from synax.llm.model import ModelSpec
            from synax.llm.training import TrainingRun, train

            base = Path(cls.tmp_dir.name)
            data = base / "train.jsonl"
            val = base / "validation.jsonl"
            data.write_text(
                json.dumps({"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]}) + "\n",
                encoding="utf-8",
            )
            val.write_text(
                json.dumps({"messages": [{"role": "user", "content": "Hey"}, {"role": "assistant", "content": "Hello!"}]}) + "\n",
                encoding="utf-8",
            )
            output = base / "checkpoint"
            cls.trained_report = train(
                TrainingRun(data, val, output, steps=15),
                ModelSpec(context=64, width=32, heads=2, layers=1),
            )
            cls.trained_output = output

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_dir.cleanup()

    def test_01_utf8_tokenizer_round_trip(self) -> None:
        text = "Türkçe bilim 🧠 <assistant>"
        result = decode(list(text.encode("utf-8")))
        self.assertEqual(result, text)

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_02_causal_attention_cannot_read_future_tokens(self) -> None:
        from synax.llm.model import ModelSpec, SynaxTransformer

        torch.manual_seed(1)
        model = SynaxTransformer(ModelSpec(context=32, width=32, heads=2, layers=1)).eval()
        with torch.no_grad():
            first = model(torch.tensor([[1, 2, 3, 4]]))
            second = model(torch.tensor([[1, 2, 99, 98]]))
        torch.testing.assert_close(first[:, :2], second[:, :2])

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_03_training_masks_user_tokens(self) -> None:
        from synax.llm.data import tensorize

        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Yes"},
        ]
        _, targets = tensorize([messages], 32)
        self.assertEqual(targets[targets != -100].tolist(), [89, 101, 115, 259])

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_04_training_learns_and_round_trips_owned_weights(self) -> None:
        from synax.llm.runtime import LocalModel

        assert self.trained_output is not None and self.trained_report is not None
        model = LocalModel(self.trained_output)
        self.assertLess(self.trained_report["final_train_loss"], self.trained_report["initial_train_loss"])
        self.assertGreater(self.trained_report["parameters"], 0)
        self.assertEqual(len(self.trained_report["weights_sha256"]), 64)
        self.assertTrue(model.generate([{"role": "user", "content": "Hi"}], 8))
        self.assertEqual(model.stage, "experimental-bootstrap")

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_05_training_rejects_validation_leakage(self) -> None:
        from synax.llm.model import ModelSpec
        from synax.llm.training import TrainingRun, train

        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            data = tmp_path / "same.jsonl"
            data.write_text(
                json.dumps({"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                train(TrainingRun(data, data, tmp_path / "output", steps=1), ModelSpec())
            self.assertFalse((tmp_path / "output").exists())

    def test_06_api_rejects_invalid_requests(self) -> None:
        invalid_bodies = [
            b"[]",
            b'{"messages":[]}',
            b'{"messages":[{"role":"tool","content":"x"}]}',
            b'{"messages":[{"role":[],"content":"x"}]}',
            b'{"messages":[{"role":"user","content":"hi"}],"stream":true}',
            b'{"messages":[{"role":"user","content":"hi"}],"max_tokens":true}',
        ]
        for body in invalid_bodies:
            with self.assertRaises(RequestError):
                parse_completion(body)

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_07_inbound_api_serves_own_model_with_auth(self) -> None:
        from synax.llm.runtime import LocalModel
        from synax.assistant.server import create_server

        assert self.trained_output is not None
        old_tok = os.environ.get("SYNAX_API_TOKEN")
        os.environ["SYNAX_API_TOKEN"] = "local-test-token"
        server = create_server(LocalModel(self.trained_output), 0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            request = Request(
                base + "/v1/chat/completions",
                method="POST",
                headers={"Authorization": "Bearer local-test-token", "Content-Type": "application/json"},
                data=json.dumps({"model": "SynaxLLM", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 8}).encode(),
            )
            with urlopen(request, timeout=10) as response:
                payload = json.load(response)
            self.assertTrue(payload["choices"][0]["message"]["content"])
            self.assertEqual(payload["synax"]["stage"], "experimental-bootstrap")
            with self.assertRaises(HTTPError) as ctx:
                urlopen(base + "/v1/models", timeout=5)
            self.assertEqual(ctx.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()
            if old_tok is None:
                os.environ.pop("SYNAX_API_TOKEN", None)
            else:
                os.environ["SYNAX_API_TOKEN"] = old_tok

    def test_08_harness_routes_check_to_real_synax_parser(self) -> None:
        from synax_chat import SynaxChatAgent

        source = (ROOT / "examples/llm_residual.sx").read_text(encoding="utf-8")
        result = SynaxChatAgent().process_message("/check " + source)
        self.assertEqual(result.action, "source_checked")
        self.assertEqual(result.metadata, {"type_checked": True, "verified": False})

    @unittest.skipUnless(HAS_TORCH, "PyTorch is not installed in this interpreter")
    def test_09_checkpoint_tampering_is_rejected(self) -> None:
        from synax.llm.runtime import LocalModel, ModelUnavailable

        assert self.trained_output is not None
        with tempfile.TemporaryDirectory() as td:
            checkpoint = Path(td) / "modified"
            shutil.copytree(self.trained_output, checkpoint)
            with (checkpoint / "weights.pt").open("ab") as stream:
                stream.write(b"corruption")
            with self.assertRaises(ModelUnavailable):
                LocalModel(checkpoint)

    def test_10_model_import_does_not_eagerly_load_compiler(self) -> None:
        script = "import sys, synax; assert 'synaxc' not in sys.modules; assert 'torch' not in sys.modules; assert 'check' in dir(synax)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
