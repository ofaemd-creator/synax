#!/usr/bin/env python3
"""
Unit and Integration Tests for SYNAX DeepTech / MedTech Expansion
(`tests/test_deeptech_bridge_compliance.py`)
=============================================================================
Tests:
  1. `@synax.kernel` Python decorator with automated .sx synthesis & IMMUNE healing.
  2. C/C++ Header Emitter (`--emit-c-header`).
  3. IEC 62304 Class C Compliance Audit Report Generator.
  4. StdLib Biomedical and Edge Defense kernels.

SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

import math
import os
import shutil
import sys
import tempfile
import unittest
from array import array
from pathlib import Path

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

import synax
from synax.c_header_emitter import emit_c_header_and_source
from synax.compliance import generate_iec62304_audit_report
from synax_ir import parse_sx
from synaxc import SynaxCompiler


class TestDeepTechBridgeAndCompliance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="synax_deeptech_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_python_kernel_decorator(self):
        """Verify @synax.kernel traces Python AST, synthesizes .sx, and heals NaNs."""

        @synax.kernel(
            intent="Test MAP calculation with IMMUNE healing",
            nonfinite_heal=0.0,
            output_clamp=(0.0, 300.0),
        )
        def calc_map(sbp, dbp):
            return dbp + (sbp - dbp) / 3.0

        self.assertIn("kernel calc_map", calc_map.sx_source)
        self.assertTrue(os.path.exists(calc_map.winner_dylib_path))

        sbp = [120.0, float("nan"), 150.0]
        dbp = [80.0, 70.0, 95.0]
        res = calc_map(sbp, dbp)
        vals = res.tolist()

        self.assertEqual(len(vals), 3)
        self.assertAlmostEqual(vals[0], 93.3333, places=2)
        # The NaN element was healed to 0.0: 70.0 + (0.0 - 70.0)/3.0 = 46.666
        self.assertAlmostEqual(vals[1], 46.6666, places=2)
        self.assertFalse(math.isnan(vals[1]))
        self.assertAlmostEqual(vals[2], 113.3333, places=2)

    def test_c_header_emitter(self):
        """Verify C/C++ ABI .h and .c files are generated cleanly."""
        sx_path = os.path.join(_ROOT, "src", "synax", "stdlib", "biomed", "hemodynamic_triage.sx")
        ir = parse_sx(sx_path)
        out_dir = Path(self.temp_dir) / "c_export"

        h_path, c_path = emit_c_header_and_source(ir, out_dir)
        self.assertTrue(h_path.exists())
        self.assertTrue(c_path.exists())

        h_content = h_path.read_text(encoding="utf-8")
        self.assertIn("synax_hemodynamic_triage_run", h_content)
        self.assertIn("synax_hemodynamic_triage_sha256", h_content)

        c_content = c_path.read_text(encoding="utf-8")
        self.assertIn("synax_is_valid_f32", c_content)

    def test_iec62304_compliance_report(self):
        """Verify IEC 62304 Class C audit report generation."""
        sx_path = os.path.join(_ROOT, "src", "synax", "stdlib", "biomed", "cerebral_perfusion_guard.sx")
        compiler = SynaxCompiler()
        comp = compiler.compile(sx_path, bench_n=1024, bench_repeats=1, verbose=False)

        out_dir = Path(self.temp_dir) / "compliance"
        reports = generate_iec62304_audit_report(comp.ir, comp, out_dir)

        self.assertTrue(reports["json"].exists())
        self.assertTrue(reports["md"].exists())

        md_text = reports["md"].read_text(encoding="utf-8")
        self.assertIn("IEC 62304", md_text)
        self.assertIn("Class C", md_text)
        self.assertIn("0.00e+00", md_text)


if __name__ == "__main__":
    unittest.main()
