#!/usr/bin/env python3
"""
SYNAX E-Graph Equality Saturation & Formal Interval Prover Suite (`tests/test_nextgen_2050.py`)
===============================================================================================
Cross-platform unit tests for `src/synax/egraph.py` and `src/synax/formal_prover.py`.
Runs cleanly on macOS, Linux, and Windows without requiring external C compilers.
"""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from synax.egraph import saturate_and_extract
from synax.formal_prover import prove_kernel_safety
from synax_ir import parse_sx, parse_symbolic_expression


class TestEGraphAndFormalProver(unittest.TestCase):
    def test_01_egraph_fma_and_relu_idempotence(self) -> None:
        expr = parse_symbolic_expression("relu(relu(a)) * b + b")
        rep = saturate_and_extract(expr, target="neon")
        self.assertLess(rep.cost_after, rep.cost_before)
        self.assertEqual(rep.optimized_ast.op, "FMA")
        self.assertIn("fma", rep.optimized_ast.to_human_formula())

    def test_02_egraph_pow2_and_pow3_fusion(self) -> None:
        expr = parse_symbolic_expression("(a * a) * a + 0.0")
        rep = saturate_and_extract(expr, target="neon")
        self.assertEqual(rep.optimized_ast.op, "POW3")

    def test_03_formal_interval_prover_safe_kernel(self) -> None:
        sx = """synax 1.0

kernel cerebral_cpp_safe(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
  safety {
    nonfinite = heal(0.0)
    output_range = clamp(0.0, 250.0)
  }
  let y = relu(a - b)
  return y
}
"""
        ir = parse_sx(sx)
        cert = prove_kernel_safety(ir, a_bounds=(50.0, 180.0), b_bounds=(5.0, 40.0))
        self.assertTrue(cert.all_verified)
        self.assertTrue(cert.div_by_zero_free)
        self.assertTrue(cert.overflow_free)
        self.assertEqual(cert.final_output_bounds.lo, 10.0)
        self.assertEqual(cert.final_output_bounds.hi, 175.0)
        self.assertEqual(len(cert.certificate_sha256), 16)

    def test_04_formal_interval_prover_detects_div_by_zero_hazard(self) -> None:
        sx = """synax 1.0

kernel div_hazard(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
  safety {
    nonfinite = heal(0.0)
  }
  let y = a / b
  return y
}
"""
        ir = parse_sx(sx)
        cert = prove_kernel_safety(ir, a_bounds=(10.0, 100.0), b_bounds=(-5.0, 5.0))
        self.assertFalse(cert.div_by_zero_free)
        self.assertGreater(len(cert.hazards), 0)


if __name__ == "__main__":
    unittest.main()
