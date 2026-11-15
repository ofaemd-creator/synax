#!/usr/bin/env python3
"""
Unit & Integration Tests for SYNAX Token Shield & Context Vault (`tests/test_token_shield.py`)
==============================================================================================
Verifies:
  1. AST-Aware Code Skeletonization for Python, C/TS/Rust/SX with focus_symbol support
  2. Surgical Terminal Log & Stack-Trace Deduplication
  3. SHA-256 Content-Hash Semantic Cache hit/miss behavior
  4. Prompt-Cache Prefix Aligner for Anthropic Claude (`cache_control: ephemeral`) & OpenAI Codex
  5. Frugal Model Tier Router (`TIER_0_LOCAL_ZERO_TOKEN`, `TIER_1_FRUGAL_FLASH_FREE`, `TIER_2_FRONTIER_SHIELDED`)
  6. Cross-Agent Semantic Handoff Capsule (`SynaxContextVault`)
  7. Telegram Bot `/shield` and `/vault` integration
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from synax.context_vault import SynaxContextVault, format_vault_summary_text
from synax.telegram_bot import SynaxTelegramBot
from synax.token_shield import (
    FrugalModelRouter,
    SemanticTokenCache,
    benchmark_directory_shield,
    build_cache_aligned_payload,
    compress_terminal_output,
    estimate_tokens,
    format_shield_summary_text,
    skeletonize_code,
)


SAMPLE_PYTHON_MODULE = '''
import math
from typing import List, Dict

MAX_BUFFER_SIZE = 4096


class SignalConditioner:
    """High-precision biomedical signal processor for 250 Hz ECG streams."""

    sample_rate: float = 250.0

    def __init__(self, gain: float = 1.0) -> None:
        """Initialize conditioner with hardware gain."""
        self.gain = gain
        self.history: List[float] = []
        for idx in range(64):
            self.history.append(float(idx) * 0.01)

    def sanitize_window(self, samples: List[float], baseline: List[float]) -> List[float]:
        """Remove baseline wander and heal non-finite IEEE-754 anomalies."""
        cleaned: List[float] = []
        for a, b in zip(samples, baseline):
            diff = (a - b) * self.gain
            if math.isnan(diff) or math.isinf(diff):
                cleaned.append(0.0)
            elif diff < 0.0:
                cleaned.append(0.0)
            else:
                cleaned.append(diff)
        return cleaned

    def compute_energy(self, values: List[float]) -> float:
        """Compute mean nonlinear energy across window."""
        total = 0.0
        for v in values:
            total += v * v
        return total / max(1, len(values))
'''


class TestTokenShieldAndVault(unittest.TestCase):
    def test_ast_python_skeletonizer_saves_tokens(self) -> None:
        rep = skeletonize_code(SAMPLE_PYTHON_MODULE, filename="conditioner.py")
        self.assertEqual(rep.strategy, "ast_python_skeleton")
        self.assertLess(rep.compressed_tokens, rep.original_tokens)
        self.assertGreaterEqual(rep.reduction_pct, 35.0)
        self.assertIn("class SignalConditioner:", rep.compressed_text)
        self.assertIn("def sanitize_window(", rep.compressed_text)
        self.assertIn("lines elided", rep.compressed_text)

    def test_ast_python_focus_symbol_preserves_body(self) -> None:
        rep = skeletonize_code(
            SAMPLE_PYTHON_MODULE,
            filename="conditioner.py",
            focus_symbol="compute_energy",
        )
        self.assertIn("total += v * v", rep.compressed_text)
        self.assertIn("def sanitize_window(", rep.compressed_text)

    def test_brace_language_skeletonizer(self) -> None:
        c_code = """
        #include <stdint.h>
        void synax_kernel(const float* a, const float* b, float* out, int n) {
            for (int i = 0; i < n; ++i) {
                float d = a[i] - b[i];
                out[i] = d > 0.0f ? d : 0.0f;
            }
        }
        """
        rep = skeletonize_code(c_code, filename="kernel.c")
        self.assertEqual(rep.strategy, "structural_brace_skeleton")
        self.assertIn("#include <stdint.h>", rep.compressed_text)
        self.assertIn("lines elided", rep.compressed_text)

    def test_terminal_log_deduplicator(self) -> None:
        noisy_log = "\n".join(
            ["[INFO] Compiling module step..."] * 40
            + ["ERROR: Undefined symbol _synax_fast_exp at 0x7fff0012"]
            + ["[DEBUG] Worker heartbeat OK"] * 40
        )
        rep = compress_terminal_output(noisy_log)
        self.assertGreater(rep.reduction_pct, 60.0)
        self.assertIn("ERROR: Undefined symbol", rep.compressed_text)
        self.assertIn("identical lines collapsed", rep.compressed_text)

    def test_semantic_sha256_cache_hit(self) -> None:
        cache = SemanticTokenCache()
        first = cache.read_or_stub("conditioner.py", SAMPLE_PYTHON_MODULE, turn_index=1)
        second = cache.read_or_stub("conditioner.py", SAMPLE_PYTHON_MODULE, turn_index=2)
        self.assertEqual(cache.cache_misses, 1)
        self.assertEqual(cache.cache_hits, 1)
        self.assertEqual(second.strategy, "sha256_cache_hit")
        self.assertIn("SYNAX-CACHE-HIT", second.compressed_text)
        self.assertGreater(second.reduction_pct, 80.0)

    def test_prompt_cache_prefix_aligner(self) -> None:
        static_rules = "Always enforce 0-ULP IEEE-754 verification. " * 40
        repo_map = "src/synax/egraph.py, src/synax/formal_prover.py " * 40
        task = "Optimize relu(a - b) for ARM64 NEON"
        claude_payload = build_cache_aligned_payload(static_rules, repo_map, task, provider="anthropic")
        self.assertEqual(claude_payload["provider"], "anthropic_claude")
        self.assertEqual(claude_payload["system"][0]["cache_control"]["type"], "ephemeral")
        self.assertGreater(claude_payload["token_metrics"]["billing_reduction_pct"], 70.0)

    def test_frugal_model_router_tiers(self) -> None:
        router = FrugalModelRouter()
        d0 = router.route("Run egraph equality saturation and prove IEEE-754 bounds", context_tokens=5000)
        self.assertEqual(d0.tier, "TIER_0_LOCAL_ZERO_TOKEN")
        self.assertEqual(d0.estimated_llm_tokens_used, 0)

        d1 = router.route("Add docstring to helper function", context_tokens=3000)
        self.assertEqual(d1.tier, "TIER_1_FRUGAL_FLASH_FREE")
        self.assertLess(d1.estimated_llm_tokens_used, 1000)

        d2 = router.route("Refactor entire distributed architecture and fix concurrency bug", context_tokens=10000)
        self.assertEqual(d2.tier, "TIER_2_FRONTIER_SHIELDED")
        self.assertLess(d2.estimated_llm_tokens_used, 3000)

    def test_context_vault_handoff_capsule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            vault = SynaxContextVault(workspace_dir=REPO_ROOT, vault_path=vpath)
            cap = vault.create_capsule(
                active_goal="Minimize Claude & Codex token burn",
                source_agent="claude-code",
                target_agent="openai-codex",
            )
            vault.save_capsule(cap)
            loaded = vault.load_latest_capsule()
            self.assertEqual(loaded.capsule_id, cap.capsule_id)
            self.assertLess(loaded.capsule_tokens, 250)
            self.assertIn("SYNAX-CONTEXT-VAULT", loaded.to_compact_prompt())

    def test_telegram_bot_shield_and_vault_commands(self) -> None:
        bot = SynaxTelegramBot()
        shield_reply = bot.handle_command_text("/shield")
        self.assertIn("SYNAX Token Shield", shield_reply)
        self.assertIn("TASARRUF", shield_reply)

        vault_reply = bot.handle_command_text("/vault")
        self.assertIn("SYNAX Context Vault", vault_reply)
        self.assertIn("SYNAX-CONTEXT-VAULT", vault_reply)


if __name__ == "__main__":
    unittest.main()
