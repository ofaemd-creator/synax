#!/usr/bin/env python3
"""
SYNAX Telegram Bot & Multi-Model Skill Bridge Tests (`tests/test_telegram_bot.py`)
==================================================================================
Tests command parsing, E-Graph optimization, Formal Interval Proving, 19-suite
IEEE-754 kernel verification, IMMUNE NaN healing, chat allowlist security, and
mocked Telegram Bot API long-polling dispatch.
"""

import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from synax.telegram_bot import SynaxTelegramBot, TelegramConfig


class TestSynaxTelegramBot(unittest.TestCase):
    def setUp(self) -> None:
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

        def fake_transport(method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            self.calls.append((method, payload))
            if method == "getMe":
                return {"ok": True, "result": {"id": 999, "is_bot": True, "username": "synax_compiler_bot"}}
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 42, "chat": {"id": payload.get("chat_id")}}}
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 1001,
                            "message": {
                                "message_id": 10,
                                "chat": {"id": 777},
                                "text": "/egraph (a * b + 1.0) + (a - a)",
                            },
                        }
                    ],
                }
            return {"ok": True, "result": {}}

        self.config = TelegramConfig(
            bot_token="TEST_TOKEN_DO_NOT_USE",
            default_chat_id="777",
            allowed_chat_ids={"777"},
            workspace_dir=REPO_ROOT,
        )
        self.bot = SynaxTelegramBot(config=self.config, http_transport=fake_transport)

    def test_01_help_and_status_commands(self) -> None:
        help_txt = self.bot.handle_command_text("/start", chat_id="777")
        self.assertIn("SYNAX Telegram Bot", help_txt)
        self.assertIn("/egraph", help_txt)
        self.assertIn("/prove", help_txt)

        status_txt = self.bot.handle_command_text("/status", chat_id="777")
        self.assertIn("SYNAX Telegram & Sistem Durumu", status_txt)
        self.assertIn("E-Graph Saturation", status_txt)

    def test_02_egraph_command_fusion(self) -> None:
        reply = self.bot.handle_command_text("/egraph (a * b + 1.0) + (a - a)", chat_id="777")
        self.assertIn("E-Graph Eşitlik Doygunluğu", reply)
        self.assertIn("fma(a, b, 1)", reply)

    def test_03_prove_command_interval_certificate(self) -> None:
        reply = self.bot.handle_command_text("/prove relu(a - b)", chat_id="777")
        self.assertIn("Statik IEEE-754 Aralık Kanıtlayıcı", reply)
        self.assertIn("KANITLANDI (SAFE)", reply)
        self.assertIn("[0.0000, 250.0000]", reply)

    def test_04_check_and_run_commands(self) -> None:
        chk = self.bot.handle_command_text("/check relu(a - b) * 0.5", chat_id="777")
        self.assertIn("19-Küme IEEE-754 Doğrulaması Başarılı", chk)
        self.assertIn("0-ULP Geçti", chk)

        run_out = self.bot.handle_command_text("/run relu(a - b)", chat_id="777")
        self.assertIn("SYNAX Çekirdek Yürütme Sonucu", run_out)
        self.assertIn("[80.0, 90.0, 0.0, 0.0]", run_out)
        self.assertIn("1 adet NaN/Inf -> 0.0", run_out)

    def test_05_unauthorized_chat_id_blocked(self) -> None:
        denied = self.bot.handle_command_text("/status", chat_id="999999")
        self.assertIn("Yetkisiz Chat ID", denied)

    def test_06_poll_once_processes_and_replies(self) -> None:
        count = self.bot.poll_once()
        self.assertEqual(count, 1)
        methods = [m for m, _ in self.calls]
        self.assertIn("getUpdates", methods)
        self.assertIn("sendMessage", methods)
        sent_payload = [p for m, p in self.calls if m == "sendMessage"][0]
        self.assertEqual(sent_payload["chat_id"], "777")
        self.assertIn("fma(a, b, 1)", sent_payload["text"])


if __name__ == "__main__":
    unittest.main()
