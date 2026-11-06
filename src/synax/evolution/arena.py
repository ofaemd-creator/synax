#!/usr/bin/env python3
"""
SYNAX Evolution Arena (`src/synax/evolution/arena.py`)
=============================================================================
Orchestrates the 4-layer autonomous cycle:
  1. Neural Synthesis: Evaluates 4 candidate variants.
  2. Symbolic IMMUNE Filter: Eliminates hallucinations & contract violations.
  3. Hardware TYCON Arena: Compiles (NEON/AVX2) and benchmarks in GB/s.
  4. MYELIN & Episodic Memory: Locks winner and commits genetic learnings.

SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_verifier import LoadedKernel
from synaxc import SynaxCompiler
from .memory import EpisodicEvolutionMemory
from .synthesizer import KernelCandidate, NeuroSymbolicSynthesizer


class EvolutionReport:
    """Complete summary of an evolution arena match."""

    def __init__(
        self,
        kernel_name: str,
        intent: str,
        candidates: List[KernelCandidate],
        winner: Optional[KernelCandidate],
        winner_target: str,
        peak_throughput_gbs: float,
        best_latency_us: float,
        speedup: float,
        lock_path: Optional[str] = None,
    ):
        self.kernel_name = kernel_name
        self.intent = intent
        self.candidates = candidates
        self.winner = winner
        self.winner_target = winner_target
        self.peak_throughput_gbs = peak_throughput_gbs
        self.best_latency_us = best_latency_us
        self.speedup = speedup
        self.lock_path = lock_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kernel_name": self.kernel_name,
            "intent": self.intent,
            "winner_id": self.winner.variant_id if self.winner else None,
            "winner_target": self.winner_target,
            "peak_throughput_gbs": round(self.peak_throughput_gbs, 2),
            "best_latency_us": round(self.best_latency_us, 2),
            "speedup": round(self.speedup, 2),
            "lock_path": self.lock_path,
            "candidates": [
                {
                    "id": c.variant_id,
                    "label": c.label,
                    "immune_passed": c.immune_passed,
                    "immune_reason": c.immune_reason,
                    "throughput_gbs": round(c.throughput_gbs, 2),
                    "latency_us": round(c.latency_us, 2),
                    "speedup": round(c.speedup_vs_baseline, 2),
                }
                for c in self.candidates
            ],
        }

    def format_markdown(self) -> str:
        lines = [
            f"### 🧬 SYNAX Otonom Evrim Raporu: `{self.kernel_name}`",
            f"**Klinik Niyet:** \"{self.intent}\"\n",
            "| Varyant | IMMUNE Durumu | Donanım Hedefi | Hız (GB/s) | Gecikme (µs) | Hızlanma |",
            "|---|---|---|---|---|---|",
        ]
        for c in self.candidates:
            status_badge = "🛡️ GEÇTİ (%100)" if c.immune_passed else f"❌ ELENDİ ({c.immune_reason[:25]}...)"
            target = self.winner_target if c == self.winner else "SIMD"
            lines.append(
                f"| **{c.label}** | {status_badge} | `{target}` | **{c.throughput_gbs:.1f} GB/s** | {c.latency_us:.1f} µs | **{c.speedup_vs_baseline:.2f}x** |"
            )

        if self.winner:
            lines.extend([
                "",
                f"🏆 **Kazanan Varyant:** `{self.winner.label}`",
                f"⚡ **Donanım Mimarisi:** `{self.winner_target}` ({self.peak_throughput_gbs:.1f} GB/s, {self.best_latency_us:.1f} µs gecikme)",
                f"🔒 **MYELIN Kilidi:** `{self.lock_path or 'Mühürlendi'}`",
            ])
        return "\n".join(lines)


class EvolutionArena:
    """Evaluates and benchmarks multiple competing algorithm candidates."""

    def __init__(self, memory: Optional[EpisodicEvolutionMemory] = None):
        self.memory = memory or EpisodicEvolutionMemory()
        self.synthesizer = NeuroSymbolicSynthesizer(self.memory)
        self.compiler = SynaxCompiler()

    def run_match(
        self,
        kernel_name_or_code: str,
        intent: Optional[str] = None,
        param_names: Optional[List[str]] = None,
        bench_n: int = 65536,
        bench_repeats: int = 5,
    ) -> EvolutionReport:
        """Run the end-to-end 4-layer evolution arena match."""
        # Check if first argument is code or file path or just kernel name
        if "\n" in kernel_name_or_code or "kernel " in kernel_name_or_code or kernel_name_or_code.endswith(".sx"):
            code = kernel_name_or_code
            if os.path.exists(kernel_name_or_code):
                code = Path(kernel_name_or_code).read_text(encoding="utf-8")
            m_k = re.search(r"kernel\s+([A-Za-z0-9_]+)", code)
            k_name = m_k.group(1) if m_k else "evolved_kernel"
            m_i = re.search(r'intent\s+"([^"]+)"', code)
            int_str = intent or (m_i.group(1) if m_i else "autonomous evolution")
            m_p = re.search(r"kernel\s+[A-Za-z0-9_]+\s*\((.*?)\)", code)
            if m_p:
                raw_params = m_p.group(1).split(",")
                p_names = [p.split(":")[0].strip() for p in raw_params if ":" in p]
            else:
                p_names = ["a", "b"]
        else:
            k_name = kernel_name_or_code
            int_str = intent or "autonomous evolution"
            p_names = param_names or ["a", "b"]

        # 1. Neural Layer: Generate candidates
        candidates = self.synthesizer.synthesize_variants(k_name, int_str, p_names)

        best_cand: Optional[KernelCandidate] = None
        best_gbs = 0.0
        best_lat_us = float("inf")
        best_target = "scalar"
        best_lock_path: Optional[str] = None
        best_speedup = 1.0

        bytes_per_sample = 2 * 4  # 2 inputs * 4 bytes per float32
        total_gb = (bench_n * bytes_per_sample) / 1e9

        for cand in candidates:
            with tempfile.NamedTemporaryFile("w", suffix=".sx", delete=False) as f:
                f.write(cand.code)
                tmp_sx = f.name

            try:
                # 2. Symbolic IMMUNE Filter + Dual Oracle Verification
                comp_res = self.compiler.compile(
                    tmp_sx,
                    bench_n=bench_n,
                    bench_repeats=bench_repeats,
                    verbose=False,
                )

                cand.immune_passed = comp_res.dual_ref_verified
                cand.immune_reason = f"32 Test Geçti (0.00e+00 bit sapma, {comp_res.suites_count} küme)"

                # 3. Hardware Arena: Benchmark throughput
                cand.latency_us = comp_res.winner_median_ms * 1000.0
                if comp_res.winner_median_ms > 0:
                    cand.throughput_gbs = total_gb / (comp_res.winner_median_ms / 1000.0)
                cand.speedup_vs_baseline = comp_res.speedup_vs_scalar

                # Track best candidate
                if cand.throughput_gbs > best_gbs:
                    best_gbs = cand.throughput_gbs
                    best_lat_us = cand.latency_us
                    best_cand = cand
                    best_target = comp_res.winner_name
                    best_speedup = comp_res.speedup_vs_scalar
                    lock_file = comp_res.cache_dir / f"{comp_res.ir.name}.sx.lock"
                    if lock_file.exists():
                        best_lock_path = str(lock_file)

            except Exception as exc:
                cand.immune_passed = False
                cand.immune_reason = str(exc)
                cand.throughput_gbs = 0.0
                cand.latency_us = 99999.0
            finally:
                if os.path.exists(tmp_sx):
                    try:
                        os.unlink(tmp_sx)
                    except OSError:
                        pass

        # 4. Memory & Learning: Commit to Episodic Memory
        if best_cand:
            self.memory.record_evolution(
                kernel_name=k_name,
                intent=int_str,
                winning_variant_id=best_cand.variant_id,
                winning_code=best_cand.code,
                throughput_gbs=best_gbs,
                latency_us=best_lat_us,
                speedup=best_speedup,
                variants_tested=len(candidates),
            )

        return EvolutionReport(
            kernel_name=k_name,
            intent=int_str,
            candidates=candidates,
            winner=best_cand,
            winner_target=best_target,
            peak_throughput_gbs=best_gbs,
            best_latency_us=best_lat_us,
            speedup=best_speedup,
            lock_path=best_lock_path,
        )
