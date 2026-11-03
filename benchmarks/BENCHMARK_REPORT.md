# 📊 SYNAX Reproducible Benchmark Report

- **Date (UTC):** `2026-11-03T00:46:03Z`
- **CPU / Arch:** `Apple M1` (`arm64`, `8` logical cores, SIMD `arm64_neon`)
- **Hardware Fingerprint:** `4258050f0fd7`
- **Compiler:** `Apple clang version 21.0.0 (clang-2100.4.1.1)`
- **Flags (`clang -O3`):** `-O3 -mcpu=native -shared -fPIC -std=c11 -Wall -Wno-unused-function` *(strictly no `-ffast-math`)*
- **Protocol:** Pre-allocated `float32` buffers, `N = 4,000,000` elements (`48.0 MB` stream traffic), `5` warmup runs + median & IQR of `21` warm runs. All candidates verified across 19 adversarial IEEE-754 edge suites.

| Workload | Safety | Scalar `-O1` (ms) | `clang -O3` (ms) | LLVM SSA IR (ms) | SYNAX Winner | Winner Median ± IQR (ms) | Throughput | vs `clang -O3` |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| `kapili_aktivasyon.sx` | `preserve` | `7.495` | `6.911` | `7.009` | `v4_gcd_multicore_neon` | **`1.010 ± 0.048`** | `47.5 GB/s` | **`6.84x`** |
| `biyomedikal_kardiyo.sx` | `heal_inputs` | `6.467` | `1.327` | `1.324` | `v5_llvm_ssa_ir_o3` | **`1.324 ± 0.243`** | `36.2 GB/s` | **`1.00x`** |
| `hemodynamic_cpp.sx` | `heal_inputs` | `5.476` | `1.106` | `1.156` | `v0_clang_o3_scalar` | **`1.106 ± 0.099`** | `43.4 GB/s` | **`1.00x`** |
| `normalized_difference.sx` | `reject` | `6.181` | `1.481` | `1.584` | `v2_neon_simd` | **`0.995 ± 0.068`** | `48.2 GB/s` | **`1.49x`** |
| `anomali_v04.sx` | `zero_output` | `3.935` | `0.932` | `1.050` | `v0_clang_o3_scalar` | **`0.932 ± 0.180`** | `51.5 GB/s` | **`1.00x`** |
