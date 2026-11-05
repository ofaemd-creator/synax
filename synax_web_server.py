#!/usr/bin/env python3
"""
SYNAX Local Studio & Compiler API Server (`synax_web_server.py`)
================================================================
Serves `sites/online_index.html` at `/studio` (and root `index.html` at `/`)
and exposes `/api/compile` & `/api/evolve` backed by the unified `SynaxCompiler`
(19-suite differential verification + native SIMD / LLVM IR execution).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from synax_sdk import compile_intent
from synax_telemetry import get_full_dashboard_payload, record_beacon
from synaxc import SynaxCompiler


class SynaxWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        if self.path in ("/studio", "/studio/"):
            self.path = "/sites/online_index.html"
        elif self.path in ("/dashboard", "/dashboard/", "/dashboard.html"):
            self.path = "/sites/dashboard.html"
        elif self.path in ("/synax_beacon.js", "/sites/synax_beacon.js"):
            self.path = "/sites/synax_beacon.js"
        elif self.path in ("/api/telemetry/stats", "/api/stats"):
            try:
                stats = get_full_dashboard_payload()
                self._send_json(200, stats)
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        return super().do_GET()

    def _send_json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 262_144:
            self._send_json(413, {"error": "Payload too large"})
            return
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        if self.path == "/api/telemetry/beacon":
            try:
                res = record_beacon(payload)
                self._send_json(200, res)
            except Exception as exc:
                self._send_json(422, {"error": str(exc)})
            return

        if self.path == "/api/compile":
            sx_text = str(payload.get("sx") or "")
            if not sx_text.strip():
                self._send_json(400, {"error": "Missing 'sx' source code"})
                return
            try:
                compiler = SynaxCompiler()
                res = compiler.compile(sx_text, bench_n=262_144, bench_repeats=7, verbose=False)
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "module": res.ir.name,
                        "ir_hash": res.ir.ir_hash,
                        "formula": res.ir.expr.to_human_formula(*res.ir.param_names),
                        "safety": res.ir.safety.to_dict(),
                        "winner": res.winner_name,
                        "winner_ms": round(res.winner_median_ms, 4),
                        "clang_o3_ms": round(res.clang_o3_median_ms, 4),
                        "speedup_vs_clang_o3": round(res.speedup_vs_clang_o3, 3),
                        "speedup_vs_scalar": round(res.speedup_vs_scalar, 3),
                        "suites_verified": res.suites_count,
                        "cache_hit": res.cache_hit,
                    },
                )
            except Exception as exc:
                self._send_json(422, {"ok": False, "error": str(exc)})
            return

        if self.path == "/api/evolve":
            sx_text = str(payload.get("sx", "niyet: derin rezonans hesapla"))
            is_tiny = bool(payload.get("tiny_mcu", False))
            try:
                kernel = compile_intent(sx_text, simulate_tiny_mcu=is_tiny)
                sample_a = [1.25, 2.50, -0.5, 4.0] * 25_000
                sample_b = [0.80, 1.10, 3.0, 0.5] * 25_000
                res = kernel.run(sample_a, sample_b, bias=-0.1)
                self._send_json(
                    200,
                    {
                        "operation": kernel.intent.operation,
                        "formula": kernel.intent.formula_desc,
                        "winner_dna": res["secilen_dna"],
                        "best_us": res["sure_us"],
                        "healed": res["onarilan_bozuk_veri"],
                        "preview": res["sonuc_ilk_5"],
                    },
                )
            except Exception as exc:
                self._send_json(422, {"error": str(exc)})
            return

        self._send_json(404, {"error": "Endpoint not found"})


def run_studio_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    print(f"📊 SYNAX Live Dashboard   : http://{host}:{port}/dashboard")
    print(f"🌐 SYNAX Local Studio IDE : http://{host}:{port}/studio")
    print(f"⚡ SYNAX Compiler REST API: POST http://{host}:{port}/api/compile")
    HTTPServer((host, port), SynaxWebHandler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SYNAX Local Studio & Compiler Server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    run_studio_server(host=args.host, port=args.port)
