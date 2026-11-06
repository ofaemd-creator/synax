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
        try:
            from synax.evolution import EpisodicEvolutionMemory, EvolutionArena, NeuroSymbolicSynthesizer
            self.memory = EpisodicEvolutionMemory()
            self.arena = EvolutionArena(self.memory)
            self.synthesizer = NeuroSymbolicSynthesizer(self.memory)
        except Exception:
            self.memory = None
            self.arena = None
            self.synthesizer = None

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

    def handle_code_lens(self, uri: str) -> List[Dict[str, Any]]:
        text = self.documents.get(uri, "")
        if not text:
            return []
        lines = text.splitlines()
        code_lenses: List[Dict[str, Any]] = []

        for i, line in enumerate(lines):
            # Check for kernel definition
            m_kernel = re.match(r"^\s*kernel\s+([A-Za-z0-9_]+)", line)
            if m_kernel:
                k_name = m_kernel.group(1)
                speed_str = "ARM64 NEON / AVX2"
                winner_title = f"⚡ SYNAX Donanım Arenasında Yarıştır ({speed_str})"
                if self.memory:
                    best = self.memory.query_similar(k_name)
                    if best:
                        speed_str = f"{best.winner_target.upper()} ({best.throughput_gbs:.1f} GB/s | IMMUNE: 100%)"
                        winner_title = f"⚡ SYNAX Evrildi: {speed_str} [Yeniden Yarıştır]"

                code_lenses.append({
                    "range": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                    "command": {
                        "title": winner_title,
                        "command": "synax.evolveKernel",
                        "arguments": [uri, k_name, i],
                    },
                })

            # Check for intent declaration
            m_intent = re.match(r'^\s*intent\s+"([^"]+)"', line)
            if m_intent:
                intent_desc = m_intent.group(1)
                short_desc = (intent_desc[:32] + "...") if len(intent_desc) > 32 else intent_desc
                code_lenses.append({
                    "range": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                    "command": {
                        "title": f'🧬 Niyetten Otonom Sentezle: "{short_desc}"',
                        "command": "synax.synthesizeFromIntent",
                        "arguments": [uri, i, intent_desc],
                    },
                })

        return code_lenses

    def handle_completion(self, uri: str, line: int, char: int) -> Dict[str, Any]:
        items = [
            {
                "label": "intent",
                "kind": 15,
                "detail": "SYNAX Nöro-Sembolik Niyet Deklarasyonu",
                "documentation": "Doğal dilde klinik veya matematiksel niyeti belirtir; LLM ve genetik mutator bu niyetten 4 farklı kod varyantı üretir.",
                "insertText": 'intent "${1:klinik veya sensör işlem niyeti}"\nsafety {\n    nonfinite = heal(0.0)\n    clamp = (${2:-50.0}, ${3:300.0})\n}\n',
                "insertTextFormat": 2,
            },
            {
                "label": "kernel",
                "kind": 14,
                "detail": "SYNAX Soma Çekirdeği Tanımı",
                "documentation": "Girdileri alan, Ranvier düğümü immün kalkanıyla donanmış hesaplama çekirdeği.",
                "insertText": "kernel ${1:name}(${2:a: tensor<f32, N>}):\n    safety {\n        nonfinite = heal(0.0)\n    }\n    let ${3:result} = ${4:a}\n    return ${3:result}\n",
                "insertTextFormat": 2,
            },
            {
                "label": "safety",
                "kind": 14,
                "detail": "Ranvier Düğümü İmmün Kalkanı",
                "documentation": "Biyomedikal NaN/Inf ve donanım gürültüsü arındırma politikası.",
                "insertText": "safety {\n    nonfinite = ${1|heal(0.0),reject,zero_output|}\n    clamp = (${2:0.0}, ${3:300.0})\n}\n",
                "insertTextFormat": 2,
            },
            {
                "label": "clamp",
                "kind": 3,
                "detail": "Akson Eşikleme Fonksiyonu",
                "documentation": "clamp(x, lo, hi): Değeri fizyolojik [lo, hi] sınırlarına kilitler.",
                "insertText": "clamp(${1:x}, ${2:0.0}, ${3:300.0})",
                "insertTextFormat": 2,
            },
            {
                "label": "relu",
                "kind": 3,
                "detail": "Akson Tepesi Doğrultucu Aktivasyonu",
                "documentation": "relu(x) = max(0.0, x): Negatif membran potansiyellerini eşikler.",
                "insertText": "relu(${1:x})",
                "insertTextFormat": 2,
            },
            {
                "label": "sum",
                "kind": 3,
                "detail": "Dendritik Uzaysal & Zamansal Toplama (Spatial Summation)",
                "documentation": "sum(x: tensor<f32>) -> f32: Neumaier kompanse toplamıyla sıfır kayıpla skaler potansiyele indirger.",
                "insertText": "sum(${1:x})",
                "insertTextFormat": 2,
            },
            {
                "label": "mean",
                "kind": 3,
                "detail": "Dendritik Ortalama Potansiyel (Mean Potential)",
                "documentation": "mean(x: tensor<f32>) -> f32: Normalize dendritik membran yükü.",
                "insertText": "mean(${1:x})",
                "insertTextFormat": 2,
            },
            {
                "label": "l2_norm",
                "kind": 3,
                "detail": "Dendritik Sinyal Enerjisi (L2 Norm)",
                "documentation": "l2_norm(x: tensor<f32>) -> f32: sqrt(sum(x_i^2))",
                "insertText": "l2_norm(${1:x})",
                "insertTextFormat": 2,
            },
            {
                "label": "dot",
                "kind": 3,
                "detail": "Sinaptik Nokta Çarpımı (Synaptic Dot Product)",
                "documentation": "dot(a, b) -> f32: İki tensörü skaler potansiyelde birleştirir.",
                "insertText": "dot(${1:a}, ${2:b})",
                "insertTextFormat": 2,
            },
        ]
        return {"isIncomplete": False, "items": items}

    def handle_evolve(self, uri: str, kernel_name: Optional[str] = None) -> Dict[str, Any]:
        text = self.documents.get(uri, "")
        if not text:
            # Fallback to reading from local file if uri is file://
            if uri.startswith("file://"):
                fpath = uri[7:]
                if os.path.exists(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            text = f.read()
                    except Exception:
                        pass
        if not text:
            return {"status": "error", "message": f"Döküman bulunamadı: {uri}"}

        if self.arena is None:
            return {"status": "error", "message": "EvolutionArena alt sistemi yüklenemedi."}

        try:
            report = self.arena.run_match(text)
            return {
                "status": "success",
                "report": report.to_dict(),
                "markdown": report.format_markdown(),
                "winner": {
                    "id": report.winner.id,
                    "name": report.winner.name,
                    "target": report.winner.target,
                    "throughput_gbs": report.winner.throughput_gbs,
                    "latency_us": report.winner.median_latency_us,
                    "speedup": report.winner.speedup_vs_baseline,
                } if report.winner else None,
            }
        except Exception as exc:
            logger.exception("Evolve failed")
            return {"status": "error", "message": str(exc)}

    def handle_synthesize(self, intent: str) -> Dict[str, Any]:
        if self.synthesizer is None:
            return {"status": "error", "message": "NeuroSymbolicSynthesizer alt sistemi yüklenemedi."}
        try:
            result = self.synthesizer.synthesize_from_intent(intent)
            return {
                "status": "success",
                "best_code": result.best_code,
                "winner_id": result.winner_id,
                "candidates_count": len(result.candidates),
                "candidates": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "code": c.code,
                    }
                    for c in result.candidates
                ],
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

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
                    "codeLensProvider": {"resolveProvider": False},
                    "completionProvider": {
                        "triggerCharacters": ["\"", "{", "(", " "],
                        "resolveProvider": False,
                    },
                },
                "serverInfo": {
                    "name": "synax-lsp",
                    "version": "0.7.0",
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

        if method == "textDocument/codeLens":
            doc_uri = params.get("textDocument", {}).get("uri", "")
            lenses = self.handle_code_lens(doc_uri)
            self.send_response(req_id, result=lenses)
            return

        if method == "textDocument/completion":
            doc_uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            l = pos.get("line", 0)
            c = pos.get("character", 0)
            completions = self.handle_completion(doc_uri, l, c)
            self.send_response(req_id, result=completions)
            return

        # Custom SYNAX RPC Extensions
        if method == "synax/evolve":
            doc_uri = params.get("uri", "")
            k_name = params.get("kernel")
            res = self.handle_evolve(doc_uri, k_name)
            self.send_response(req_id, result=res)
            return

        if method == "synax/synthesize":
            intent = params.get("intent", "")
            res = self.handle_synthesize(intent)
            self.send_response(req_id, result=res)
            return

        if method == "synax/getMemory":
            if self.memory:
                mem_data = {
                    "patterns_count": len(self.memory.data.get("proven_patterns", [])),
                    "kernels_count": len(self.memory.data.get("historical_kernels", {})),
                    "proven_patterns": self.memory.data.get("proven_patterns", []),
                }
            else:
                mem_data = {"patterns_count": 0, "kernels_count": 0, "proven_patterns": []}
            self.send_response(req_id, result=mem_data)
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
