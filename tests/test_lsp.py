#!/usr/bin/env python3
"""
SYNAX Language Server Protocol (LSP) Test Suite (`tests/test_lsp.py`)
=====================================================================
Verifies JSON-RPC 2.0 communication, diagnostics, hover documentation,
and formatting requests against `SynaxLanguageServer`.
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
for p in (str(SRC_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from synax.lsp.server import SynaxLanguageServer


class MockClient:
    """In-memory bidirectional client for testing SynaxLanguageServer."""

    def __init__(self):
        self.server_in = io.BytesIO()
        self.server_out = io.BytesIO()
        self.server = SynaxLanguageServer(
            in_stream=self.server_in,
            out_stream=self.server_out,
        )

    def send_rpc(self, msg: dict) -> None:
        data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        self.server_in.write(header + data)
        self.server_in.seek(0)
        # Process one message
        m = self.server.read_message()
        if m:
            if "id" in m:
                self.server.handle_request(m)
            else:
                self.server.handle_notification(m)
        self.server_in.seek(0)
        self.server_in.truncate(0)

    def read_responses(self) -> list[dict]:
        self.server_out.seek(0)
        content = self.server_out.read()
        self.server_out.seek(0)
        self.server_out.truncate(0)

        responses = []
        pos = 0
        while pos < len(content):
            hdr_end = content.find(b"\r\n\r\n", pos)
            if hdr_end == -1:
                break
            hdr = content[pos:hdr_end].decode("ascii")
            clen = 0
            for line in hdr.splitlines():
                if line.lower().startswith("content-length:"):
                    clen = int(line.split(":", 1)[1].strip())
            body_start = hdr_end + 4
            body = content[body_start : body_start + clen]
            responses.append(json.loads(body.decode("utf-8")))
            pos = body_start + clen
        return responses


class TestSynaxLSP(unittest.TestCase):
    def test_01_initialize_and_capabilities(self) -> None:
        client = MockClient()
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"rootUri": "file:///workspace"},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        res = resps[0].get("result", {})
        caps = res.get("capabilities", {})
        self.assertTrue(caps.get("hoverProvider"))
        self.assertTrue(caps.get("documentFormattingProvider"))
        self.assertEqual(res.get("serverInfo", {}).get("name"), "synax-lsp")

    def test_02_diagnostics_on_clean_and_broken_sources(self) -> None:
        client = MockClient()
        uri = "file:///test_kernel.sx"

        # 1. Valid program: publishes empty diagnostics
        clean_sx = """synax 0.5
kernel clean(a: tensor<f32>) -> f32 {
  return sum(a)
}
"""
        client.send_rpc({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": uri, "text": clean_sx}},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        self.assertEqual(resps[0]["method"], "textDocument/publishDiagnostics")
        self.assertEqual(resps[0]["params"]["diagnostics"], [])

        # 2. Syntax Error: publishes diagnostic with range
        broken_sx = """synax 0.5
kernel broken(a: tensor<f32>) -> f32 {
  return a @ 5.0
}
"""
        client.send_rpc({
            "jsonrpc": "2.0",
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {"uri": uri},
                "contentChanges": [{"text": broken_sx}],
            },
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        diags = resps[0]["params"]["diagnostics"]
        self.assertEqual(len(diags), 1)
        self.assertEqual(diags[0]["severity"], 1)
        self.assertEqual(diags[0]["source"], "synax")
        self.assertEqual(diags[0]["range"]["start"]["line"], 2)

    def test_03_neuro_symbolic_hover_documentation(self) -> None:
        client = MockClient()
        uri = "file:///hover_test.sx"
        doc_sx = """synax 0.5
kernel test(signal: tensor<f32>) -> f32 {
  safety {
    nonfinite = heal(0.0)
  }
  let filtered = clamp(signal, -1.0, 1.0)
  return sum(filtered)
}
"""
        client.send_rpc({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": uri, "text": doc_sx}},
        })
        client.read_responses()  # Clear publishDiagnostics

        # Hover on 'sum' (line 6, character 9)
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 10,
            "method": "textDocument/hover",
            "params": {"textDocument": {"uri": uri}, "position": {"line": 6, "character": 9}},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        val = resps[0]["result"]["contents"]["value"]
        self.assertIn("Dendritik İndirgeme", val)
        self.assertIn("Neumaier", val)

        # Hover on 'clamp' (line 5, character 18)
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 11,
            "method": "textDocument/hover",
            "params": {"textDocument": {"uri": uri}, "position": {"line": 5, "character": 18}},
        })
        resps = client.read_responses()
        self.assertIn("Akson Tepesi", resps[0]["result"]["contents"]["value"])

        # Hover on 'safety' (line 2, character 3)
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 12,
            "method": "textDocument/hover",
            "params": {"textDocument": {"uri": uri}, "position": {"line": 2, "character": 3}},
        })
        resps = client.read_responses()
        self.assertIn("Ranvier Düğümü", resps[0]["result"]["contents"]["value"])

    def test_04_document_formatting(self) -> None:
        client = MockClient()
        uri = "file:///fmt_test.sx"
        unformatted = 'synax 0.5\nkernel test(a:tensor<f32>)->f32{\nreturn sum(a)\n}\n'
        client.send_rpc({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": uri, "text": unformatted}},
        })
        client.read_responses()

        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 20,
            "method": "textDocument/formatting",
            "params": {"textDocument": {"uri": uri}},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        edits = resps[0]["result"]
        self.assertEqual(len(edits), 1)
        new_text = edits[0]["newText"]
        self.assertIn("kernel test(", new_text)
        self.assertIn("  a: tensor<f32>", new_text)
        self.assertIn("  return sum(a)", new_text)

    def test_05_code_lens_and_completion(self) -> None:
        client = MockClient()
        uri = "file:///evolution_test.sx"
        code = 'intent "calculate cerebral perfusion pressure MAP minus ICP"\nkernel cpp(map: tensor<f32>, icp: tensor<f32>) -> f32 {\n  return mean(map) - mean(icp)\n}\n'
        client.send_rpc({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": uri, "text": code}},
        })
        client.read_responses()

        # CodeLens
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 30,
            "method": "textDocument/codeLens",
            "params": {"textDocument": {"uri": uri}},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        lenses = resps[0]["result"]
        self.assertGreaterEqual(len(lenses), 2)
        titles = [lens["command"]["title"] for lens in lenses]
        self.assertTrue(any("Niyetten Otonom Sentezle" in t for t in titles))
        self.assertTrue(any("SYNAX" in t for t in titles))

        # Completion
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 31,
            "method": "textDocument/completion",
            "params": {"textDocument": {"uri": uri}, "position": {"line": 1, "character": 0}},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        items = resps[0]["result"]["items"]
        labels = [item["label"] for item in items]
        self.assertIn("intent", labels)
        self.assertIn("kernel", labels)
        self.assertIn("safety", labels)
        self.assertIn("clamp", labels)

    def test_06_neuro_symbolic_synthesis(self) -> None:
        client = MockClient()
        client.send_rpc({
            "jsonrpc": "2.0",
            "id": 40,
            "method": "synax/synthesize",
            "params": {"intent": "kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al"},
        })
        resps = client.read_responses()
        self.assertEqual(len(resps), 1)
        res = resps[0]["result"]
        self.assertEqual(res["status"], "success")
        self.assertIn("best_code", res)
        self.assertIn("relu", res["best_code"])



if __name__ == "__main__":
    unittest.main()
