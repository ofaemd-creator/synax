#!/usr/bin/env python3
"""
SYNAX Evolution Arena & Autonomous Compiler Test Suite (`tests/test_evolution_arena.py`)
=======================================================================================
Verifies the 4-layer neuro-symbolic self-evolution cycle:
  1. Neural Multi-Variant Synthesis (Synthesizer + Self-Correction)
  2. Symbolic IMMUNE & IEEE-754 Bit Parity Filtering
  3. Hardware Arena Benchmarking (ARM64 NEON / AVX2 throughput & median latency)
  4. Episodic Learning Memory (.synax/evolution_memory.json)
  5. MCP (Model Context Protocol) Server Protocol Tools
"""

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

from synax.evolution import (
    EpisodicEvolutionMemory,
    EvolutionArena,
    KernelCandidate,
    NeuroSymbolicSynthesizer,
    SynaxDreamDaemon,
)
from synax.mcp_server import SynaxMCPServer


class TestEvolutionArena(unittest.TestCase):
    def setUp(self):
        self.tmp_mem_path = Path("/tmp/test_evolution_memory.json")
        if self.tmp_mem_path.exists():
            self.tmp_mem_path.unlink()
        self.memory = EpisodicEvolutionMemory(memory_path=self.tmp_mem_path)

    def tearDown(self):
        if self.tmp_mem_path.exists():
            self.tmp_mem_path.unlink()

    def test_01_episodic_memory_persistence(self):
        self.assertIn("hardware_fingerprint", self.memory.data)
        self.assertIn("division_by_zero_guard", self.memory.data["discovered_patterns"])

        self.memory.record_evolution(
            kernel_name="test_cpp",
            intent="cerebral perfusion",
            winning_variant_id="var_b_branchless",
            winning_code="kernel test_cpp() { return 1.0 }",
            throughput_gbs=48.5,
            latency_us=12.2,
            speedup=3.4,
            variants_tested=4,
        )

        # Reload from disk
        reloaded = EpisodicEvolutionMemory(memory_path=self.tmp_mem_path)
        k = reloaded.query_similar("test_cpp")
        self.assertIsNotNone(k)
        self.assertEqual(k.throughput_gbs, 48.5)

    def test_02_neuro_symbolic_synthesis(self):
        synthesizer = NeuroSymbolicSynthesizer(self.memory)
        res = synthesizer.synthesize_from_intent("kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al")
        self.assertEqual(len(res.candidates), 4)
        self.assertIn("relu", res.best_code)
        self.assertTrue(res.winner_id.startswith("var_"))

    def test_03_self_correction_on_immune_feedback(self):
        synthesizer = NeuroSymbolicSynthesizer(self.memory)
        flawed = KernelCandidate(
            variant_id="flawed_v1",
            label="Flawed Division",
            code="kernel bad(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {\n  return a / b;\n}",
            hypothesis="Direct division without protection",
        )
        repaired = synthesizer.self_correct(flawed, "IMMUNE Exception: input[4] is 0.0 causing NaN/Inf divisor fault")
        self.assertIn("max(", repaired.code)
        self.assertIn("heal(0.0)", repaired.code)

    def test_04_evolution_arena_run_match(self):
        arena = EvolutionArena(self.memory)
        code = """synax 0.5
kernel shock_index_eval(hr: tensor<f32>, sbp: tensor<f32>) -> tensor<f32> {
    intent "shock index triage evaluation"
    safety {
        nonfinite = heal(0.0)
        clamp = (0.0, 300.0)
    }
    let si = hr / max(sbp, 1.0)
    return si
}
"""
        report = arena.run_match(code)
        self.assertIsNotNone(report.winner)
        self.assertTrue(report.winner.immune_passed)
        self.assertGreater(report.winner.throughput_gbs, 0.0)
        self.assertIn("shock_index_eval", self.memory.data["evolved_kernels"])

    def test_05_mcp_server_tools(self):
        mcp = SynaxMCPServer(self.memory)
        # 1. Compile and verify
        res = mcp.execute_tool("synax_compile_and_verify", {
            "code": "synax 0.5\nkernel test_mcp(a: tensor<f32>) -> tensor<f32> {\n  return a * 2.0\n}\n"
        })
        self.assertTrue(res.get("success", False))

        # 2. Benchmark
        bench_res = mcp.execute_tool("synax_benchmark", {
            "code": "synax 0.5\nkernel test_mcp(a: tensor<f32>) -> tensor<f32> {\n  return a * 2.0\n}\n",
            "target": "neon"
        })
        self.assertTrue(bench_res.get("success", False))
        self.assertIn("throughput_gbs", bench_res)

        # 3. Get evolution memory
        mem_res = mcp.execute_tool("synax_get_evolution_memory", {})
        self.assertTrue(mem_res.get("success", False))
        self.assertIn("patterns", mem_res)


if __name__ == "__main__":
    unittest.main()
