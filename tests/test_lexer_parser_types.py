#!/usr/bin/env python3
"""
SYNAX Language Frontend, Type System, Formatter, Semantic Lock & Python SDK Suite
(`tests/test_lexer_parser_types.py`)
=================================================================================
Cross-platform unit test suite (runs on macOS, Linux, and Windows with or without
a native C compiler) verifying:
  1. Lexer (`src/synax/lexer.py`) & caret (`^`) `SynaxLexError` diagnostics
  2. Recursive-Descent Typed AST Parser (`src/synax/parser.py`) & `SynaxIR` parity
  3. Static Type & Constraint System (`src/synax/type_system.py` / `SynaxTypeError`)
  4. Canonical Formatter (`src/synax/formatter.py`) idempotence & `ir_hash` invariance
  5. Cryptographic Semantic Lock (`src/synax/semantic_lock.py`) 32 golden vectors & tamper rejection
  6. Reference Interpreter, Debugger, Hardware Fingerprint & Public Python SDK (`import synax`)
=================================================================================
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
for p in (str(SRC_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from synax_ir import parse_sx
from synax.formatter import format_sx
from synax.hardware import detect_hardware_fingerprint
from synax.interpreter import ReferenceInterpreter, SafetyRejectError
from synax.lexer import Lexer, SynaxLexError, TokenKind
from synax.parser import SynaxParseError, lower_to_synax_ir, parse_module
from synax.profiler_debugger import SynaxDebugger
from synax.semantic_lock import generate_lock, verify_lockfile, write_lockfile
from synax.type_system import SynaxTypeError, TypeChecker


class TestSynaxFrontendAndSDK(unittest.TestCase):
    def test_01_lexer_tokens_and_caret_errors(self) -> None:
        src = 'synax 0.5\nkernel demo(x: tensor<f32, 64>) -> tensor<f32> {\n  intent "test"\n  return x * 1e-40 + 3.4e38\n}\n'
        tokens = Lexer(src).tokenize()
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds[0], TokenKind.SYNAX)
        self.assertIn(TokenKind.KERNEL, kinds)
        self.assertIn(TokenKind.ARROW, kinds)
        self.assertIn(TokenKind.FLOAT, kinds)
        self.assertEqual(kinds[-1], TokenKind.EOF)

        with self.assertRaises(SynaxLexError) as ctx:
            Lexer("synax 0.1\nlet bad = a @ b\n").tokenize()
        self.assertIn("^", str(ctx.exception))

        with self.assertRaises(SynaxLexError):
            Lexer('intent "unterminated string\n').tokenize()

    def test_02_parser_and_ir_parity_across_all_examples(self) -> None:
        examples_dir = REPO_ROOT / "examples"
        sx_files = sorted(examples_dir.glob("*.sx"))
        self.assertGreaterEqual(len(sx_files), 5)

        for sx_file in sx_files:
            typed_ir = lower_to_synax_ir(sx_file)
            legacy_ir = parse_sx(str(sx_file))
            self.assertEqual(
                typed_ir.ir_hash,
                legacy_ir.ir_hash,
                f"IR hash mismatch on {sx_file.name}: {typed_ir.ir_hash} != {legacy_ir.ir_hash}",
            )

    def test_03_static_type_checker_rejects_invalid_programs(self) -> None:
        invalid_cases = [
            # 1. Undefined variable
            """
            synax 0.1
            kernel bad_undef(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
              return a + missing_var
            }
            """,
            # 2. Wrong builtin arity
            """
            synax 0.1
            kernel bad_arity(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
              return sigmoid(a, b)
            }
            """,
            # 3. Inverted clamp bounds (lo > hi) in expression
            """
            synax 0.1
            kernel bad_clamp(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
              return clamp(a - b, 10.0, -5.0)
            }
            """,
            # 4. Inverted safety clamp bounds
            """
            synax 0.1
            kernel bad_safety_clamp(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
              safety { nonfinite = heal(0.0); range_check = clamp(100.0, 20.0) }
              return a - b
            }
            """,
            # 5. Incompatible static tensor shapes in require
            """
            synax 0.1
            kernel bad_shapes(a: tensor<f32, 16>, b: tensor<f32, 32>) -> tensor<f32, 16> {
              require shape(a) == shape(b)
              return a + b
            }
            """,
            # 6. Boolean literal in arithmetic
            """
            synax 0.1
            kernel bad_bool_math(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> {
              return a + true
            }
            """,
        ]

        for idx, code in enumerate(invalid_cases):
            with self.subTest(case=idx):
                with self.assertRaises((SynaxTypeError, SynaxParseError)):
                    mod = parse_module(code)
                    self.assertIsNotNone(mod.kernel)
                    TypeChecker.check(mod.kernel)

    def test_04_formatter_idempotence_and_semantic_invariance(self) -> None:
        messy_structured = """
        synax   0.1
        // Hemodinamik başlık yorumu
        kernel   messy_cpp(  dbp : tensor<f32> , cvp:tensor<f32> )->tensor<f32>{
        intent   "CPP hesapla"
        require   shape(dbp)==shape(cvp)
        safety{nonfinite=heal(0);range_check=clamp(-50,300)}
        let   diff = ( dbp - cvp ) + 0.0
        return   diff * 1.0
        optimize   latency
        target   auto
        }
        """
        fmt1 = format_sx(messy_structured)
        fmt2 = format_sx(fmt1)
        self.assertEqual(fmt1, fmt2, "Formatter is not idempotent on structured .sx!")
        self.assertEqual(lower_to_synax_ir(messy_structured).ir_hash, lower_to_synax_ir(fmt1).ir_hash)

        for sx_file in sorted((REPO_ROOT / "examples").glob("*.sx")):
            raw = sx_file.read_text(encoding="utf-8")
            f1 = format_sx(raw)
            f2 = format_sx(f1)
            self.assertEqual(f1, f2, f"Formatter not idempotent on {sx_file.name}")
            self.assertEqual(lower_to_synax_ir(raw).ir_hash, lower_to_synax_ir(f1).ir_hash)

    def test_05_semantic_lockfile_golden_vectors_and_tamper_detection(self) -> None:
        src_cpp = (REPO_ROOT / "examples" / "hemodynamic_cpp.sx").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            sx_f = tmp_p / "hemodynamic_cpp.sx"
            sx_f.write_text(src_cpp, encoding="utf-8")

            lock_f = write_lockfile(sx_f)
            self.assertTrue(lock_f.exists())
            lock_json = json.loads(lock_f.read_text(encoding="utf-8"))
            self.assertEqual(lock_json["golden_vector_count"], 32)
            self.assertIn("_integrity_sha256", lock_json)

            ok, msg = verify_lockfile(sx_f, lock_f)
            self.assertTrue(ok, msg)

            # Verify against compiled native SIMD kernel on POSIX hosts with clang
            if os.name == "posix" and shutil.which("clang"):
                from synax_verifier import LoadedKernel
                from synaxc import SynaxCompiler

                comp = SynaxCompiler().compile(str(sx_f), bench_n=16_384, bench_repeats=3, verbose=False)
                lk = LoadedKernel(str(comp.winner_dylib_path), name=comp.winner_name)
                ok_nat, msg_nat = verify_lockfile(sx_f, lock_f, kernel=lk)
                self.assertTrue(ok_nat, msg_nat)

            # Tamper with golden vector output -> must fail SHA-256 integrity check
            tampered = dict(lock_json)
            tampered["total_expected_healed"] = 999
            lock_f.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
            ok_bad, msg_bad = verify_lockfile(sx_f, lock_f)
            self.assertFalse(ok_bad)
            self.assertIn("INTEGRITY_MISMATCH", msg_bad)

            # Re-lock cleanly, then alter .sx semantics -> must fail IR_HASH_DRIFT
            write_lockfile(sx_f)
            sx_f.write_text(src_cpp.replace("dbp - cvp", "dbp + cvp"), encoding="utf-8")
            ok_drift, msg_drift = verify_lockfile(sx_f, lock_f)
            self.assertFalse(ok_drift)
            self.assertIn("IR_HASH_DRIFT", msg_drift)

    def test_06_reference_interpreter_debugger_and_public_sdk(self) -> None:
        import synax

        self.assertEqual(synax.__version__, "0.6.1")
        hw = synax.hardware_info()
        self.assertEqual(len(hw.fingerprint_id), 12)

        cpp_path = str(REPO_ROOT / "examples" / "hemodynamic_cpp.sx")
        ir = synax.check_sx(cpp_path)
        self.assertEqual(ir.name, "coronary_perfusion_pressure")

        out, healed = synax.eval_sx(cpp_path, [90.0, float("nan")], [10.0, 12.0], prefer_native=False)
        self.assertAlmostEqual(out[0], 80.0, places=4)
        self.assertAlmostEqual(out[1], -12.0, places=4)
        self.assertEqual(healed, 1)

        # Strict reject policy in ReferenceInterpreter
        norm_path = str(REPO_ROOT / "examples" / "normalized_difference.sx")
        interp = ReferenceInterpreter(norm_path)
        with self.assertRaises(SafetyRejectError):
            interp.execute([1.0, float("nan")], [0.5, 0.2], strict_reject=True)

        # Step-by-step IEEE-754 debugger
        dbg = SynaxDebugger.trace_element(cpp_path, a_val=float("nan"), b_val=15.0, index=7)
        self.assertEqual(dbg.healed_count, 1)
        self.assertAlmostEqual(dbg.final_ref_f32, -15.0, places=4)
        self.assertIn("0x", dbg.final_ref_hex)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    print("=" * 72)
    print("🧬 SYNAX LANGUAGE SPEC, TYPED AST, LOCKFILE & SDK SUITE")
    print("=" * 72)
    unittest.main(verbosity=2)
