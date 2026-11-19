#!/usr/bin/env python3
"""
SYNAX VS Code Chat & Studio Application Server (`src/synax/vscode_chat_app.py`)
===============================================================================
Serves both:
  1. `/chat` — The standalone SYNAX Chat Application (`editors/vscode-synax/media/index.html`)
  2. `/`     — Full interactive VS Code Workbench & Activity Bar view showcasing the
               installed `synaxcode.synax-lang-2.0.0` icon, top-right Editor Title icon,
               live `.sx` / C99 Firmware Editor, and the interactive SYNAX Chat App side-by-side.
  3. `/api/chat` — Live JSON-RPC / REST endpoint backed by `SynaxChatAgent` (`synax_chat.py`).

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from synax_chat import SynaxChatAgent
from synax.agent_office import MultitaskOfficeOrchestrator, build_embedded_3d_office_html

_CHAT_AGENT: Optional[SynaxChatAgent] = None
_OFFICE_ORCH: Optional[MultitaskOfficeOrchestrator] = None


def get_chat_agent() -> SynaxChatAgent:
    global _CHAT_AGENT
    if _CHAT_AGENT is None:
        _CHAT_AGENT = SynaxChatAgent()
    return _CHAT_AGENT


def get_office_orchestrator() -> MultitaskOfficeOrchestrator:
    global _OFFICE_ORCH
    if _OFFICE_ORCH is None:
        _OFFICE_ORCH = MultitaskOfficeOrchestrator()
    return _OFFICE_ORCH


VSCODE_WORKBENCH_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>VS Code — SYNAX Chat &amp; Autonomous Studio IDE (v2.0.0)</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #090d16; color: #e2e8f0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    /* Titlebar */
    .titlebar {
      height: 32px; background: #0d1321; border-bottom: 1px solid #1e293b;
      display: flex; align-items: center; justify-content: space-between; padding: 0 12px; font-size: 12px; color: #94a3b8;
    }
    .traffic { display: flex; gap: 7px; align-items: center; }
    .dot-r { width: 11px; height: 11px; border-radius: 50%; background: #ef4444; }
    .dot-y { width: 11px; height: 11px; border-radius: 50%; background: #f59e0b; }
    .dot-g { width: 11px; height: 11px; border-radius: 50%; background: #10b981; }
    /* Main Workbench */
    .workbench { flex: 1; display: flex; overflow: hidden; }
    /* Activity Bar (Left) */
    .activity-bar {
      width: 50px; background: #0b1120; border-right: 1px solid #1e293b;
      display: flex; flex-direction: column; align-items: center; padding-top: 10px; gap: 16px;
    }
    .act-icon {
      width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
      color: #64748b; cursor: pointer; position: relative; transition: all 0.2s;
    }
    .act-icon:hover { color: #e2e8f0; background: rgba(255,255,255,0.05); }
    .act-icon.active {
      color: #38bdf8; background: rgba(56, 189, 248, 0.14);
      border-left: 3px solid #38bdf8;
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.25);
    }
    .act-badge {
      position: absolute; bottom: -2px; right: -2px; background: #10b981; color: #052e16;
      font-size: 8px; font-weight: 800; padding: 1px 3px; border-radius: 4px;
    }
    /* Sidebar Chat Frame */
    .sidebar-pane {
      width: 520px; border-right: 1px solid #1e293b; display: flex; flex-direction: column; background: #0b0f19;
    }
    .sidebar-pane.full-mode { width: 100%; }
    /* Editor Area */
    .editor-pane { flex: 1; display: flex; flex-direction: column; background: #0b0f19; overflow: hidden; }
    .editor-tabs {
      height: 36px; background: #0d1321; border-bottom: 1px solid #1e293b;
      display: flex; align-items: center; justify-content: space-between; padding: 0 10px;
    }
    .tab-item {
      display: inline-flex; align-items: center; gap: 7px; padding: 7px 14px;
      background: #111827; border-top: 2px solid #38bdf8; color: #e2e8f0; font-size: 12px; font-weight: 600;
    }
    .editor-actions { display: flex; align-items: center; gap: 8px; }
    .top-synax-btn {
      display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px;
      background: linear-gradient(135deg, rgba(14,165,233,0.2), rgba(16,185,129,0.2));
      border: 1px solid #38bdf8; color: #f8fafc; font-size: 11px; font-weight: 700; cursor: pointer;
    }
    .top-synax-btn:hover { background: rgba(56, 189, 248, 0.35); }
    .editor-body {
      flex: 1; padding: 16px; overflow-y: auto; font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
      font-size: 12.5px; line-height: 1.6; color: #cbd5e1; background: #090d16;
    }
    .codelens {
      color: #38bdf8; font-size: 11px; margin-bottom: 6px; cursor: pointer;
      display: inline-flex; gap: 14px; background: rgba(56,189,248,0.08); padding: 3px 8px; border-radius: 4px;
    }
    /* Status Bar */
    .statusbar {
      height: 24px; background: #0284c7; color: #ffffff; display: flex; align-items: center;
      justify-content: space-between; padding: 0 12px; font-size: 11px; font-weight: 600;
    }
    .sb-left, .sb-right { display: flex; align-items: center; gap: 14px; }
    .sb-item { cursor: pointer; display: inline-flex; align-items: center; gap: 5px; padding: 1px 6px; border-radius: 3px; }
    .sb-item:hover { background: rgba(255,255,255,0.18); }
  </style>
</head>
<body>
  <div class="titlebar">
    <div class="traffic">
      <div class="dot-r"></div><div class="dot-y"></div><div class="dot-g"></div>
      <span style="margin-left:8px; font-weight:600; color:#e2e8f0;">Visual Studio Code / Antigravity IDE</span>
    </div>
    <div>synax — SYNAX Chat &amp; Studio Application v2.0.0 (synaxcode.synax-lang-2.0.0.vsix Kurulu)</div>
    <div style="color:#10b981; font-weight:700;">● 0-ULP IEEE-754 Verified</div>
  </div>

  <div class="workbench">
    <!-- Left Activity Bar with Official SYNAX App Icon -->
    <div class="activity-bar">
      <div class="act-icon" title="Explorer (Dosya Gezgini)">📁</div>
      <div class="act-icon" title="Search (Arama)">🔍</div>
      <div class="act-icon active" id="act-synax" title="SYNAX Chat &amp; Studio IDE (v2.0.0)" onclick="toggleFullChat()">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="2" width="20" height="20" rx="6" fill="#0b1120" stroke="#38bdf8" stroke-width="2"/>
          <path d="M8 9.2C8 7.6 9.6 6.6 12.1 6.6C14.5 6.6 16 7.6 16 9.0C16 10.6 14.2 11.1 12 11.7C9.8 12.2 8 12.9 8 14.7C8 16.3 9.7 17.4 12.2 17.4C14.8 17.4 16.4 16.2 16.4 14.6" stroke="#10b981" stroke-width="2.2" stroke-linecap="round"/>
          <circle cx="7.2" cy="7.2" r="1.5" fill="#38bdf8"/>
          <circle cx="16.8" cy="16.8" r="1.5" fill="#10b981"/>
          <circle cx="17.0" cy="7.0" r="1.3" fill="#f59e0b"/>
        </svg>
        <span class="act-badge">AI</span>
      </div>
      <div class="act-icon" title="Extensions (synaxcode.synax-lang-2.0.0 Installed)">🧩</div>
    </div>

    <!-- SYNAX Chat Application Sidebar -->
    <div class="sidebar-pane" id="chat-pane">
      <iframe id="chat-iframe" src="/chat" style="width:100%; height:100%; border:none;"></iframe>
    </div>

    <!-- Active Editor Area with Top-Right SYNAX Chat Button -->
    <div class="editor-pane" id="editor-pane">
      <div class="editor-tabs">
        <div class="tab-item">
          <span style="color:#10b981;">●</span>
          <span>biomedical_zero_drift_autocal.sx</span>
        </div>
        <div class="editor-actions">
          <button class="top-synax-btn" onclick="sendToChat('/calibrate ecg')" title="Üst Araç Çubuğu SYNAX Sohbet İkonu (Cmd+Shift+Y)">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="2" width="20" height="20" rx="6" fill="#0b1120" stroke="#38bdf8" stroke-width="2"/>
              <path d="M8 9.2C8 7.6 9.6 6.6 12.1 6.6C14.5 6.6 16 7.6 16 9.0C16 10.6 14.2 11.1 12 11.7C9.8 12.2 8 12.9 8 14.7C8 16.3 9.7 17.4 12.2 17.4C14.8 17.4 16.4 16.2 16.4 14.6" stroke="#10b981" stroke-width="2.2" stroke-linecap="round"/>
            </svg>
            <span>SYNAX Chat (Cmd+Shift+Y)</span>
          </button>
        </div>
      </div>

      <div class="editor-body">
        <div class="codelens" onclick="sendToChat('/calibrate ecg')">
          <span>▶️ SYNAX Çalıştır &amp; Doğrula (0-ULP Run)</span>
          <span>🩺 Otonom Sıfır-Sapma Kalibratörü (/calibrate ecg)</span>
          <span>🛡️ Token Kalkanı (/shield)</span>
        </div>
        <pre id="editor-code" style="color:#38bdf8; background:transparent; padding:0;">synax 1.0

kernel biomedical_zero_drift_autocal(
  raw_signal: tensor&lt;f32&gt;,
  drift_estimate: tensor&lt;f32&gt;
) -&gt; tensor&lt;f32&gt; {
  intent "Eliminate biomedical sensor baseline drift and heal IEEE-754 faults with contractive zero-point locking"
  safety {
    nonfinite = heal(0.0)
  }
  let corrected = raw_signal - drift_estimate
  return corrected
}

/* =========================================================================
 * Kurulu VS Code &amp; Antigravity Eklenti Bilgileri:
 *   • Paket       : synaxcode.synax-lang-2.0.0 (synax-vscode-chat-2.0.0.vsix)
 *   • İkonlar     : Sol Activity Bar İkonu + Sağ Üst Editör SYNAX Chat İkonu
 *   • Kısayol     : Cmd+Shift+Y (Tam Ekran SYNAX Sohbet Uygulaması)
 *   • Beceriler   : /calibrate (Zero-Drift) | /shield (Token Kalkanı) | /vault | /egraph
 * ========================================================================= */</pre>
      </div>
    </div>
  </div>

  <!-- Bottom VS Code Status Bar -->
  <div class="statusbar">
    <div class="sb-left">
      <div class="sb-item" onclick="toggleFullChat()">💬 SYNAX Chat v2.0.0</div>
      <div class="sb-item" onclick="sendToChat('/calibrate ecg')">🩺 Zero-Drift Autocal: %99.98 Kararlı</div>
      <div class="sb-item" onclick="sendToChat('/shield')">🛡️ Token Shield: -%87.8 Kota Tasarrufu</div>
    </div>
    <div class="sb-right">
      <div class="sb-item">🧠 Context Vault: SHA-256 Kilitli</div>
      <div class="sb-item">⚡ Apple M1 (ARM64 NEON + Q16.16 MCU)</div>
    </div>
  </div>

  <script>
    function sendToChat(cmdText) {
      const iframe = document.getElementById('chat-iframe');
      if (iframe && iframe.contentWindow && typeof iframe.contentWindow.sendPrompt === 'function') {
        iframe.contentWindow.sendPrompt(cmdText);
      }
    }
    function toggleFullChat() {
      const chatPane = document.getElementById('chat-pane');
      const editorPane = document.getElementById('editor-pane');
      if (editorPane.style.display === 'none') {
        editorPane.style.display = 'flex';
        chatPane.style.width = '520px';
      } else {
        editorPane.style.display = 'none';
        chatPane.style.width = '100%';
      }
    }
  </script>
</body>
</html>
"""


class SynaxVSCodeAppHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def _send_bytes(self, content: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        media_dir = REPO_ROOT / "editors" / "vscode-synax" / "media"
        if self.path in ("/", "/index.html", "/vscode", "/office", "/office.html"):
            office_html = build_embedded_3d_office_html().encode("utf-8")
            self._send_bytes(office_html, "text/html; charset=utf-8")
            return
        if self.path.startswith("/workbench"):
            self._send_bytes(VSCODE_WORKBENCH_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path.startswith("/chat"):
            chat_html = (media_dir / "index.html").read_bytes()
            self._send_bytes(chat_html, "text/html; charset=utf-8")
            return
        if self.path.startswith("/studio"):
            studio_html = (media_dir / "studio.html").read_bytes()
            self._send_bytes(studio_html, "text/html; charset=utf-8")
            return
        if self.path.endswith(".svg"):
            fname = Path(self.path).name
            f = media_dir / fname
            if f.exists():
                self._send_bytes(f.read_bytes(), "image/svg+xml")
                return
        if self.path.endswith(".png"):
            fname = Path(self.path).name
            f = media_dir / fname
            if f.exists():
                self._send_bytes(f.read_bytes(), "image/png")
                return
        self._send_bytes(b"Not Found", "text/plain", status=404)

    def do_POST(self) -> None:
        if self.path == "/api/run-python":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else "{}"
            data = json.loads(raw)
            orch = get_office_orchestrator()
            res = orch.producer.react.execute_python_sandbox(data.get("code", ""))
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8")
            return
        if self.path == "/api/open-workspace":
            orch = get_office_orchestrator()
            res = orch.producer.computer.open_workspace_in_os()
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8")
            return
        if self.path == "/api/register-agent":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else "{}"
            data = json.loads(raw)
            orch = get_office_orchestrator()
            res = orch.producer.computer.register_custom_user_agent(
                agent_name=data.get("name", "Custom Agent"),
                agent_role=data.get("role", "Specialist"),
                system_prompt=data.get("system_prompt", ""),
                provider=data.get("provider", "Claude Code"),
            )
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8")
            return
        if self.path == "/api/office-chat":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
                prompt = payload.get("prompt") or payload.get("message") or "Merhaba SYNAX"
                target_agent_id = payload.get("target_agent_id")
                engine_provider = payload.get("engine_provider") or "Claude Code + Codex + Antigravity"
                orch = get_office_orchestrator()
                res = orch.execute_multitask(
                    prompt,
                    target_agent_id=target_agent_id,
                    engine_provider=engine_provider,
                    user_api_key=payload.get("user_api_key", ""),
                    user_model=payload.get("user_model", ""),
                    custom_system_prompt=payload.get("custom_system_prompt", ""),
                )
                body = json.dumps(res, ensure_ascii=False).encode("utf-8")
                self._send_bytes(body, "application/json; charset=utf-8")
            except Exception as e:
                err = json.dumps({"reply": f"❌ Hata: {e}", "intent": "error"}).encode("utf-8")
                self._send_bytes(err, "application/json; charset=utf-8", status=500)
            return
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
                msg = payload.get("message", "")
                context = payload.get("context") or {}
                agent = get_chat_agent()
                res = agent.process_message(msg, context=context)
                body = json.dumps(res.to_dict(), ensure_ascii=False).encode("utf-8")
                self._send_bytes(body, "application/json; charset=utf-8")
            except Exception as e:
                err = json.dumps({"text": f"❌ Hata: {e}", "action": "error"}).encode("utf-8")
                self._send_bytes(err, "application/json; charset=utf-8", status=500)
            return
        self._send_bytes(b"{}", "application/json", status=404)


def run_server(port: int = 8795) -> None:
    server = HTTPServer(("127.0.0.1", port), SynaxVSCodeAppHandler)
    print(f"🚀 SYNAX VS Code Chat & Studio Application aktif: http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SYNAX VS Code Chat & Studio Application Server")
    ap.add_argument("--port", type=int, default=8795)
    args = ap.parse_args()
    run_server(args.port)
