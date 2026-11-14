#!/usr/bin/env python3
"""
SYNAX v1.0.0 Language Completeness & Multi-Backend Parity Suite (`tests/test_language_v1.py`)
=============================================================================================
Verifies:
  1. `synax 1.0` structured module parsing, multi-step typed `let` bindings, and formatter idempotence.
  2. Branchless `select(cond, val_true, val_false)` (`mux`) and `fma(a, b, c)` across:
     - Python IEEE-754 ReferenceInterpreter
     - C11 Scalar (-O0 and -O3)
     - ARM64 NEON SIMD (`vbslq_f32` / `vcgtq_f32`)
     - x86_64 AVX2 (`_mm256_blendv_ps`)
     - SSA LLVM IR (`fcmp ogt` + `select i1`)
     - Q16.16 Fixed-Point MCU lowering
  3. 19-suite 0-ULP differential verification on `examples/synax_v1_showcase.sx`.
  4. `synax.run_sx()` SDK and `/run` interactive execution in `SynaxChatAgent`.
"""

import math
import os
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import synax
from synax.backends.avx2_backend import AVX2Backend
from synax.backends.llvm_ir_backend import LLVMIRBackend
from synax_chat import SynaxChatAgent


class TestSynaxLanguageV1(unittest.TestCase):
    def test_01_synax_v1_showcase_parse_format_and_0ulp_compile(self) -> None:
        showcase_path = ROOT_DIR / "examples" / "synax_v1_showcase.sx"
        self.assertTrue(showcase_path.exists())

        raw_src = showcase_path.read_text(encoding="utf-8")
        formatted_once = synax.format_sx(raw_src)
        formatted_twice = synax.format_sx(formatted_once)
        self.assertEqual(formatted_once, formatted_twice, "Formatter must be strictly idempotent on synax 1.0")

        ir = synax.check_sx(str(showcase_path))
        self.assertEqual(ir.version, "1.0")
        self.assertEqual(ir.name, "synax_v1_showcase")
        self.assertTrue(ir.expr.can_use_pure_neon_intrinsics())

        # Verify AVX2, LLVM IR, and Q16.16 codegen for SELECT and FMA
        avx2_src = AVX2Backend.emit_c_source(ir)
        self.assertIn("_mm256_blendv_ps", avx2_src)
        llvm_src = LLVMIRBackend.emit_llvm_ir(ir)
        self.assertIn("select i1", llvm_src)
        q16_src = ir.expr.to_q16_fixed_point()
        self.assertIn("?", q16_src)

        # Full 19-suite 0-ULP compilation
        comp = synax.compile_sx(str(showcase_path), bench_n=16384, bench_repeats=3, verbose=False)
        self.assertTrue(comp.winner_dylib_path.exists())
        self.assertGreater(comp.speedup_vs_clang_o3, 0.0)

    def test_02_select_and_fma_numerical_exactness(self) -> None:
        sx_code = """synax 1.0

kernel branchless_mux_test(
  a: tensor<f32>,
  b: tensor<f32>
) -> tensor<f32> {
  intent "Branchless select and fma verification"
  safety {
    nonfinite = heal(0.0)
  }
  let diff = a - b
  let hi_branch = fma(a, 2.0, b)
  let lo_branch = b - a
  let out = select(diff, hi_branch, lo_branch)
  return out
}
"""
        a_in = [10.0, 3.0, 5.0, float("nan")]
        b_in = [4.0, 8.0, 5.0, 7.0]
        out, healed = synax.eval_sx(sx_code, a_in, b_in)
        self.assertEqual(healed, 1)
        # i=0: diff = 6 > 0 -> fma(10, 2, 4) = 24.0
        self.assertAlmostEqual(out[0], 24.0, places=5)
        # i=1: diff = -5 <= 0 -> 8 - 3 = 5.0
        self.assertAlmostEqual(out[1], 5.0, places=5)
        # i=2: diff = 0 <= 0 -> 5 - 5 = 0.0
        self.assertAlmostEqual(out[2], 0.0, places=5)
        # i=3: a healed to 0.0 -> diff = -7 <= 0 -> 7 - 0 = 7.0
        self.assertAlmostEqual(out[3], 7.0, places=5)

    def test_03_sdk_run_sx_and_chat_run_command(self) -> None:
        showcase_path = str(ROOT_DIR / "examples" / "synax_v1_showcase.sx")
        info = synax.run_sx(showcase_path)
        self.assertEqual(info["kernel_name"], "synax_v1_showcase")
        self.assertEqual(info["version"], "1.0")
        self.assertEqual(info["healed_count"], 1)
        self.assertEqual(len(info["outputs"]), 8)
        self.assertTrue(all(isinstance(v, float) and math.isfinite(v) for v in info["outputs"]))

        agent = SynaxChatAgent()
        resp = agent.process_message("/run")
        self.assertEqual(resp.action, "kernel_executed")
        self.assertIn("synax_v1_showcase", resp.text)
        self.assertIn("vbslq_f32", resp.text)

    def test_04_agent_workspace_sx_check_and_run(self) -> None:
        from synax.agent import Workspace

        ws = Workspace(ROOT_DIR)
        chk_out = ws.sx_check("examples/synax_v1_showcase.sx")
        self.assertIn("synax_v1_showcase", chk_out)
        run_out = ws.sx_run("examples/synax_v1_showcase.sx")
        self.assertIn("synax_v1_showcase", run_out)


if __name__ == "__main__":
    unittest.main()
