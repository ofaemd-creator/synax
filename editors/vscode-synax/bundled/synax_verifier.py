#!/usr/bin/env python3
"""
SYNAX DIFFERENTIAL VERIFIER, DUAL-REFERENCE GATE & BENCHMARK HARNESS
=============================================================================
Implements SYNAX's core engineering invariant:
  `optimization must never change semantics`

Capabilities:
  1. 19 Adversarial Edge-Case Suites (ported & unified from SYNAX v0.4):
     - Lengths: [0, 1, 3, 4, 5, 7, 8, 15, 16, 17, 31, 63, 1023, 4097, 100_003]
     - IEEE-754 specials: [0.0, -0.0, 1.0, -1.0, NaN, +Inf, -Inf, 1e30, -1e30,
       1e-40 (subnormal), 3.4e38, -3.4e38] + optional range-bound spikes
     - Full 12x12 = 144 Cartesian product of all special-value pairs
     - Sentinel pre-fill (`1234.5f`) to catch any unwritten output tail elements
  2. Dual-Reference Semantic Verification:
     - Offline mode: Pure-Python IEEE-754 binary32 AST Evaluator vs C11 `-O0` Scalar
     - LLM mode: Two independently synthesized C11 Scalar references
  3. Zero-Dependency Support + Optional NumPy Acceleration:
     - Runs with pure Python `array('f')` + `ctypes` everywhere; uses `numpy`
       for fast vectorized checks when available.
  4. Honest Warm-Cache Median Benchmarking:
     - Pre-allocated buffers, explicit warmup runs, median of repeated runs.
=============================================================================
"""

import ctypes
import math
import random
import statistics
import time
from array import array
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union

from synax_ir import SynaxIR

try:
    import numpy as _np
except ImportError:
    _np = None

SENTINEL_F32 = 1234.5

SPECIAL_VALUES_F32 = [
    0.0,
    -0.0,
    1.0,
    -1.0,
    float("nan"),
    float("inf"),
    float("-inf"),
    1e30,
    -1e30,
    1e-40,
    3.4e38,
    -3.4e38,
]

CANONICAL_LENGTHS = [0, 1, 3, 4, 5, 7, 8, 15, 16, 17, 31, 63, 1023, 4097, 100_003]


class DualReferenceMismatchError(RuntimeError):
    """Raised when two independent semantic references disagree on intent behavior."""


@dataclass
class VerificationReport:
    passed: bool
    suites_tested: int
    total_elements: int
    max_abs_diff: float
    failure_reason: str = ""


class LoadedKernel:
    """
    ctypes wrapper around a compiled SYNAX shared library (`.dylib` / `.so`).
    Supports both:
      - `void synax_kernel(const float* a, const float* b, float* out, size_t n)`
      - `void synax_kernel_tracked(const float* a, const float* b, float* out, size_t n, size_t* out_healed)`
    """

    def __init__(self, dylib_path: str, name: str = ""):
        self.dylib_path = str(dylib_path)
        self.name = name or self.dylib_path
        self.lib = ctypes.CDLL(self.dylib_path)

        f_ptr = ctypes.POINTER(ctypes.c_float)
        sz_ptr = ctypes.POINTER(ctypes.c_size_t)

        self._fn_basic = self.lib.synax_kernel
        self._fn_basic.argtypes = [f_ptr, f_ptr, f_ptr, ctypes.c_size_t]
        self._fn_basic.restype = None

        self._fn_tracked = None
        if hasattr(self.lib, "synax_kernel_tracked"):
            self._fn_tracked = self.lib.synax_kernel_tracked
            self._fn_tracked.argtypes = [f_ptr, f_ptr, f_ptr, ctypes.c_size_t, sz_ptr]
            self._fn_tracked.restype = None

    @property
    def has_tracked(self) -> bool:
        return self._fn_tracked is not None

    def run_pure(self, a_arr: array, b_arr: array) -> Tuple[array, Optional[int]]:
        """Execute kernel using pure Python `array('f')` with `1234.5f` sentinel pre-fill."""
        n = len(a_arr)
        out_arr = array("f", [SENTINEL_F32]) * n if n > 0 else array("f", [SENTINEL_F32])
        f_ptr = ctypes.POINTER(ctypes.c_float)

        # Even when n == 0, pass valid pointers to 1-element dummy arrays so C pointers are non-NULL,
        # and verify the dummy sentinel at index 0 is untouched!
        dummy_a = a_arr if n > 0 else array("f", [0.0])
        dummy_b = b_arr if n > 0 else array("f", [0.0])

        ptr_a = ctypes.cast(dummy_a.buffer_info()[0], f_ptr)
        ptr_b = ctypes.cast(dummy_b.buffer_info()[0], f_ptr)
        ptr_out = ctypes.cast(out_arr.buffer_info()[0], f_ptr)

        healed_val: Optional[int] = None
        if self._fn_tracked is not None:
            c_healed = ctypes.c_size_t(0)
            self._fn_tracked(ptr_a, ptr_b, ptr_out, n, ctypes.byref(c_healed))
            healed_val = int(c_healed.value)
        else:
            self._fn_basic(ptr_a, ptr_b, ptr_out, n)

        if n == 0:
            if out_arr[0] != SENTINEL_F32:
                raise AssertionError(f"Kernel '{self.name}' n=0 çağrısında sınır dışı bellek yazdı!")
            return array("f"), healed_val

        return out_arr, healed_val

    def run_numpy(self, a_np, b_np):
        """Execute kernel using NumPy float32 arrays with `1234.5f` sentinel pre-fill."""
        n = int(a_np.shape[0])
        f_ptr = ctypes.POINTER(ctypes.c_float)
        if n == 0:
            sentinel = _np.array([SENTINEL_F32], dtype=_np.float32)
            da = _np.zeros(1, dtype=_np.float32)
            db = _np.zeros(1, dtype=_np.float32)
            healed_val = None
            if self._fn_tracked is not None:
                c_healed = ctypes.c_size_t(0)
                self._fn_tracked(
                    da.ctypes.data_as(f_ptr),
                    db.ctypes.data_as(f_ptr),
                    sentinel.ctypes.data_as(f_ptr),
                    0,
                    ctypes.byref(c_healed),
                )
                healed_val = int(c_healed.value)
            else:
                self._fn_basic(
                    da.ctypes.data_as(f_ptr),
                    db.ctypes.data_as(f_ptr),
                    sentinel.ctypes.data_as(f_ptr),
                    0,
                )
            if float(sentinel[0]) != SENTINEL_F32:
                raise AssertionError(f"Kernel '{self.name}' n=0 çağrısında sınır dışı bellek yazdı!")
            return _np.empty(0, dtype=_np.float32), healed_val

        out = _np.full(n, _np.float32(SENTINEL_F32), dtype=_np.float32)
        healed_val = None
        if self._fn_tracked is not None:
            c_healed = ctypes.c_size_t(0)
            self._fn_tracked(
                a_np.ctypes.data_as(f_ptr),
                b_np.ctypes.data_as(f_ptr),
                out.ctypes.data_as(f_ptr),
                n,
                ctypes.byref(c_healed),
            )
            healed_val = int(c_healed.value)
        else:
            self._fn_basic(
                a_np.ctypes.data_as(f_ptr),
                b_np.ctypes.data_as(f_ptr),
                out.ctypes.data_as(f_ptr),
                n,
            )
        return out, healed_val


def build_adversarial_suites(
    seed: int = 7,
    input_abs_bound: Optional[float] = None,
    force_pure_python: bool = False,
) -> List[Tuple[Union[array, object], Union[array, object]]]:
    """
    Construct the 19 canonical adversarial input suites:
      - Suites 1..15 : Gaussian N(0, 10) across `CANONICAL_LENGTHS` (0 up to 100,003)
      - Suites 16..18: Mixed IEEE-754 special values (lengths 12, 37, 1000)
      - Suite 19     : Full 12x12 = 144 Cartesian product of `SPECIAL_VALUES_F32`
    If `input_abs_bound` is specified (e.g., 1000.0), threshold-straddling spikes
    are injected into Suite 18 (`n=1000`) so bound edges are tested too.
    """
    use_np = (_np is not None) and (not force_pure_python)
    suites = []

    if use_np:
        rng = _np.random.default_rng(seed)
        specials = _np.array(SPECIAL_VALUES_F32, dtype=_np.float32)
        for n in CANONICAL_LENGTHS:
            a = (rng.standard_normal(n) * 10.0).astype(_np.float32)
            b = (rng.standard_normal(n) * 10.0).astype(_np.float32)
            suites.append((a, b))
        for n in (12, 37, 1000):
            a = rng.choice(specials, n).astype(_np.float32)
            b = rng.choice(specials, n).astype(_np.float32)
            if n == 1000 and input_abs_bound is not None:
                bnd = float(input_abs_bound)
                spikes = [bnd * 0.999, -bnd * 0.999, bnd, -bnd, bnd * 1.001, -bnd * 1.001, 99999.0, -99999.0]
                for k, sv in enumerate(spikes):
                    a[k] = _np.float32(sv)
                    b[k + 16] = _np.float32(sv)
            suites.append((a, b))
        cart_a = _np.repeat(specials, len(specials)).astype(_np.float32)
        cart_b = _np.tile(specials, len(specials)).astype(_np.float32)
        suites.append((cart_a, cart_b))
    else:
        py_rng = random.Random(seed)
        for n in CANONICAL_LENGTHS:
            a = array("f", (py_rng.gauss(0.0, 10.0) for _ in range(n)))
            b = array("f", (py_rng.gauss(0.0, 10.0) for _ in range(n)))
            suites.append((a, b))
        for n in (12, 37, 1000):
            a = array("f", (py_rng.choice(SPECIAL_VALUES_F32) for _ in range(n)))
            b = array("f", (py_rng.choice(SPECIAL_VALUES_F32) for _ in range(n)))
            if n == 1000 and input_abs_bound is not None:
                bnd = float(input_abs_bound)
                spikes = [bnd * 0.999, -bnd * 0.999, bnd, -bnd, bnd * 1.001, -bnd * 1.001, 99999.0, -99999.0]
                for k, sv in enumerate(spikes):
                    a[k] = sv
                    b[k + 16] = sv
            suites.append((a, b))
        cart_a = array("f")
        cart_b = array("f")
        for x in SPECIAL_VALUES_F32:
            for y in SPECIAL_VALUES_F32:
                cart_a.append(x)
                cart_b.append(y)
        suites.append((cart_a, cart_b))

    return suites


def check_equivalence_pure(
    ref_out: Sequence[float],
    cand_out: Sequence[float],
    rtol: float = 1e-5,
    ref_healed: Optional[int] = None,
    cand_healed: Optional[int] = None,
) -> Tuple[bool, str, float]:
    """Pure-Python IEEE-754 equivalence check (NaN parity, ±Inf sign parity, 1e-5 relative tolerance)."""
    if len(ref_out) != len(cand_out):
        return False, f"uzunluk farklı ({len(ref_out)} vs {len(cand_out)})", float("inf")

    max_rel_diff = 0.0
    for i in range(len(ref_out)):
        rx = float(ref_out[i])
        cy = float(cand_out[i])
        r_nan = math.isnan(rx)
        c_nan = math.isnan(cy)
        if r_nan != c_nan:
            return False, f"NaN konumu farklı (indeks {i}: ref={rx}, aday={cy})", float("inf")
        if r_nan:
            continue
        r_inf = math.isinf(rx)
        c_inf = math.isinf(cy)
        if r_inf != c_inf:
            return False, f"Inf konumu farklı (indeks {i}: ref={rx}, aday={cy})", float("inf")
        if r_inf:
            if (rx > 0) != (cy > 0):
                return False, f"Inf işareti farklı (indeks {i}: ref={rx}, aday={cy})", float("inf")
            continue
        diff = abs(rx - cy)
        scale = max(1.0, abs(rx))
        rel = diff / scale
        if rel > max_rel_diff:
            max_rel_diff = rel
        tol = rtol * scale
        if diff > tol:
            return False, f"sayısal fark {diff:.3e} > tol {tol:.3e} (indeks {i}: ref={rx:.6g}, aday={cy:.6g})", max_rel_diff

    if ref_healed is not None and cand_healed is not None and ref_healed != cand_healed:
        return False, f"anomali sayacı farklı (ref={ref_healed}, aday={cand_healed})", max_rel_diff

    return True, "", max_rel_diff


def check_equivalence(
    ref_out,
    cand_out,
    rtol: float = 1e-5,
    ref_healed: Optional[int] = None,
    cand_healed: Optional[int] = None,
) -> Tuple[bool, str, float]:
    """Fast vectorized equivalence check using NumPy when inputs are ndarray, else pure Python."""
    if _np is not None and isinstance(ref_out, _np.ndarray) and isinstance(cand_out, _np.ndarray):
        if ref_out.shape != cand_out.shape:
            return False, f"uzunluk farklı ({ref_out.shape} vs {cand_out.shape})", float("inf")
        if ref_out.size == 0:
            if ref_healed is not None and cand_healed is not None and ref_healed != cand_healed:
                return False, f"anomali sayacı farklı (ref={ref_healed}, aday={cand_healed})", 0.0
            return True, "", 0.0

        nan_x = _np.isnan(ref_out)
        nan_y = _np.isnan(cand_out)
        if not _np.array_equal(nan_x, nan_y):
            idx = int(_np.argmax(nan_x != nan_y))
            return False, f"NaN konumu farklı (indeks {idx}: ref={ref_out[idx]}, aday={cand_out[idx]})", float("inf")

        m = ~nan_x
        inf_x = _np.isinf(ref_out[m])
        inf_y = _np.isinf(cand_out[m])
        if not _np.array_equal(inf_x, inf_y):
            return False, "Inf konumu farklı", float("inf")

        both_inf = m & _np.isinf(ref_out)
        if not _np.array_equal(ref_out[both_inf], cand_out[both_inf]):
            return False, "Inf işareti farklı", float("inf")

        finite = m & _np.isfinite(ref_out)
        max_rel_diff = 0.0
        if _np.any(finite):
            rx64 = ref_out[finite].astype(_np.float64)
            cy64 = cand_out[finite].astype(_np.float64)
            diffs = _np.abs(rx64 - cy64)
            scale = _np.maximum(1.0, _np.abs(rx64))
            max_rel_diff = float(_np.max(diffs / scale))
            tol = rtol * scale
            excess = diffs - tol
            if _np.any(excess > 0.0):
                bad_i = int(_np.argmax(excess))
                return (
                    False,
                    f"sayısal fark {diffs[bad_i]:.3e} > tol {tol[bad_i]:.3e} "
                    f"(ref={rx64[bad_i]:.6g}, aday={cy64[bad_i]:.6g})",
                    max_rel_diff,
                )

        if ref_healed is not None and cand_healed is not None and ref_healed != cand_healed:
            return False, f"anomali sayacı farklı (ref={ref_healed}, aday={cand_healed})", max_rel_diff

        return True, "", max_rel_diff

    return check_equivalence_pure(ref_out, cand_out, rtol=rtol, ref_healed=ref_healed, cand_healed=cand_healed)


def verify_against_reference(
    candidate: LoadedKernel,
    reference: LoadedKernel,
    suites: List[Tuple[object, object]],
    rtol: float = 1e-5,
    is_reduction: bool = False,
) -> VerificationReport:
    """Run all 19 adversarial test suites comparing `candidate` against `reference`."""
    overall_max_diff = 0.0
    total_elems = 0

    for idx, (a, b) in enumerate(suites):
        use_np = (_np is not None) and isinstance(a, _np.ndarray)
        n = int(a.shape[0]) if use_np else len(a)
        total_elems += n

        if use_np:
            ref_out, ref_h = reference.run_numpy(a, b)
            cand_out, cand_h = candidate.run_numpy(a, b)
            if is_reduction and n > 0:
                ref_out = ref_out[:1]
                cand_out = cand_out[:1]
        else:
            ref_out, ref_h = reference.run_pure(a, b)
            cand_out, cand_h = candidate.run_pure(a, b)
            if is_reduction and n > 0:
                ref_out = ref_out[:1]
                cand_out = cand_out[:1]

        ok, reason, mdiff = check_equivalence(
            ref_out, cand_out, rtol=rtol, ref_healed=ref_h, cand_healed=cand_h
        )
        if mdiff > overall_max_diff and math.isfinite(mdiff):
            overall_max_diff = mdiff
        if not ok:
            return VerificationReport(
                passed=False,
                suites_tested=idx + 1,
                total_elements=total_elems,
                max_abs_diff=mdiff,
                failure_reason=f"küme #{idx + 1} (n={n}): {reason}",
            )

    return VerificationReport(
        passed=True,
        suites_tested=len(suites),
        total_elements=total_elems,
        max_abs_diff=overall_max_diff,
    )


def verify_dual_reference_offline(
    ir: SynaxIR,
    c_ref_kernel: LoadedKernel,
    suites: List[Tuple[object, object]],
    rtol: float = 1e-5,
) -> VerificationReport:
    """
    Offline Dual-Reference Semantic Gate:
    Compares Independent Reference #1 (Pure-Python IEEE-754 binary32 AST Evaluator)
    against Independent Reference #2 (Compiled C11 `-O0` Scalar Kernel) across all
    small & medium adversarial suites (every length <= 1024 + all special/Cartesian suites).
    """
    max_diff = 0.0
    tested_suites = 0
    total_elems = 0

    for idx, (a, b) in enumerate(suites):
        use_np = (_np is not None) and isinstance(a, _np.ndarray)
        n = int(a.shape[0]) if use_np else len(a)
        if n > 2048:
            # Skip only the 4097 and 100,003 random Gaussian bulk arrays in pure-Python AST eval;
            # those are verified in C-vs-C across all candidates, while all 17 edge/special/Cartesian
            # suites (2,343 elements) are dual-verified against the Python IEEE-754 reference!
            continue

        tested_suites += 1
        total_elems += n

        if ir.is_reduction:
            py_out, py_healed = ir.execute_array(a, b)
        else:
            py_out = array("f")
            py_healed = 0
            for i in range(n):
                v, h = ir.eval_element_f32(float(a[i]), float(b[i]))
                py_out.append(v)
                py_healed += h

        if use_np:
            c_out_np, c_healed = c_ref_kernel.run_numpy(a, b)
            c_out = c_out_np.tolist()
        else:
            c_out_arr, c_healed = c_ref_kernel.run_pure(a, b)
            c_out = c_out_arr

        if ir.is_reduction and n > 0:
            c_out = c_out[:1]

        ok, reason, mdiff = check_equivalence_pure(
            py_out, c_out, rtol=rtol, ref_healed=py_healed, cand_healed=c_healed
        )
        if mdiff > max_diff and math.isfinite(mdiff):
            max_diff = mdiff
        if not ok:
            raise DualReferenceMismatchError(
                f"Çift-Referans Semantik Uyuşmazlığı [küme #{idx + 1}, n={n}]: {reason}"
            )

    return VerificationReport(
        passed=True,
        suites_tested=tested_suites,
        total_elements=total_elems,
        max_abs_diff=max_diff,
    )


def benchmark_kernel(
    kernel: LoadedKernel,
    n: int = 4_000_000,
    repeats: int = 15,
    warmup: int = 3,
) -> float:
    """
    Fair warm-cache median benchmark (returns median execution time in milliseconds).
    Buffers are allocated ONCE outside the timed region so Python/NumPy memory
    allocation never inflates or compresses native kernel latency.
    """
    f_ptr = ctypes.POINTER(ctypes.c_float)
    fn = kernel._fn_basic

    if _np is not None:
        rng = _np.random.default_rng(1)
        a = rng.standard_normal(n, dtype=_np.float32)
        b = rng.standard_normal(n, dtype=_np.float32)
        out = _np.empty(max(1, n), dtype=_np.float32)
        pa = a.ctypes.data_as(f_ptr)
        pb = b.ctypes.data_as(f_ptr)
        pout = out.ctypes.data_as(f_ptr)
    else:
        py_rng = random.Random(1)
        block = [py_rng.gauss(0.0, 1.0) for _ in range(min(n, 4096) or 1)]
        repeats_blk = (n // len(block)) + 1
        a = array("f", (block * repeats_blk)[:n])
        b = array("f", (block[::-1] * repeats_blk)[:n])
        out = array("f", [0.0]) * max(1, n)
        pa = ctypes.cast(a.buffer_info()[0], f_ptr)
        pb = ctypes.cast(b.buffer_info()[0], f_ptr)
        pout = ctypes.cast(out.buffer_info()[0], f_ptr)

    for _ in range(max(1, warmup)):
        fn(pa, pb, pout, n)

    times_ms: List[float] = []
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter_ns()
        fn(pa, pb, pout, n)
        t1 = time.perf_counter_ns()
        times_ms.append((t1 - t0) / 1e6)

    return float(statistics.median(times_ms))
