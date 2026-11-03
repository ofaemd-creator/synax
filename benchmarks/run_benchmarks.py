#!/usr/bin/env python3
"""
SYNAX REPRODUCIBLE BENCHMARK SUITE (benchmarks/run_benchmarks.py)
=============================================================================
Executes controlled, warm-cache reproducible benchmarks across the canonical
`.sx` workload suite, recording:
  - Deterministic Hardware Fingerprint (`detect_hardware_fingerprint()`)
  - Exact compiler flags (zero `-ffast-math` semantic violations)
  - Median, IQR (p25..p75), Min latency (ms), and Memory Bandwidth (GB/s)
  - Comparisons across C11 Scalar (`-O1`), `clang -O3`, LLVM SSA IR (`-O3`),
    ARM64 NEON / x86 AVX2 SIMD, and Multicore GCD.
Writes machine-readable `benchmarks/latest_results.json` and human-readable
`benchmarks/BENCHMARK_REPORT.md`.
=============================================================================
"""

import ctypes
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

from synax.backends.llvm_ir_backend import LLVMIRBackend
from synax.hardware import detect_hardware_fingerprint, fingerprint_to_dict
from synax_verifier import LoadedKernel, build_adversarial_suites, verify_against_reference
from synaxc import SHARED_CFLAGS_O1_SCALAR, SHARED_CFLAGS_O3, SynaxCodeGenerator, SynaxCompiler


def _measure_stats_ms(kernel: LoadedKernel, a: np.ndarray, b: np.ndarray, out: np.ndarray, runs: int = 21, warmup: int = 5) -> Dict[str, float]:
    f_ptr = ctypes.POINTER(ctypes.c_float)
    pa = a.ctypes.data_as(f_ptr)
    pb = b.ctypes.data_as(f_ptr)
    pout = out.ctypes.data_as(f_ptr)
    n = int(a.shape[0])
    fn = kernel._fn_basic

    for _ in range(warmup):
        fn(pa, pb, pout, n)

    samples: List[float] = []
    for _ in range(runs):
        t0 = time.perf_counter_ns()
        fn(pa, pb, pout, n)
        t1 = time.perf_counter_ns()
        samples.append((t1 - t0) / 1e6)

    samples.sort()
    q25 = samples[len(samples) // 4]
    q75 = samples[(3 * len(samples)) // 4]
    med = float(statistics.median(samples))
    # 2 float32 reads + 1 float32 write = 12 bytes per element
    gbps = (n * 12.0) / (med * 1e-3) / 1e9
    return {
        "median_ms": round(med, 4),
        "iqr_ms": round(q75 - q25, 4),
        "p25_ms": round(q25, 4),
        "p75_ms": round(q75, 4),
        "min_ms": round(samples[0], 4),
        "effective_gbps": round(gbps, 2),
    }


def run_reproducible_benchmarks(n: int = 4_000_000, runs: int = 21) -> Dict:
    hw = detect_hardware_fingerprint()
    rng = np.random.default_rng(42)
    a = rng.standard_normal(n, dtype=np.float32)
    b = rng.standard_normal(n, dtype=np.float32)
    out = np.empty(n, dtype=np.float32)

    workloads = [
        "kapili_aktivasyon.sx",
        "biyomedikal_kardiyo.sx",
        "hemodynamic_cpp.sx",
        "normalized_difference.sx",
        "anomali_v04.sx",
    ]

    results = []
    print("=" * 78)
    print(f"📊 SYNAX REPRODUCIBLE BENCHMARK SUITE (N={n:,} float32, {runs} Warm Runs)")
    print(f"   Hardware: {hw.cpu_brand} ({hw.machine_arch} / {hw.simd_isa}) [FP #{hw.fingerprint_id}]")
    print("=" * 78)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        comp = SynaxCompiler(cache_root=tmp / "cache")

        for wf in workloads:
            sx_path = str(ROOT_DIR / "examples" / wf)
            c_res = comp.compile(sx_path, force_rebuild=True, bench_n=65536, bench_repeats=3, verbose=False)
            ir = c_res.ir
            suites = build_adversarial_suites(input_abs_bound=ir.safety.input_abs_bound)
            ref_k = LoadedKernel(str(c_res.ref_dylib_path), name="ref_o0")

            # Also compile LLVM SSA IR candidate and verify across 19 suites
            ll_dylib = tmp / f"{ir.name}_llvm.dylib"
            ok_ll, _ = LLVMIRBackend.compile_ll_to_dylib(ir, tmp / f"{ir.name}.ll", ll_dylib)
            llvm_stats = None
            if ok_ll:
                ll_k = LoadedKernel(str(ll_dylib), name="llvm_ssa_ir")
                if verify_against_reference(ll_k, ref_k, suites).passed:
                    llvm_stats = _measure_stats_ms(ll_k, a, b, out, runs=runs)

            base_o1_k = LoadedKernel(str(c_res.baseline_o1_dylib_path), name="scalar_o1")
            o1_stats = _measure_stats_ms(base_o1_k, a, b, out, runs=runs)

            variant_stats: Dict[str, Dict] = {}
            for cand in c_res.candidates:
                if cand.verified and cand.dylib_path:
                    ck = LoadedKernel(cand.dylib_path, name=cand.name)
                    variant_stats[cand.name] = _measure_stats_ms(ck, a, b, out, runs=runs)

            if llvm_stats:
                variant_stats["v5_llvm_ssa_ir_o3"] = llvm_stats

            best_name = min(variant_stats, key=lambda k: variant_stats[k]["median_ms"])
            best_med = variant_stats[best_name]["median_ms"]
            o3_med = variant_stats["v0_clang_o3_scalar"]["median_ms"]
            o1_med = o1_stats["median_ms"]

            entry = {
                "workload": wf,
                "kernel_name": ir.name,
                "ir_hash": ir.ir_hash,
                "formula": ir.expr.to_human_formula(*ir.param_names),
                "safety_mode": ir.safety.nonfinite_mode,
                "scalar_o1": o1_stats,
                "clang_o3": variant_stats["v0_clang_o3_scalar"],
                "variants": variant_stats,
                "winner": best_name,
                "winner_stats": variant_stats[best_name],
                "speedup_vs_scalar_o1": round(o1_med / best_med, 3),
                "speedup_vs_clang_o3": round(o3_med / best_med, 3),
            }
            results.append(entry)
            print(
                f"  • {wf:<26} | O1: {o1_med:6.3f} ms | clang -O3: {o3_med:6.3f} ms | "
                f"Winner ({best_name}): {best_med:6.3f} ms (±{variant_stats[best_name]['iqr_ms']:.3f} IQR) "
                f"=> {o3_med / best_med:.2f}x vs O3 | {variant_stats[best_name]['effective_gbps']:.1f} GB/s"
            )

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_elements": n,
        "warm_runs": runs,
        "cflags_o3": " ".join(SHARED_CFLAGS_O3),
        "cflags_scalar_o1": " ".join(SHARED_CFLAGS_O1_SCALAR),
        "hardware": fingerprint_to_dict(hw),
        "results": results,
    }

    bench_dir = ROOT_DIR / "benchmarks"
    bench_dir.mkdir(exist_ok=True)
    (bench_dir / "latest_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# 📊 SYNAX Reproducible Benchmark Report",
        "",
        f"- **Date (UTC):** `{payload['timestamp']}`",
        f"- **CPU / Arch:** `{hw.cpu_brand}` (`{hw.machine_arch}`, `{hw.logical_cores}` logical cores, SIMD `{hw.simd_isa}`)",
        f"- **Hardware Fingerprint:** `{hw.fingerprint_id}`",
        f"- **Compiler:** `{hw.compiler_id}`",
        f"- **Flags (`clang -O3`):** `{payload['cflags_o3']}` *(strictly no `-ffast-math`)*",
        f"- **Protocol:** Pre-allocated `float32` buffers, `N = {n:,}` elements (`{(n * 12) / 1e6:.1f} MB` stream traffic), `5` warmup runs + median & IQR of `{runs}` warm runs. All candidates verified across 19 adversarial IEEE-754 edge suites.",
        "",
        "| Workload | Safety | Scalar `-O1` (ms) | `clang -O3` (ms) | LLVM SSA IR (ms) | SYNAX Winner | Winner Median ± IQR (ms) | Throughput | vs `clang -O3` |",
        "| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |",
    ]
    for r in results:
        ll_ms = r["variants"].get("v5_llvm_ssa_ir_o3", {}).get("median_ms")
        ll_str = f"`{ll_ms:.3f}`" if ll_ms is not None else "—"
        ws = r["winner_stats"]
        md_lines.append(
            f"| `{r['workload']}` | `{r['safety_mode']}` | `{r['scalar_o1']['median_ms']:.3f}` | "
            f"`{r['clang_o3']['median_ms']:.3f}` | {ll_str} | `{r['winner']}` | "
            f"**`{ws['median_ms']:.3f} ± {ws['iqr_ms']:.3f}`** | `{ws['effective_gbps']:.1f} GB/s` | "
            f"**`{r['speedup_vs_clang_o3']:.2f}x`** |"
        )

    (bench_dir / "BENCHMARK_REPORT.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print("=" * 78)
    print(f"✓ Saved: {bench_dir / 'latest_results.json'} & {bench_dir / 'BENCHMARK_REPORT.md'}")
    return payload


if __name__ == "__main__":
    n_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 4_000_000
    run_reproducible_benchmarks(n=n_arg)
