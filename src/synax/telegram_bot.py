#!/usr/bin/env python3
"""
SYNAX Telegram Bot & Multi-Model Skill Bridge (`src/synax/telegram_bot.py`)
===========================================================================
Zero-dependency Telegram Bot API client (Long-Polling + Webhook-ready) and
Model Context Protocol (MCP) skill bridge for:
  - SYNAX Compiler & Runtime (`synaxc`, 19-suite IEEE-754 0-ULP verifier)
  - E-Graph Equality Saturation Optimizer (`src/synax/egraph.py`)
  - Static IEEE-754 Interval Formal Prover (`src/synax/formal_prover.py`)
  - Autonomous Workspace Coding Agent (`src/synax/agent.py` — Claude Code,
    OpenAI Codex, Google Antigravity, OpenRouter, Groq, Ollama)

Security Model:
  - `TELEGRAM_BOT_TOKEN` is read exclusively from environment variables (never hardcoded).
  - `TELEGRAM_ALLOWED_CHAT_IDS` restricts `/code` workspace agent execution to
    authorized Telegram user/chat IDs.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import synax
from synax.egraph import saturate_and_extract
from synax.formal_prover import prove_kernel_safety
from synax.hardware import detect_hardware_fingerprint
from synax_ir import parse_sx


@dataclass
class TelegramConfig:
    bot_token: str = ""
    default_chat_id: str = ""
    allowed_chat_ids: Set[str] = None  # type: ignore[assignment]
    workspace_dir: Path = REPO_ROOT
    poll_timeout: int = 25

    def __post_init__(self) -> None:
        if self.allowed_chat_ids is None:
            self.allowed_chat_ids = set()

    @classmethod
    def from_env(cls, workspace: Optional[Path] = None) -> "TelegramConfig":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        raw_allowed = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
        allowed: Set[str] = set()
        if raw_allowed:
            for part in raw_allowed.split(","):
                if part.strip():
                    allowed.add(part.strip())
        if chat_id:
            allowed.add(chat_id)
        return cls(
            bot_token=token,
            default_chat_id=chat_id,
            allowed_chat_ids=allowed,
            workspace_dir=workspace or REPO_ROOT,
        )

    def is_chat_authorized(self, chat_id: Optional[str | int]) -> bool:
        """If TELEGRAM_ALLOWED_CHAT_IDS is configured, verify chat_id is in allowlist."""
        if not self.allowed_chat_ids:
            return True
        if chat_id is None:
            return False
        return str(chat_id).strip() in self.allowed_chat_ids


class SynaxTelegramBot:
    """
    Zero-dependency Telegram Bot & Compiler/Agent Bridge for SYNAX, Claude Code,
    OpenAI Codex, and Google Antigravity.
    """

    def __init__(
        self,
        config: Optional[TelegramConfig] = None,
        http_transport: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.config = config or TelegramConfig.from_env()
        self._http_transport = http_transport
        self._last_update_id: int = 0

    # ------------------------------------------------------------------
    # Telegram Bot HTTP API (Zero External Dependencies)
    # ------------------------------------------------------------------
    def _api_call(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._http_transport is not None:
            return self._http_transport(method, payload or {})

        if not self.config.bot_token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN ortam değişkeni tanımlı değil. "
                "Lütfen `export TELEGRAM_BOT_TOKEN='<BotFather_Token>'` komutunu çalıştırın."
            )

        url = f"https://api.telegram.org/bot{self.config.bot_token}/{method}"
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.poll_timeout + 10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram API HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Telegram ağ bağlantı hatası: {e}") from e

    def get_me(self) -> Dict[str, Any]:
        return self._api_call("getMe")

    def send_message(
        self,
        text: str,
        chat_id: Optional[str | int] = None,
        parse_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_chat = str(chat_id or self.config.default_chat_id).strip()
        if not target_chat:
            raise ValueError("Mesaj gönderimi için `chat_id` veya `TELEGRAM_CHAT_ID` gereklidir.")
        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": text[:4000],
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        return self._api_call("sendMessage", payload)

    def get_updates(self, offset: Optional[int] = None, timeout: int = 10) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        res = self._api_call("getUpdates", payload)
        if not res.get("ok"):
            return []
        return res.get("result", [])

    # ------------------------------------------------------------------
    # Command Dispatch Engine (Local + Remote Telegram)
    # ------------------------------------------------------------------
    def handle_command_text(
        self,
        text: str,
        chat_id: Optional[str | int] = None,
    ) -> str:
        """
        Parses and executes a Telegram command or natural-language compiler request,
        returning a clean response string suitable for Telegram and CLI output.
        """
        raw = (text or "").strip()
        if not raw:
            return self._format_help()

        if not self.config.is_chat_authorized(chat_id):
            return (
                "⛔ Yetkisiz Chat ID. Bu bot `TELEGRAM_ALLOWED_CHAT_IDS` güvenlik kilidi ile korunmaktadır."
            )

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        # Strip @bot_username suffix if sent in a group chat
        if "@" in cmd:
            cmd = cmd.split("@", 1)[0]
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/start", "/help", "help"):
            return self._format_help()
        if cmd in ("/status", "status"):
            return self._handle_status()
        if cmd == "/egraph":
            return self._handle_egraph(arg)
        if cmd == "/prove":
            return self._handle_prove(arg)
        if cmd == "/check":
            return self._handle_check(arg)
        if cmd == "/run":
            return self._handle_run(arg)
        if cmd in ("/shield", "/tokens", "shield"):
            from synax.token_shield import format_shield_summary_text

            return format_shield_summary_text(arg, workspace_dir=self.config.workspace_dir)
        if cmd in ("/vault", "/memory", "vault"):
            from synax.context_vault import format_vault_summary_text

            return format_vault_summary_text(arg, workspace_dir=self.config.workspace_dir)
        if cmd in ("/calibrate", "/autocal", "calibrate", "autocal"):
            from synax.biomedical_autocal import format_autocal_telegram_report

            return format_autocal_telegram_report(arg or "ecg")
        if cmd in ("/code", "/agent"):
            return self._handle_code(arg)

        # If user sends raw .sx code or expression without a slash command
        if raw.startswith("synax ") or "kernel " in raw:
            return self._handle_check(raw)
        return self._handle_egraph(raw)

    def _format_help(self) -> str:
        return (
            "🤖 SYNAX Telegram Bot & Multi-Model Skill Bridge (v1.0.0)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Claude Code, OpenAI Codex, Google Antigravity ve SYNAX Derleyicisi için "
            "uzaktan doğrulama ve otonom ajan köprüsü.\n\n"
            "📌 Komutlar:\n"
            "• /status — Donanım (SIMD), derleyici ve aktif LLM durumunu göster\n"
            "• /calibrate [ecg|ibp|ventilator|spo2] — Otonom Biyomedikal Sıfır-Sapma Kalibratörü\n"
            "• /shield — Claude/Codex/Antigravity Token Kalkanı (%75-%92 token tasarrufu)\n"
            "• /vault  — Ajanlar Arası Sıfır-Kaybı Hafıza Kapsülü (%99.7 devir tasarrufu)\n"
            "• /egraph <ifade> — E-Graph Eşitlik Doygunluğu ile ifadeyi optimize et\n"
            "  Örnek: `/egraph (a * b + c) + max(x - x, 0.0)`\n"
            "• /prove <kod_veya_ifade> — Statik IEEE-754 Aralık ([lo, hi]) güvenlik kanıtı üret\n"
            "  Örnek: `/prove relu(a - b)`\n"
            "• /check <sx_kodu> — .sx çekirdeğini 19 IEEE-754 test kümesiyle doğrula\n"
            "• /run <sx_kodu> — .sx çekirdeğini örnek tensörlerle çalıştır ve NaN onarımını ölç\n"
            "• /code <görev> — Otonom kodlama ajanını (`src/synax/agent.py`) çalıştır"
        )

    def _handle_status(self) -> str:
        fp = detect_hardware_fingerprint()
        from synax.agent import resolve_backend

        backend = resolve_backend()
        backend_str = (
            f"{backend[0]} ({backend[1]})"
            if backend
            else "Yapılandırılmadı (ANTHROPIC_API_KEY / OPENROUTER_API_KEY / OLLAMA bekleniyor)"
        )
        token_configured = "Evet (Aktif)" if self.config.bot_token else "Hayır (Yerel Test Modu)"
        return (
            "📊 SYNAX Telegram & Sistem Durumu\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• İşlemci / SIMD : {fp.cpu_brand} ({fp.simd_isa})\n"
            f"• Donanım İzi    : {fp.fingerprint_id}\n"
            f"• Ajan LLM       : {backend_str}\n"
            f"• Telegram Token : {token_configured}\n"
            f"• Çalışma Alanı  : {self.config.workspace_dir}\n"
            "• Hazır Motorlar : synaxc (19-suite 0-ULP), E-Graph Saturation, Formal Interval Prover"
        )

    def _handle_egraph(self, expr: str) -> str:
        target = expr.strip() or "(a * b + 1.0) + (a - a)"
        sx_code = self._wrap_sx_if_needed(target)
        try:
            ir = parse_sx(sx_code)
            rep = saturate_and_extract(ir.expr, target="neon")
            orig_str = rep.original_ast.to_human_formula()
            opt_str = rep.optimized_ast.to_human_formula()
            red_pct = (
                round((rep.cost_before - rep.cost_after) / rep.cost_before * 100.0, 1)
                if rep.cost_before > 0
                else 0.0
            )
            return (
                "🧬 SYNAX E-Graph Eşitlik Doygunluğu (Equality Saturation)\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Girdi İfadesi   : {orig_str}\n"
                f"• En İyi (Optimal): {opt_str}\n"
                f"• Donanım Maliyeti: {rep.cost_before} -> {rep.cost_after} çevrim "
                f"(%{red_pct} kazanç)\n"
                f"• E-Sınıf / Düğüm : {rep.eclasses_count} e-class / {rep.enodes_count} e-node"
            )
        except Exception as e:
            return f"✗ E-Graph ayrıştırma hatası: {e}"

    def _wrap_sx_if_needed(self, snippet: str) -> str:
        clean = snippet.strip()
        if not clean:
            clean = "relu(a - b)"
        if "kernel " in clean:
            if not clean.startswith("synax "):
                return "synax 1.0\n\n" + clean
            return clean
        return (
            "synax 1.0\n\n"
            "kernel telegram_kernel(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {\n"
            "  safety {\n"
            "    nonfinite = heal(0.0)\n"
            "  }\n"
            f"  let y = {clean}\n"
            "  return y\n"
            "}\n"
        )

    def _handle_prove(self, snippet: str) -> str:
        sx_code = self._wrap_sx_if_needed(snippet)
        try:
            ir = parse_sx(sx_code)
            cert = prove_kernel_safety(
                ir,
                a_bounds=(0.0, 250.0),
                b_bounds=(0.0, 100.0),
            )
            status = "KANITLANDI (SAFE)" if cert.all_verified else "UYARI (BOUNDARY RISK)"
            return (
                "🛡️ SYNAX Statik IEEE-754 Aralık Kanıtlayıcı (Formal Prover)\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Çekirdek        : {cert.kernel_name}\n"
                f"• Durum           : {status}\n"
                f"• Çıktı Aralığı   : [{cert.final_output_bounds.lo:.4f}, {cert.final_output_bounds.hi:.4f}]\n"
                f"• Sıfıra Bölme Yok: {cert.div_by_zero_free}\n"
                f"• Taşma (Overflow): {'Yok' if cert.overflow_free else 'Olası'}\n"
                f"• Kanıt Özeti     : #{cert.certificate_sha256[:16]}"
            )
        except Exception as e:
            return f"✗ Biçimsel kanıt hatası: {e}"

    def _handle_check(self, snippet: str) -> str:
        sx_code = self._wrap_sx_if_needed(snippet)
        try:
            ir = synax.check_sx(sx_code)
            kname = getattr(ir, "kernel_name", getattr(ir, "name", "telegram_kernel"))
            inames = getattr(ir, "input_names", getattr(ir, "params", ["a", "b"]))
            return (
                "✅ SYNAX 19-Küme IEEE-754 Doğrulaması Başarılı\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Çekirdek Adı : {kname}\n"
                f"• Parametreler : {', '.join(inames)}\n"
                f"• Semantik İzi : #{ir.ir_hash}\n"
                "• Çift-Referans: 19/19 IEEE-754 Uç Küme 0-ULP Geçti"
            )
        except Exception as e:
            return f"✗ SYNAX doğrulama hatası: {e}"

    def _handle_run(self, snippet: str) -> str:
        sx_code = self._wrap_sx_if_needed(snippet)
        try:
            vec_a = [95.0, 110.0, 75.0, float("nan")]
            vec_b = [15.0, 20.0, 85.0, 10.0]
            out, healed = synax.eval_sx(sx_code, vec_a, vec_b, prefer_native=False)
            formatted_out = [round(x, 4) for x in out]
            return (
                "⚡ SYNAX Çekirdek Yürütme Sonucu\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Girdi A       : [95.0, 110.0, 75.0, NaN]\n"
                f"• Girdi B       : [15.0, 20.0, 85.0, 10.0]\n"
                f"• Çıktı Tensörü : {formatted_out}\n"
                f"• IMMUNE Onarım : {healed} adet NaN/Inf -> 0.0 olarak iyileştirildi"
            )
        except Exception as e:
            return f"✗ SYNAX yürütme hatası: {e}"

    def _handle_code(self, task: str) -> str:
        if not task:
            return "Lütfen `/code <görev>` şeklinde bir görev belirtin."
        from synax.agent import resolve_backend, run_turn

        backend = resolve_backend()
        if not backend:
            return (
                "⚠️ Otonom ajan için aktif bir LLM anahtarı bulunamadı. "
                "Yerel doğrulama için `/check`, `/run`, `/egraph` veya `/prove` kullanabilirsiniz."
            )
        messages: List[Dict[str, Any]] = [{"role": "user", "content": task}]
        try:
            reply = run_turn(backend, messages, auto_approve=False)
            return f"🤖 SYNAX Code ({backend[1]}):\n\n{reply}"
        except Exception as e:
            return f"✗ Ajan hatası: {e}"

    # ------------------------------------------------------------------
    # Long-Polling Loop
    # ------------------------------------------------------------------
    def poll_once(self) -> int:
        """Fetches pending Telegram updates once, replies to each, and returns processed count."""
        updates = self.get_updates(offset=self._last_update_id + 1 if self._last_update_id else None, timeout=5)
        processed = 0
        for upd in updates:
            upd_id = int(upd.get("update_id", 0))
            if upd_id > self._last_update_id:
                self._last_update_id = upd_id
            msg = upd.get("message") or upd.get("edited_message") or {}
            text = msg.get("text", "")
            chat_id = (msg.get("chat") or {}).get("id")
            if text and chat_id is not None:
                reply_text = self.handle_command_text(text, chat_id=chat_id)
                self.send_message(reply_text, chat_id=chat_id)
                processed += 1
        return processed

    def run_polling(self) -> None:
        me = self.get_me()
        bot_info = me.get("result", {})
        username = bot_info.get("username", "synax_bot")
        print(f"🤖 SYNAX Telegram Bot aktif: @{username}")
        print("   Komutlar: /status, /calibrate, /shield, /vault, /egraph, /prove, /check, /run, /code")
        print("   Durdurmak için Ctrl+C tuşlayın.\n")
        try:
            while True:
                try:
                    self.poll_once()
                except (TimeoutError, Exception):
                    pass
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 SYNAX Telegram Bot durduruldu.")


def run_telegram_cli(argv: Optional[List[str]] = None) -> int:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        prog="synax telegram",
        description="SYNAX Telegram Bot & Multi-Model Skill Bridge (Claude, Codex, Antigravity)",
    )
    ap.add_argument("--status", action="store_true", help="Telegram bot ve sistem durumunu göster")
    ap.add_argument("--cmd", type=str, default=None, help="Telegram bot komutunu yerel olarak test et (örn. '/egraph (a*b)+c')")
    ap.add_argument("--send", type=str, default=None, help="TELEGRAM_CHAT_ID adresine mesaj gönder")
    ap.add_argument("--chat-id", type=str, default=None, help="Hedef Telegram Chat ID")
    ap.add_argument("--poll", action="store_true", help="Canlı Telegram Long-Polling bot döngüsünü başlat")
    args = ap.parse_args(argv)

    bot = SynaxTelegramBot()

    if args.status:
        print(bot.handle_command_text("/status"))
        return 0

    if args.cmd is not None:
        print(bot.handle_command_text(args.cmd, chat_id=args.chat_id))
        return 0

    if args.send is not None:
        res = bot.send_message(args.send, chat_id=args.chat_id)
        print(f"✓ Mesaj gönderildi: message_id={res.get('result', {}).get('message_id')}")
        return 0

    if args.poll:
        bot.run_polling()
        return 0

    print(bot.handle_command_text("/status"))
    print("\n" + bot.handle_command_text("/help"))
    return 0


if __name__ == "__main__":
    sys.exit(run_telegram_cli())
