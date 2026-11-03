## Summary

<!-- Briefly describe what this pull request changes, why it is needed, and which architectural layer(s) it touches (SYNAPSE / IMMUNE / AXON / TYCON / MYELIN / SDK / Docs). -->

## Core Engineering Principle Check

> **SYNAX Invariant:** `optimization must never change semantics`

- [ ] **Zero `-ffast-math` / Unsafe FP Violations:** No compiler flags (`-ffast-math`, `-ffinite-math-only`, `-funsafe-math-optimizations`) or bit-shortcuts alter IEEE-754 `NaN`, `±Inf`, `±0.0`, or subnormal (`1e-40`) behavior relative to the C11 `-O0` and Python binary32 reference semantics.
- [ ] **19-Suite Differential Verification Passed:** All candidate kernels pass all 19 adversarial verification suites (`n=0..100,003`, `NaN`, `±Inf`, `±0.0`, `1e-40`, `±3.4e38`, `12x12` special-value Cartesian pairs, `1234.5f` tail-sentinel protection, and exact anomaly-heal counter parity).
- [ ] **Local Regression Suites Executed:**
  - [ ] `./synax test`
  - [ ] `python3 test_differential_myelin.py`
  - [ ] `python3 test_unified_compiler.py`
  - [ ] `python3 tests/test_lexer_parser_types.py`
  - [ ] `python3 tests/test_fuzz_differential.py`

## Honest Benchmark Disclosure (Required for Compiler / Runtime / SIMD Changes)

<!-- If this PR modifies codegen, SIMD intrinsics, or runtime hot-paths, disclose reproducible warm-cache median timings below. Never compare cold-cache interpreter runs against warm SIMD loops, and always include a fair `clang -O3` baseline. Write "N/A" if non-performance PR. -->

- **CPU / OS / Compiler:** <!-- e.g., Apple M1 (8C), macOS 15, Apple Clang 21.0 -->
- **Vector Length (`N`) & Warm Repeats:** <!-- e.g., N = 4,000,000 float32, median of 15 warm-cache runs -->
- **Scalar Reference (`-O1 -fno-vectorize`) Median:** <!-- e.g., 6.18 ms -->
- **`clang -O3 -mcpu=native` Baseline Median:** <!-- e.g., 1.70 ms -->
- **SYNAX Verified Winner Median & Speedup vs `-O3`:** <!-- e.g., 1.30 ms (1.31x) -->

## Security, Licensing & Medical Research Boundary

- [ ] **Zero-Trust Security Intact:** `SynaxSecurityGuard` expression/module checks, `0700` cache directory isolation, and SHA-256 JSON integrity verification remain enforced.
- [ ] **Apache-2.0 Compliance:** All contributed code is original or compatible with [Apache License 2.0](../LICENSE).
- [ ] **Non-Clinical Research Boundary:** Any biomedical signal examples or PhysioNet analysis strictly adhere to [`MEDICAL_RESEARCH_DISCLAIMER.md`](../MEDICAL_RESEARCH_DISCLAIMER.md) (no clinical/diagnostic/AED device claims).
