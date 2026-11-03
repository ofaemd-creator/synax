# Contributing to SYNAX (`.sx`)

Thank you for your interest in contributing to **SYNAX**! We welcome compiler engineers, SIMD/systems programmers, formal verification researchers, and biomedical signal processing scientists.

---

## 1. Core Engineering Principle

Every line of code in SYNAX is governed by one non-negotiable invariant:

> **`optimization must never change semantics`**

1. **Zero `-ffast-math` Shortcuts:** Never enable `-ffast-math`, `-ffinite-math-only`, or `-funsafe-math-optimizations` in candidate kernel compilation. Optimizations must preserve IEEE-754 `NaN`, `±Inf`, signed zero (`±0.0`), and subnormal (`1e-40`) behavior as specified by the kernel's `safety` policy (`preserve`, `heal_inputs`, `zero_output`, `reject`).
2. **19-Suite Differential Elimination:** Every new codegen variant, SIMD intrinsic (ARM64 NEON, x86 AVX2/AVX-512), or multicore pass must pass all **19 adversarial verification suites** (`n=0..100,003`, `NaN`, `±Inf`, `±0.0`, `1e-40`, `±3.4e38`, `12x12=144` special-value Cartesian pairs, `1234.5f` tail-sentinel checks, and exact anomaly-heal counter parity).
3. **Channel Parity:** Dual-channel kernels must apply identical IEEE-754 validation to both Channel A and Channel B across scalar loops, SIMD main loops, and unaligned vector tails.

---

## 2. Development Setup & Running Tests

### Prerequisites
- Python `>= 3.10` (`3.12` recommended)
- `clang` / `clang++` with C11 and C++17 support (Apple Clang on macOS, LLVM Clang on Linux)

### Build Native Runtime & Editable Python Package
```bash
# macOS (ARM64 NEON / x86_64)
clang -O3 -shared -fPIC -std=c11 synax_myelin_engine.c -lm -ldl -o libsynax_myelin.dylib

# Linux (x86_64 / AArch64)
clang -O3 -mavx2 -mfma -shared -fPIC -std=c11 synax_myelin_engine.c -lm -ldl -o libsynax_myelin.so

# Editable Python install
python3 -m pip install -e .
```

### Required Verification Commands Before Submitting a PR
Run the unified test suite and ensure **100% pass rate**:

```bash
# Unified CLI regression & differential test runner
./synax test

# Individual verification suites
python3 test_differential_myelin.py
python3 test_unified_compiler.py
python3 tests/test_lexer_parser_types.py
python3 tests/test_fuzz_differential.py
```

If you touch `editors/vscode-synax/`, validate all JSON manifests:
```bash
python3 -m json.tool editors/vscode-synax/package.json > /dev/null
python3 -m json.tool editors/vscode-synax/language-configuration.json > /dev/null
python3 -m json.tool editors/vscode-synax/syntaxes/synax.tmLanguage.json > /dev/null
python3 -m json.tool editors/vscode-synax/snippets/synax.code-snippets > /dev/null
```

---

## 3. Honest Benchmarking Rules

SYNAX maintains a culture of strict empirical honesty:
- **Warm-Cache Median Only:** Pre-allocate input/output buffers, execute warm-up iterations, and report the **median** of multiple warm runs (e.g., 15–201 repeats). Never compare cold-cache interpreter or JIT compilation overhead against warm native loops.
- **Fair Compiler Baselines:** Always compare SYNAX candidate kernels against `clang -O3 -mcpu=native` compiled on the exact same machine and vector length (`N`).
- **Disclose Hardware & Bandwidth Ceilings:** State exact CPU model, OS, compiler version, `N`, and whether a kernel is compute-bound (e.g., transcendental `sigmoid`/`exp`) or DRAM bandwidth-bound (e.g., simple `a - b` at `N = 4,000,000`).

---

## 4. Pull Request Workflow

1. Fork the repository and create a focused feature branch (`feat/...`, `fix/...`, `docs/...`).
2. Add regression tests covering both normal execution and adversarial IEEE-754 edge cases.
3. Complete every item in [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md).
4. Ensure all Biomedical / PhysioNet contributions strictly comply with [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md) (retrospective research terminology only; zero clinical device or diagnostic claims).

---

## 5. Licensing

By submitting a contribution to SYNAX, you agree that your contribution is licensed under the **[Apache License, Version 2.0](LICENSE)** (pursuant to Section 5 of the License). No separate CLA is required. Please also abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
