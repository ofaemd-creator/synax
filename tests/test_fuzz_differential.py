#!/usr/bin/env python3
"""
SYNAX DIFFERENTIAL PROPERTY & FUZZ TESTER (tests/test_fuzz_differential.py)
=============================================================================
Generates randomized valid `.sx` structured kernels across nested arithmetic,
transcendentals, `let` bindings, and all 4 `SafetyPolicy` contracts, then
compares 4 independent execution backends bit-by-bit / within `1e-5` rtol:

  1. Pure-Python IEEE-754 Reference Interpreter (`ReferenceInterpreter`)
  2. Unoptimized C11 Scalar Reference (`clang -O0`)
  3. Explicit ARM64 NEON / x86 AVX2 Vector Backend (`SynaxCodeGenerator` / `AVX2Backend`)
  4. Direct SSA LLVM IR Backend (`LLVMIRBackend` -> `clang -O3 -x ir`)

Core Invariant Tested: `optimization must never change semantics`.
=============================================================================
"""

import os
import platform
import random
import sys
import tempfile
import time
from array import array
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

from synax.backends.avx2_backend import AVX2Backend
from synax.backends.llvm_ir_backend import LLVMIRBackend
from synax.interpreter import ReferenceInterpreter
from synax_ir import parse_sx
from synax_verifier import SPECIAL_VALUES_F32, LoadedKernel, check_equivalence_pure
from synaxc import SHARED_CFLAGS_O0_REF, SHARED_CFLAGS_O3, SynaxCodeGenerator, SynaxCompiler


def _random_expr(rng: random.Random, depth: int = 0) -> str:
    if depth >= 3 or (depth >= 1 and rng.random() < 0.35):
        choice = rng.choice(["a", "b", "const"])
        if choice == "const":
            c = rng.choice([-2.5, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 1.5, 3.25])
            return f"{c}"
        return choice

    kind = rng.choice(["bin", "bin", "unary", "minmax", "clamp"])
    if kind == "bin":
        op = rng.choice(["+", "-", "*"])
        lhs = _random_expr(rng, depth + 1)
        rhs = _random_expr(rng, depth + 1)
        return f"({lhs} {op} {rhs})"
    if kind == "unary":
        fn = rng.choice(["abs", "square", "relu", "sigmoid"])
        inner = _random_expr(rng, depth + 1)
        if fn == "sigmoid":
            # Clamp extreme growth inside deep random ASTs so finite tests exercise nontrivial values too
            return f"sigmoid(clamp({inner}, -20.0, 20.0))"
        return f"{fn}({inner})"
    if kind == "minmax":
        fn = rng.choice(["min", "max"])
        return f"{fn}({_random_expr(rng, depth + 1)}, {_random_expr(rng, depth + 1)})"
    lo = rng.choice([-10.0, -1.0, 0.0])
    hi = rng.choice([1.0, 5.0, 25.0])
    return f"clamp({_random_expr(rng, depth + 1)}, {lo}, {hi})"


def _random_sx_program(rng: random.Random, idx: int) -> str:
    safety_choice = rng.choice(["preserve", "heal(0.0)", "heal(0.5)", "zero_output", "reject"])
    extra_safety = []
    if rng.random() < 0.45:
        extra_safety.append("range_check = clamp(-50.0, 100.0)")
    if safety_choice != "preserve" and rng.random() < 0.4:
        extra_safety.append("input_bound = abs_max(500.0)")

    safety_lines = [f"    nonfinite = {safety_choice}"] + [f"    {s}" for s in extra_safety]
    safety_block = "\n".join(safety_lines)

    e1 = _random_expr(rng, 0)
    e2 = _random_expr(rng, 1)
    comb_op = rng.choice(["+", "-", "*"])

    return f"""synax 0.1

kernel fuzz_kernel_{idx}(
  a: tensor<f32>,
  b: tensor<f32>
) -> tensor<f32> {{
  intent "Randomized differential fuzz kernel #{idx}"
  require shape(a) == shape(b)

  safety {{
{safety_block}
  }}

  let t1 = {e1}
  let t2 = {e2}
  return ({comb_op.join(['t1', 't2'])})
}}
"""


def _random_adversarial_vectors(rng: random.Random):
    vectors = []
    for n in (0, 1, 3, 4, 8, 17, 65, 259):
        a = array("f")
        b = array("f")
        for _ in range(n):
            if rng.random() < 0.28:
                a.append(rng.choice(SPECIAL_VALUES_F32 + [499.0, 501.0, -501.0]))
            else:
                a.append(rng.uniform(-12.0, 12.0))
            if rng.random() < 0.28:
                b.append(rng.choice(SPECIAL_VALUES_F32 + [499.0, 501.0, -501.0]))
            else:
                b.append(rng.uniform(-12.0, 12.0))
        vectors.append((a, b))
    return vectors


def run_fuzz_suite(num_programs: int = 25, seed: int = 20261103):
    print("=" * 72)
    print(f"🎲 SYNAX DIFFERENTIAL AST & IEEE-754 FUZZER ({num_programs} Rastgele Çekirdek)")
    print("=" * 72)
    t0 = time.perf_counter()
    rng = random.Random(seed)
    has_clang = os.system("clang --version > /dev/null 2>&1") == 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for i in range(num_programs):
            sx_src = _random_sx_program(rng, i)
            ir = parse_sx(sx_src)
            interp = ReferenceInterpreter(ir)
            test_vecs = _random_adversarial_vectors(rng)

            if not has_clang:
                # Windows / no-Clang environments still fuzz-test AST lowering + Reference Interpreter
                for a, b in test_vecs:
                    res = interp.execute(a, b, strict_reject=False)
                    assert len(res.output) == len(a)
                continue

            # 1. C11 -O0 Scalar Reference
            ref_c = SynaxCodeGenerator.emit_scalar_variant(
                ir, pragma_line="#pragma clang loop vectorize(disable) unroll(disable)"
            )
            ok, err = SynaxCompiler._compile_dylib(
                ref_c, tmp / f"r{i}.c", tmp / f"r{i}.dylib", SHARED_CFLAGS_O0_REF
            )
            assert ok, f"Fuzz #{i} C11 -O0 derlenemedi: {err}\n{sx_src}"
            k_ref = LoadedKernel(str(tmp / f"r{i}.dylib"), name=f"ref_{i}")

            # 2. SIMD Variant (ARM64 NEON 4x on arm64, AVX2 on x86_64)
            arch = platform.machine().lower()
            if "arm64" in arch or "aarch64" in arch:
                simd_c = SynaxCodeGenerator.emit_neon_variant(ir, unroll_4x=True)
                simd_flags = SHARED_CFLAGS_O3
            else:
                simd_c = AVX2Backend.emit_c_source(ir)
                simd_flags = ["-O3", "-mavx2", "-mfma", "-shared", "-fPIC", "-std=c11"]

            ok_s, err_s = SynaxCompiler._compile_dylib(
                simd_c, tmp / f"s{i}.c", tmp / f"s{i}.dylib", simd_flags
            )
            assert ok_s, f"Fuzz #{i} SIMD derlenemedi: {err_s}\n{sx_src}"
            k_simd = LoadedKernel(str(tmp / f"s{i}.dylib"), name=f"simd_{i}")

            # 3. Direct SSA LLVM IR Variant
            ok_l, err_l = LLVMIRBackend.compile_ll_to_dylib(
                ir, tmp / f"l{i}.ll", tmp / f"l{i}.dylib"
            )
            assert ok_l, f"Fuzz #{i} LLVM IR derlenemedi: {err_l}\n{sx_src}"
            k_llvm = LoadedKernel(str(tmp / f"l{i}.dylib"), name=f"llvm_{i}")

            for a, b in test_vecs:
                i_res = interp.execute(a, b, strict_reject=False)
                r_out, r_h = k_ref.run_pure(a, b)
                s_out, s_h = k_simd.run_pure(a, b)
                l_out, l_h = k_llvm.run_pure(a, b)

                ok_ir, msg_ir, _ = check_equivalence_pure(
                    i_res.output, r_out, rtol=1e-5, ref_healed=i_res.healed_count, cand_healed=r_h
                )
                assert ok_ir, f"Fuzz #{i} Interp vs C11-O0 hatası (n={len(a)}): {msg_ir}\n{sx_src}"

                ok_rs, msg_rs, _ = check_equivalence_pure(
                    r_out, s_out, rtol=1e-5, ref_healed=r_h, cand_healed=s_h
                )
                assert ok_rs, f"Fuzz #{i} C11-O0 vs SIMD hatası (n={len(a)}): {msg_rs}\n{sx_src}"

                ok_rl, msg_rl, _ = check_equivalence_pure(
                    r_out, l_out, rtol=1e-5, ref_healed=r_h, cand_healed=l_h
                )
                assert ok_rl, f"Fuzz #{i} C11-O0 vs LLVM-IR hatası (n={len(a)}): {msg_rl}\n{sx_src}"

            if (i + 1) % 5 == 0 or i == num_programs - 1:
                print(
                    f"  ✓ Fuzz Çekirdekleri [1..{i + 1:02d}/{num_programs}] "
                    f"(Interpreter == C11-O0 == SIMD == LLVM-IR) DOĞRULANDI"
                )

    dt = time.perf_counter() - t0
    print("=" * 72)
    print(f"🎉 {num_programs} RASTGELE AST & ADVERSARIAL FUZZ TESTİ %100 GEÇTİ! ({dt:.2f} sn)")
    print("=" * 72)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    run_fuzz_suite(num_programs=count)
