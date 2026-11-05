#!/usr/bin/env python3
"""
SYNAX Dendritic Reductions & Synaptic Ingestion Test Suite
(`tests/test_dendritic_reductions.py`)
=========================================================
Verifies neuroanatomical dendritic summation concepts:
  - Spatial & temporal summation: `sum`, `mean`, `l2_norm`, `dot`
  - Sliding-window temporal convolution: `window_mean`
  - IEEE-754 Neumaier compensated accumulation (zero cancellation drift)
  - Immune Shield non-finite healing & rejection during reduction
  - Static TypeChecker enforcement & shape reduction (tensor<f32> -> f32)
  - End-to-end native compilation and differential bit-exact verification
"""

from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest
from array import array
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
for p in (str(SRC_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import synax
from synax.interpreter import ReferenceInterpreter, SafetyRejectError
from synax.parser import parse_kernel, lower_to_synax_ir
from synax.type_system import SynaxTypeError, TypeChecker
from synaxc import SynaxCompiler


class TestDendriticReductions(unittest.TestCase):
    def test_01_type_checker_reduction_shape_and_types(self) -> None:
        valid_sx = """
        synax 0.5
        kernel dendritic_summation(signal: tensor<f32>, weights: tensor<f32>) -> f32 {
          require shape(signal) == shape(weights)
          safety {
            nonfinite = heal(0.0)
          }
          let net_input: tensor<f32> = signal * weights
          let total_pot: f32 = sum(net_input)
          let avg_pot: f32 = mean(signal)
          let energy: f32 = l2_norm(signal)
          let syn_dot: f32 = dot(signal, weights)
          return total_pot
        }
        """
        kd = parse_kernel(valid_sx, check_types=True)
        self.assertEqual(kd.name, "dendritic_summation")
        self.assertEqual(kd.return_type.format_canonical(), "f32")

    def test_02_type_checker_rejects_invalid_reductions(self) -> None:
        # Invalid: wrong arity to sum()
        bad_arity = """
        synax 0.5
        kernel bad_arity(a: tensor<f32>, b: tensor<f32>) -> f32 {
          return sum(a, b)
        }
        """
        with self.assertRaises(SynaxTypeError) as ctx:
            parse_kernel(bad_arity, check_types=True)
        self.assertIn("expects 1 argument", str(ctx.exception))

        # Invalid: dot with dimension mismatch
        bad_dim = """
        synax 0.5
        kernel bad_dim(a: tensor<f32, 16>, b: tensor<f32, 32>) -> f32 {
          return dot(a, b)
        }
        """
        with self.assertRaises(SynaxTypeError) as ctx:
            parse_kernel(bad_dim, check_types=True)
        self.assertIn("shape mismatch", str(ctx.exception))

        # Invalid: window_mean with zero/negative window
        bad_win = """
        synax 0.5
        kernel bad_win(a: tensor<f32>) -> tensor<f32> {
          return window_mean(a, 0)
        }
        """
        with self.assertRaises(SynaxTypeError) as ctx:
            parse_kernel(bad_win, check_types=True)
        self.assertIn("Window size", str(ctx.exception))

    def test_03_neumaier_summation_precision_and_immunity(self) -> None:
        sx = """
        synax 0.5
        kernel dendritic_energy(a: tensor<f32>) -> f32 {
          safety {
            nonfinite = heal(0.0)
          }
          return sum(a)
        }
        """
        ir = lower_to_synax_ir(sx)
        self.assertTrue(ir.is_reduction)
        interp = ReferenceInterpreter(ir)

        # Standard numbers
        a = [1.0, 2.0, 3.0, 4.0]
        res = interp.execute(a)
        self.assertEqual(len(res.output), 1)
        self.assertAlmostEqual(res.output[0], 10.0, places=5)
        self.assertEqual(res.healed_count, 0)

        # Extreme magnitude cancellation test: 1e7 + 1.0 - 1e7 + 2.0 == 3.0
        # In naive single precision, (1e7 + 1.0) == 1e7 (1.0 is completely lost!)
        # Neumaier tracks lost bits in the compensation accumulator!
        cancel_a = [1e7, 1.0, -1e7, 2.0]
        res_cancel = interp.execute(cancel_a)
        self.assertAlmostEqual(res_cancel.output[0], 3.0, places=4)

        # Non-finite immunity healing: [10.0, NaN, 20.0, Inf] with heal(0.0) -> 30.0, healed=2
        anom_a = [10.0, float("nan"), 20.0, float("inf")]
        res_anom = interp.execute(anom_a)
        self.assertAlmostEqual(res_anom.output[0], 30.0, places=5)
        self.assertEqual(res_anom.healed_count, 2)

    def test_04_l2_norm_and_mean_reductions(self) -> None:
        norm_sx = """
        synax 0.5
        kernel dendritic_norm(signal: tensor<f32>) -> f32 {
          return l2_norm(signal)
        }
        """
        ir_norm = lower_to_synax_ir(norm_sx)
        interp_norm = ReferenceInterpreter(ir_norm)
        # Vector: [3.0, 4.0] -> L2 norm = sqrt(9 + 16) = 5.0
        res_norm = interp_norm.execute([3.0, 4.0])
        self.assertAlmostEqual(res_norm.output[0], 5.0, places=5)

        mean_sx = """
        synax 0.5
        kernel dendritic_mean_pot(signal: tensor<f32>) -> f32 {
          return mean(signal)
        }
        """
        ir_mean = lower_to_synax_ir(mean_sx)
        interp_mean = ReferenceInterpreter(ir_mean)
        res_mean = interp_mean.execute([2.0, 4.0, 6.0, 8.0])
        self.assertAlmostEqual(res_mean.output[0], 5.0, places=5)

    def test_05_dendritic_dot_product(self) -> None:
        dot_sx = """
        synax 0.5
        kernel synaptic_dot(a: tensor<f32>, b: tensor<f32>) -> f32 {
          require shape(a) == shape(b)
          return dot(a, b)
        }
        """
        ir_dot = lower_to_synax_ir(dot_sx)
        interp_dot = ReferenceInterpreter(ir_dot)
        # a = [1.0, 2.0, 3.0], b = [4.0, 5.0, 6.0] -> 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32.0
        res_dot = interp_dot.execute([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        self.assertAlmostEqual(res_dot.output[0], 32.0, places=5)

    def test_06_native_compilation_and_differential_verification(self) -> None:
        kernel_code = """synax 0.5
kernel dendritic_sum_verified(signal: tensor<f32>) -> f32 {
  intent "Dendritic spatial summation with immune healing"
  safety {
    nonfinite = heal(0.0)
    range_check = clamp(-1000.0, 1000.0)
  }
  return sum(signal)
}
"""
        with tempfile.NamedTemporaryFile("w", suffix=".sx", delete=False) as f:
            f.write(kernel_code)
            tmp_path = f.name

        try:
            compiler = SynaxCompiler()
            res = compiler.compile(tmp_path, bench_n=4096, bench_repeats=3, verbose=False)
            self.assertTrue(res.dual_ref_verified)
            self.assertGreaterEqual(res.suites_count, 15)
            self.assertTrue(os.path.exists(res.winner_dylib_path))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
