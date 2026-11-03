# ⚡ SYNAX (`.sx`) — Neuro-Symbolic Kernel Language, Differential Verifier & Adaptive Myelin Runtime

[![CI](https://img.shields.io/github/actions/workflow/status/ofaemd-creator/synax/ci.yml?branch=main&style=for-the-badge&label=Cross-Platform_CI)](https://github.com/ofaemd-creator/synax/actions)
[![Platform](https://img.shields.io/badge/Platform-synaxcode.com-10b981?style=for-the-badge)](https://synaxcode.com)
[![Whitepaper](https://img.shields.io/badge/Spec_&_Docs-synaxcode.org-06b6d4?style=for-the-badge)](https://synaxcode.org)
[![Cloud IDE](https://img.shields.io/badge/Cloud_Studio-synaxcode.online-a855f7?style=for-the-badge)](https://synaxcode.online)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)

> **Core Engineering Invariant:** `optimization must never change semantics`  
> **"Ne yapmak istediğinizi semantik olarak tanımlayın; sistem bunu doğrulasın, çalıştığı donanıma göre varyantlar üretsin, ölçsün ve en iyisini hatırlasın."**

**SYNAX (`.sx`)** is an open-source **neuro-symbolic kernel language, differential verification compiler (`synaxc`), and adaptive runtime (`libsynax_myelin`)**. Inspired by biological saltatory conduction across Ranvier nodes, SYNAX lowers `.sx` programs into a canonical IEEE-754 Intermediate Representation (`SynaxIR`), enforces static type & tensor-shape constraints, synthesizes multi-target native code (**C11 Scalar**, **ARM64 NEON**, **x86_64 AVX2+FMA**, **Apple GCD Multicore**, and direct **SSA LLVM IR**), eliminates any candidate that deviates across **19 adversarial IEEE-754 test suites**, and hot-swaps live `SynaxAxonChannel` function pointers in `O(1)`.

---

## 🏗️ 8-Layer Platform Architecture (`v0.5.0`)

| Layer | Subsystem | Repository Implementation |
| :--- | :--- | :--- |
| **1. Language & Spec** | ISO-14977 EBNF grammar, Lexer, Typed AST Parser, Static `TypeChecker` | [`spec/synax.ebnf`](spec/synax.ebnf), [`spec/LANGUAGE_SPEC.md`](spec/LANGUAGE_SPEC.md), [`src/synax/lexer.py`](src/synax/lexer.py), [`src/synax/parser.py`](src/synax/parser.py), [`src/synax/type_system.py`](src/synax/type_system.py) |
| **2. Compiler & Runtime** | IEEE-754 `ReferenceInterpreter`, C11, ARM64 NEON, x86_64 AVX2+FMA, SSA LLVM IR (`.ll`), `.sx.lock` Semantic Lock | [`synaxc.py`](synaxc.py), [`src/synax/interpreter.py`](src/synax/interpreter.py), [`src/synax/backends/`](src/synax/backends/), [`src/synax/semantic_lock.py`](src/synax/semantic_lock.py), [`synax_myelin_engine.c`](synax_myelin_engine.c) |
| **3. TYCON / MYELIN** | Multi-variant synthesis, warm-cache median benchmark, `hw_fingerprint`, SHA-256 signed persistent cache | [`src/synax/hardware.py`](src/synax/hardware.py), [`src/synax/myelin_store.py`](src/synax/myelin_store.py), [`synax_verifier.py`](synax_verifier.py) |
| **4. Multi-Language SDKs** | `pip install synax` (zero-dep PEP 517/660), Python API (`import synax`), C11 ABI (`synax.h`), C++17 RAII (`synax.hpp`), Rust FFI (`synax-rs`) | [`pyproject.toml`](pyproject.toml), [`src/synax/sdk.py`](src/synax/sdk.py), [`include/synax.h`](include/synax.h), [`include/synax.hpp`](include/synax.hpp), [`bindings/rust/`](bindings/rust/) |
| **5. Verification & Fuzzing** | Unit, C11/C++17 FFI, 19-suite differential, randomized AST/IEEE-754 fuzzer, reproducible benchmarks, macOS/Linux/Windows CI | [`tests/`](tests/), [`test_unified_compiler.py`](test_unified_compiler.py), [`benchmarks/run_benchmarks.py`](benchmarks/run_benchmarks.py), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| **6. Developer Tooling** | Unified CLI (`fmt`, `inspect`, `lock`, `debug`, `profile`, `studio`), Cloud Studio IDE, VS Code extension | [`synax_cli.py`](synax_cli.py), [`src/synax/formatter.py`](src/synax/formatter.py), [`src/synax/profiler_debugger.py`](src/synax/profiler_debugger.py), [`editors/vscode-synax/`](editors/vscode-synax/) |
| **7. Distribution & Releases** | Automated GitHub Releases + PyPI wheel/sdist + SHA-256 verified installer & updater | [`.github/workflows/release.yml`](.github/workflows/release.yml), [`scripts/install.sh`](scripts/install.sh), [`src/synax/updater.py`](src/synax/updater.py) |
| **8. Governance & Legal** | Apache-2.0 License, Trademarks, Security Policy, Governance, Roadmap, CFF Citation, Medical Disclaimer | [`LICENSE`](LICENSE), [`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md), [`GOVERNANCE.md`](GOVERNANCE.md), [`ROADMAP.md`](ROADMAP.md), [`CITATION.cff`](CITATION.cff), [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md) |

---

## 🚀 Quick Install & Usage

### 1. Python SDK & CLI (`pip install`)
```bash
pip install git+https://github.com/ofaemd-creator/synax.git
# Or inside a local clone (100% offline zero-dependency PEP 517/660 build):
pip install -e .
```

```python
import synax

ir = synax.check("examples/hemodynamic_cpp.sx")
out, healed = synax.eval_sx("examples/hemodynamic_cpp.sx", [90.0, float("nan")], [10.0, 12.0])
print(out, healed)  # array('f', [80.0, -12.0]), healed=1
```

### 2. Developer CLI (`synax`)
```bash
# Static type-check, canonical IR & Dual-Reference IEEE-754 verification:
./synax check examples/hemodynamic_cpp.sx

# Format .sx canonically & generate 32-vector SHA-256 Semantic Lock (.sx.lock):
./synax fmt --write examples/hemodynamic_cpp.sx
./synax lock examples/hemodynamic_cpp.sx
./synax verify-lock examples/hemodynamic_cpp.sx --native

# Inspect lowered SSA LLVM IR (.ll), ARM64 NEON, or x86_64 AVX2:
./synax inspect examples/kapili_aktivasyon.sx --llvm
./synax inspect examples/kapili_aktivasyon.sx --avx2

# Step-by-step IEEE-754 hex AST debugger & warm-cache Roofline profiler:
./synax debug examples/hemodynamic_cpp.sx --corrupt --b 12.5
./synax profile examples/kapili_aktivasyon.sx

# Run all 5 test suites (Unit, C/C++17 SDK, Differential, Compiler, Fuzzer):
./synax test
```

---

## 📊 Reproducible Benchmarks (Apple Silicon M1, Clang 17, `N = 4,000,000` `float32`)

Measured under warm-cache conditions (21 timed runs, pre-allocated buffers, zero `-ffast-math`, 19/19 IEEE-754 edge suites verified — see [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md)):

| `.sx` Workload | Safety Policy | Scalar C11 (`-O1`) | `clang -O3` | Verified Winner | Median ± IQR | Throughput | vs `clang -O3` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `kapili_aktivasyon.sx` (`sigmoid(a)*b`) | `preserve` | `7.92 ms` | `6.91 ms` | `v4_gcd_multicore_neon` | **`1.01 ± 0.08 ms`** | **`47.5 GB/s`** | **`6.84x`** (`2.05x` 1C NEON) |
| `biyomedikal_kardiyo.sx` (`sqrt(Δ²+ε)+0.5(a+b)`) | `heal_inputs (±1000)` | `6.18 ms` | `1.70 ms` | `v4_gcd_multicore_neon` | **`1.30 ± 0.05 ms`** | **`36.9 GB/s`** | **`1.31x`** |
| `hemodynamic_cpp.sx` (`clamp(dbp - cvp)`) | `heal_inputs + clamp` | `5.30 ms` | `1.05 ms` | `v2_neon_simd` | **`0.97 ± 0.02 ms`** | **`49.5 GB/s`** | **`1.09x`** |
| `anomali_v04.sx` (`(a-b)² + 0.5`) | `zero_output` | `3.61 ms` | `0.93 ms` | `v3_neon_4acc_prefetch` | **`0.93 ± 0.01 ms`** | **`51.5 GB/s`** | **`1.00x`** (DRAM limit) |

---

## ⚖️ License, Governance & Medical Research Disclaimer

- **License:** Open source under the [Apache License, Version 2.0](LICENSE) ([NOTICE](NOTICE), [LICENSING.md](LICENSING.md)).
- **Trademarks:** `SYNAX`, `SYNAXCODE`, and official marks are governed by [TRADEMARKS.md](TRADEMARKS.md).
- **Governance & Security:** See [GOVERNANCE.md](GOVERNANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md).
- **Medical Research Disclaimer:** SYNAX is **experimental academic/computational research software** and is **NOT** a certified medical device (EU MDR 2017/745, FDA 21 CFR, IEC 60601-2-4). Never use for clinical diagnosis, patient monitoring, or defibrillation decisions. See [MEDICAL_RESEARCH_DISCLAIMER.md](MEDICAL_RESEARCH_DISCLAIMER.md).

---

## 🌐 Official Ecosystem

- **Platform:** https://synaxcode.com
- **Specification & Docs:** https://synaxcode.org | [Formal EBNF](spec/synax.ebnf) | [Language Spec](spec/LANGUAGE_SPEC.md)
- **Cloud Studio IDE:** https://synaxcode.online
- **GitHub Repository:** https://github.com/ofaemd-creator/synax
- **Contact:** `dev@synaxcode.com` | `ofaemd@gmail.com`
