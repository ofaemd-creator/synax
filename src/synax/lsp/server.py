#!/usr/bin/env python3
"""
SYNAX Language Server Protocol (LSP) Server (`src/synax/lsp/server.py`)
========================================================================
Implements a standard JSON-RPC 2.0 (LSP 3.17) stdio server for `.sx` files:
  - `textDocument/publishDiagnostics`: Real-time Lexer, Parser, and TypeChecker
    diagnostics with exact caret-level 0-based range mapping.
  - `textDocument/hover`: Neuro-symbolic and neuroanatomical documentation:
      * Dendrites: `sum`, `mean`, `l2_norm`, `dot` spatial & temporal summation.
      * Soma: Canonical IR, types (`tensor<f32, N>`), `kernel`, `let` bindings.
      * Axon Hillock: Threshold activations (`clamp`, `relu`, `sigmoid`).
      * Nodes of Ranvier: `safety { nonfinite = heal | reject }` Immune Shield.
      * Myelin Sheath: SIMD superoptimizer targets (`neon`, `avx2`, `llvm`).
  - `textDocument/formatting`: Canonical idempotent source formatter (`format_sx`).
  - Standard lifecycle: `initialize`, `initialized`, `shutdown`, `exit`.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from synax.formatter import format_sx
from synax.lexer import SynaxLexError
from synax.parser import SynaxParseError, parse_module
from synax.type_system import SynaxTypeError

logger = logging.getLogger("synax_lsp")


NEURO_HOVER_DOCS = {
    "sum": """### 🌲 Dendritik İndirgeme (`sum`)
**Rol:** Dendritik Uzaysal & Zamansal Toplama (Spatial Summation).
Bütün sinaptik girdi sinyallerini IEEE-754 Neumaier kompanse toplamıyla sıfır kayıpla ve bit-birebir skaler değere indirger.
`sum(x: tensor<f32>) -> f32`""",
    "mean": """### 🌲 Dendritik Ortalama Potansiyel (`mean`)
**Rol:** Dendritik Normalize Membran Yükü.
Girdi tensörünün ortalama potansiyelini $1/N \\sum x_i$ şeklinde hesaplar.
`mean(x: tensor<f32>) -> f32`""",
    "l2_norm": """### 🌲 Dendritik Sinyal Enerjisi (`l2_norm`)
**Rol:** Dendritik Öklid Büyüklüğü (Signal Energy).
Sinaptik girdi vektörünün toplam $L_2$ enerjisini $\\sqrt{\\sum x_i^2}$ olarak hesaplar.
`l2_norm(x: tensor<f32>) -> f32`""",
    "norm": """### 🌲 Dendritik Sinyal Enerjisi (`norm`)
`l2_norm` fonksiyonunun eşdeğeri.
`norm(x: tensor<f32>) -> f32`""",
    "dot": """### 🌲 Sinaptik Nokta Çarpımı (`dot`)
**Rol:** Presinaptik Ağırlık İletimi (Synaptic Dot Product).
İki sinyal tensörünü $\\sum a_i \\cdot b_i$ şeklinde skaler potansiyelde birleştirir.
`dot(a: tensor<f32>, b: tensor<f32>) -> f32`""",
    "window_mean": """### 🌲 Dendritik Zamansal Kayar Pencere (`window_mean`)
**Rol:** Dendritik Düşük Geçiren Zamansal Filtre (Temporal Summation Filter).
Belirlenen pencere genişliği $k$ boyunca kayan ortalama uygular.
`window_mean(x: tensor<f32>, k: i32) -> tensor<f32>`""",
    "kernel": """### 🧠 Soma Çekirdeği (`kernel`)
**Rol:** Nöron Gövdesi (Soma Decision Center).
Bütün dendritik girdileri kanonik IR seviyesinde toplayıp metabolik ve semantik karara bağlayan hesaplama çekirdeği.""",
    "safety": """### 🛡️ Ranvier Düğümü İmmün Kalkanı (`safety`)
**Rol:** Ranvier Düğümleri ve İyonik Rejenerasyon.
Biyomedikal elektrot kopması, NaN/Inf ve aşırı gerilim darbelerini donanımsal olarak filtreler ve aksiyon potansiyelini deterministik olarak yeniler.""",
    "heal": """### 🛡️ Ranvier İyonik Şifa (`heal`)
**Politika:** `nonfinite = heal(değer)`
Bozuk sensör NaN/Inf veya sınır dışı değerlerini anında belirtilen değere dönüştürür ve anomali sayacını artırır.""",
    "reject": """### 🛡️ Ranvier İmmün Ret (`reject`)
**Politika:** `nonfinite = reject`
Bozuk sensör NaN/Inf tespit edildiğinde deterministik olarak yürütmeyi reddeder ve güvenli duruma geçer.""",
    "zero_output": """### 🛡️ Ranvier Sıfır Çıktı (`zero_output`)
**Politika:** `nonfinite = zero_output`
Bozuk girdilerde çekirdek formülünü işletmeden doğrudan güvenli şifa değerini çıktıya basar.""",
    "clamp": """### ⚡ Akson Tepesi Eşik Kapısı (`clamp`)
**Rol:** Eşikleme ve Doygunluk Sınırı (Threshold Clamping).
`clamp(x, lo, hi)` değeri $[lo, hi]$ fizyolojik aralığında sınırlar.""",
    "relu": """### ⚡ Akson Tepesi Düzeltici (`relu`)
**Rol:** Doğrultucu Eşik Fonksiyonu (Rectified Linear Activation).
Eşik altı potansiyelleri sıfırlar, eşik üstü potansiyelleri aksiyona iletir.""",
    "sigmoid": """### ⚡ Akson Tepesi Sigmoid Aktivasyonu (`sigmoid`)
**Rol:** Sinaptik Olasılık ve Doygunluk Fonksiyonu.
$S(x) = 1 / (1 + e^{-x})$ dönüşümü uygular.""",
    "neon": """### ⚡ Miyelin Kılıfı: ARM64 NEON (`neon`)
**Rol:** Sıçramalı İletim (Saltatory Conduction).
ARM64 NEON 128-bit vektör şeritleri ve donanım prefetch ile yüksek hızlı iletim sağlar.""",
    "avx2": """### ⚡ Miyelin Kılıfı: x86_64 AVX2 (`avx2`)
**Rol:** 256-bit AVX2+FMA Vektör Boru Hattı.""",
    "llvm": """### ⚡ Miyelin Kılıfı: LLVM SSA IR (`llvm`)
**Rol:** Doğrudan LLVM SSA IR derleme ve süperoptimizasyon.""",
}


class SynaxLanguageServer:
    """LSP 3.17 server for SYNAX (.sx) language files."""

    def __init__(self, in_stream: Optional[BinaryIO] = None, out_stream: Optional[BinaryIO] = None):
        self.in_stream = in_stream or sys.stdin.buffer
        self.out_stream = out_stream or sys.stdout.buffer
        self.documents: Dict[str, str] = {}
        self.shutdown_received: bool = False

    def send_response(self, response_id: Any, result: Any = None, error: Any = None) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": response_id}
        if error is not None:
            payload["error"] = error
        else:
            payload["result"] = result
        self._write_msg(payload)

    def send_notification(self, method: str, params: Any = None) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._write_msg(payload)

    def _write_msg(self, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        self.out_stream.write(header)
        self.out_stream.write(data)
        self.out_stream.flush()

    def read_message(self) -> Optional[Dict[str, Any]]:
        # Read header lines
        content_length: Optional[int] = None
        while True:
            line = self.in_stream.readline()
            if not line:
                return None
            line_str = line.decode("ascii", errors="replace").strip()
            if not line_str:
                break
            if line_str.lower().startswith("content-length:"):
                parts = line_str.split(":", 1)
                content_length = int(parts[1].strip())

        if content_length is None:
            return None

        body = self.in_stream.read(content_length)
        if len(body) < content_length:
            return None
        return json.loads(body.decode("utf-8"))

    def validate_document(self, uri: str, text: str) -> None:
        diagnostics: List[Dict[str, Any]] = []
        try:
            parse_module(text, check_types=True)
        except (SynaxLexError, SynaxParseError, SynaxTypeError) as err:
            span = getattr(err, "span", None)
            if span is not None:
                start_l = max(0, span.line - 1)
                start_c = max(0, span.col - 1)
                end_l = max(0, span.end_line - 1)
                end_c = max(start_c + 1, span.end_col - 1)
            else:
                start_l = start_c = end_l = 0
                end_c = 1

            diagnostics.append({
                "range": {
                    "start": {"line": start_l, "character": start_c},
                    "end": {"line": end_l, "character": end_c},
                },
                "severity": 1,  # Error
                "source": "synax",
                "message": getattr(err, "message", str(err)),
            })
        except Exception as exc:
            diagnostics.append({
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 1},
                },
                "severity": 1,
                "source": "synax",
                "message": str(exc),
            })

        self.send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": diagnostics,
        })

    def handle_hover(self, uri: str, line: int, char: int) -> Optional[Dict[str, Any]]:
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        if not (0 <= line < len(lines)):
            return None

        cur_line = lines[line]
        if not (0 <= char < len(cur_line)):
            return None

        # Find word boundaries around char
        match = None
        for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", cur_line):
            if m.start() <= char <= m.end():
                match = m
                break

        if not match:
            return None

        word = match.group(0)

        # Check neuro-symbolic builtins
        if word in NEURO_HOVER_DOCS:
            doc = NEURO_HOVER_DOCS[word]
            return {
                "contents": {
                    "kind": "markdown",
                    "value": doc,
                },
                "range": {
                    "start": {"line": line, "character": match.start()},
                    "end": {"line": line, "character": match.end()},
                },
            }

        # Try to resolve symbol in AST
        try:
            mod = parse_module(text, check_types=True)
            if mod.kernel is not None:
                for p in mod.kernel.params:
                    if p.name == word:
                        return {
                            "contents": {
                                "kind": "markdown",
                                "value": (
                                    f"### 🧬 Giriş Kanalı `{p.name}`\n"
                                    f"**Tip:** `{p.type_name}`\n"
                                    f"**Rol:** Presinaptik girdi kanalı."
                                ),
                            },
                        }
                for l in mod.kernel.lets:
                    if l.name == word:
                        t_str = str(l.inferred_type) if l.inferred_type else "f32"
                        return {
                            "contents": {
                                "kind": "markdown",
                                "value": (
                                    f"### 🧬 Ara Değişken `{l.name}`\n"
                                    f"**Tip:** `{t_str}`\n"
                                    f"**Rol:** Soma içi nöro-semantik durum."
                                ),
                            },
                        }
        except Exception:
            pass

        return None

    def handle_formatting(self, uri: str) -> List[Dict[str, Any]]:
        text = self.documents.get(uri, "")
        if not text:
            return []
        try:
            formatted = format_sx(text)
            if formatted == text:
                return []
            lines = text.splitlines()
            num_lines = max(1, len(lines))
            last_col = len(lines[-1]) if lines else 0
            return [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": num_lines, "character": last_col},
                    },
                    "newText": formatted,
                }
            ]
        except Exception:
            return []

    def handle_request(self, msg: Dict[str, Any]) -> None:
        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            res = {
                "capabilities": {
                    "textDocumentSync": 1,  # Full sync
                    "hoverProvider": True,
                    "documentFormattingProvider": True,
                },
                "serverInfo": {
                    "name": "synax-lsp",
                    "version": "0.6.0",
                },
            }
            self.send_response(req_id, result=res)
            return

        if method == "shutdown":
            self.shutdown_received = True
            self.send_response(req_id, result=None)
            return

        if method == "textDocument/hover":
            doc_uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            l = pos.get("line", 0)
            c = pos.get("character", 0)
            hover = self.handle_hover(doc_uri, l, c)
            self.send_response(req_id, result=hover)
            return

        if method == "textDocument/formatting":
            doc_uri = params.get("textDocument", {}).get("uri", "")
            edits = self.handle_formatting(doc_uri)
            self.send_response(req_id, result=edits)
            return

        self.send_response(req_id, error={"code": -32601, "message": f"Method {method} not found"})

    def handle_notification(self, msg: Dict[str, Any]) -> None:
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialized":
            return

        if method == "exit":
            sys.exit(0 if self.shutdown_received else 1)

        if method == "textDocument/didOpen":
            td = params.get("textDocument", {})
            uri = td.get("uri", "")
            text = td.get("text", "")
            self.documents[uri] = text
            self.validate_document(uri, text)
            return

        if method == "textDocument/didChange":
            td = params.get("textDocument", {})
            uri = td.get("uri", "")
            changes = params.get("contentChanges", [])
            if changes:
                # Full sync: first change contains new text
                text = changes[-1].get("text", "")
                self.documents[uri] = text
                self.validate_document(uri, text)
            return

        if method == "textDocument/didClose":
            td = params.get("textDocument", {})
            uri = td.get("uri", "")
            self.documents.pop(uri, None)
            self.send_notification("textDocument/publishDiagnostics", {
                "uri": uri,
                "diagnostics": [],
            })
            return

    def run(self) -> None:
        """Main stdio JSON-RPC loop."""
        while True:
            msg = self.read_message()
            if msg is None:
                break
            if "id" in msg:
                self.handle_request(msg)
            else:
                self.handle_notification(msg)


def run_lsp_server() -> None:
    server = SynaxLanguageServer()
    server.run()


if __name__ == "__main__":
    run_lsp_server()
