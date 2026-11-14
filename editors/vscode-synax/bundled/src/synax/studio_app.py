"""
SYNAX Studio Standalone Desktop & Web Application (`src/synax/studio_app.py`)
=============================================================================
Transforms SYNAX from a mere editor plugin into a full standalone application:
  1. Serves the full-screen `SYNAX Studio IDE` (`editors/vscode-synax/media/studio.html`)
     over a local loopback HTTP/JSON API (`127.0.0.1`).
  2. Exposes real endpoints for:
     - `/api/compile`: Compiles `.sx` code, runs 19-suite 0-ULP verification, E-Graph
       equality saturation (`src/synax/egraph.py`), and Formal Interval Proving
       (`src/synax/formal_prover.py`).
     - `/api/agent`: Runs the real tool-calling `Agent` (`src/synax/agent.py`).
     - `/api/ecosystem`: Installs/verifies Claude Code, Codex, Antigravity, Cursor,
       and OpenCode plugin integrations.
  3. Builds the native macOS desktop application bundle (`/Applications/SYNAX Studio.app`
     and `~/Desktop/SYNAX Studio.app`).

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
import socket
import stat
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import synax
from synax.backends.avx2_backend import AVX2Backend
from synax.backends.llvm_ir_backend import LLVMIRBackend
from synax.ecosystem import install_all_ecosystem_integrations
from synax.egraph import saturate_and_extract
from synax.formal_prover import prove_kernel_safety


def evaluate_studio_payload(sx_source: str, target: str = "neon") -> Dict[str, Any]:
    """Run full compile + 0-ULP + E-Graph saturation + Formal Interval Proof on `sx_source`."""
    run_info = synax.run_sx(sx_source)
    ir = synax.check_sx(sx_source)
    eg_report = saturate_and_extract(ir.expr, target=target)
    proof = prove_kernel_safety(ir, (-500.0, 500.0), (-500.0, 500.0))
    avx2_c = AVX2Backend.emit_c_source(ir)
    llvm_ir = LLVMIRBackend.emit_llvm_ir(ir)

    return {
        "ok": True,
        "run": run_info,
        "egraph": {
            "original_formula": eg_report.original_ast.to_human_formula(),
            "optimized_formula": eg_report.optimized_ast.to_human_formula(),
            "optimized_neon": eg_report.optimized_ast.to_neon_f32x4()
            if eg_report.optimized_ast.can_use_pure_neon_intrinsics()
            else eg_report.optimized_ast.to_c_scalar(),
            "eclasses": eg_report.eclasses_count,
            "enodes": eg_report.enodes_count,
            "iterations": eg_report.iterations_run,
            "cost_before": eg_report.cost_before,
            "cost_after": eg_report.cost_after,
            "cycle_reduction_pct": eg_report.cycle_reduction_pct,
            "rewrites": eg_report.rewrites_triggered,
        },
        "proof": proof.to_dict(),
        "backends": {
            "c_scalar": run_info["c_scalar"],
            "arm64_neon": run_info["c_neon"],
            "q16_mcu": run_info["c_q16"],
            "x86_avx2": avx2_c,
            "llvm_ir": llvm_ir,
        },
    }


class StudioHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def _send_json(self, code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/index.html", "/studio.html"):
            studio_html = REPO_ROOT / "editors" / "vscode-synax" / "media" / "studio.html"
            data = studio_html.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/status":
            from synax.frugal_engine import get_memory_and_footprint_stats
            from synax.hardware import detect_hardware_fingerprint

            hw = detect_hardware_fingerprint()
            self._send_json(
                200,
                {
                    "ok": True,
                    "version": "1.0.0",
                    "cpu": hw.cpu_brand,
                    "arch": hw.machine_arch,
                    "simd": hw.simd_isa,
                    "cores": hw.logical_cores,
                    "memory": get_memory_and_footprint_stats(),
                },
            )
            return
        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            req = {}

        path = self.path.split("?")[0]
        if path == "/api/compile":
            try:
                src = req.get("code", "")
                target = req.get("target", "neon")
                self._send_json(200, evaluate_studio_payload(src, target=target))
            except Exception as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            return

        if path == "/api/agent":
            from synax.agent import Agent, Workspace, http_chat, resolve_backend

            task = req.get("task", "").strip() or "examples/synax_v1_showcase.sx dosyasını sx_check ile kontrol et."
            allow_writes = bool(req.get("allow_writes", False))
            base_url, model_id, api_key = resolve_backend()
            logs = []

            def _approve(name: str, args: Dict[str, Any]) -> bool:
                if allow_writes:
                    return True
                logs.append(f"🔒 {name} salt-okunur modda engellendi (Yazma izni kutusunu işaretleyin)")
                return False

            try:
                ag = Agent(
                    Workspace(REPO_ROOT),
                    http_chat(base_url, model_id, api_key),
                    approve=_approve,
                    log=lambda m: logs.append(str(m)),
                    max_steps=15,
                )
                reply = ag.run(task)
                self._send_json(200, {"ok": True, "model": model_id, "logs": logs, "reply": reply})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc), "logs": logs})
            return

        if path == "/api/ecosystem":
            try:
                res = install_all_ecosystem_integrations(REPO_ROOT)
                self._send_json(200, {"ok": True, **res})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})


def build_macos_app_bundle(target_app_path: Optional[Path] = None) -> Path:
    """Create a native macOS `.app` bundle (`SYNAX Studio.app`) in `/Applications` or `~/Applications`."""
    app_path = target_app_path or Path("/Applications/SYNAX Studio.app")
    try:
        contents = app_path / "Contents"
        macos_dir = contents / "MacOS"
        res_dir = contents / "Resources"
        macos_dir.mkdir(parents=True, exist_ok=True)
        res_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        app_path = Path.home() / "Applications" / "SYNAX Studio.app"
        contents = app_path / "Contents"
        macos_dir = contents / "MacOS"
        res_dir = contents / "Resources"
        macos_dir.mkdir(parents=True, exist_ok=True)
        res_dir.mkdir(parents=True, exist_ok=True)

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>SYNAXStudioLauncher</string>
    <key>CFBundleIdentifier</key>
    <string>org.synaxcode.studio</string>
    <key>CFBundleName</key>
    <string>SYNAX Studio</string>
    <key>CFBundleDisplayName</key>
    <string>SYNAX Studio</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    (contents / "Info.plist").write_text(plist, encoding="utf-8")

    py_bin = sys.executable or "/Users/o.farukaydin/.local/bin/python3"
    launcher_script = f"""#!/bin/zsh
export PYTHONPATH="{REPO_ROOT}:{REPO_ROOT / 'src'}"
exec "{py_bin}" "{REPO_ROOT / 'src' / 'synax' / 'studio_app.py'}" --launch-window
"""
    launcher_file = macos_dir / "SYNAXStudioLauncher"
    launcher_file.write_text(launcher_script, encoding="utf-8")
    launcher_file.chmod(launcher_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return app_path


def launch_studio_server(port: int = 0, open_window: bool = True) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", port))
    actual_port = sock.getsockname()[1]
    sock.close()

    server = ThreadingHTTPServer(("127.0.0.1", actual_port), StudioHTTPHandler)
    url = f"http://127.0.0.1:{actual_port}/"
    print(f"🚀 SYNAX Studio IDE Uygulaması Çalışıyor: {url}")

    if open_window:
        chrome_bin = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if chrome_bin.exists():
            subprocess.Popen([str(chrome_bin), f"--app={url}", "--window-size=1440,920"])
        else:
            webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    if "--build-app" in sys.argv:
        p = build_macos_app_bundle()
        print(f"✓ macOS Uygulaması Oluşturuldu: {p}")
    else:
        launch_studio_server(open_window=("--no-window" not in sys.argv))
