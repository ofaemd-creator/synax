# SYNAX (`.sx`) Architecture & Engineering Roadmap

**Lead Architect:** Dr. Ömer Faruk Aydın  
**License:** Apache License 2.0  
**Guiding Invariant:** `optimization must never change semantics`

---

## 1. The 8-Layer Institutional Architecture

SYNAX is organized into eight modular, independently verifiable engineering layers:

| Layer | Subsystem | Key Artifacts | Status |
| :--- | :--- | :--- | :--- |
| **Layer 1** | **Formal `.sx` Language & Static Frontend** | Formal EBNF/PEG specification, deterministic Lexer, Recursive-Descent AST Parser, Static Typechecker (`tensor<f32>`, shape & safety contracts), dual `synax 0.1` + `niyet:/kural:` support | **Active (`v0.5`)** |
| **Layer 2** | **Canonical `SynaxIR` & Zero-Trust Firewall** | Alpha-invariant canonical IR hashing (`synax_ir.py`), explicit IEEE-754 `SafetyPolicy` (`preserve`, `heal_inputs`, `zero_output`, `reject`), `SynaxSecurityGuard` expression/module firewall (`synax_security.py`) | **Complete (`v0.5`)** |
| **Layer 3** | **Dual-Reference Gate & 19-Suite Verifier** | Python IEEE-754 binary32 AST == C11 `-O0` Scalar check (`synax_verifier.py`), 19 adversarial suites (`n=0..100,003`, `NaN`, `±Inf`, `±0.0`, `1e-40`, `±3.4e38`, 144 Cartesian pairs, `1234.5f` tail sentinel, exact heal counts) | **Complete (`v0.5`)** |
| **Layer 4** | **Multi-Variant Codegen (`synaxc`) & Native SDKs** | C11 Scalar, 4x Unrolled, ARM64 NEON (`float32x4_t`), 4-Accumulator Prefetch NEON, Apple GCD Multicore (`synaxc.py`); Public C11 (`include/synax.h`), C++17 (`include/synax.hpp`), and Rust (`bindings/rust/`) SDKs | **Complete (`v0.5`)** |
| **Layer 5** | **Adaptive Myelin Runtime & Signed Cache** | Native `libsynax_myelin` (`synax_myelin_engine.c`), `0700` isolated `~/.cache/synax/hafiza/<ir_hash>/`, SHA-256 signed `rapor.json` & `.sx.lock`, O(1) `SynaxAxonChannel` function-pointer hot-swap | **Complete (`v0.5`)** |
| **Layer 6** | **Developer Tooling, Python Package & IDE** | Installable Python SDK (`pip install synax`), unified `synax` CLI, Cloud Studio IDE (`synaxcode.online`), and VS Code Extension (`editors/vscode-synax/`) | **Complete (`v0.5`)** |
| **Layer 7** | **Cross-Platform CI, Fuzzing & Releases** | GitHub Actions matrix (`macos-latest` ARM64 NEON, `ubuntu-latest` x86_64 Clang+AVX2, `windows-latest` Python 3.12), differential fuzz testing, automated `SHA256SUMS.txt` & PyPI release pipeline | **Complete (`v0.5`)** |
| **Layer 8** | **Open Governance & Academic Research** | Apache-2.0 legal stack (`LICENSE`, `NOTICE`, `TRADEMARKS.md`, `GOVERNANCE.md`, `CITATION.cff`), `MEDICAL_RESEARCH_DISCLAIMER.md`, and retrospective PhysioNet research benchmarks | **Active (`v0.5` -> `v1.0`)** |

---

## 2. Milestone Matrix (`v0.5` -> `v0.6` -> `v1.0`)

### Milestone `v0.5.0` — Unified Verified Compiler & Institutional Foundation (Completed)
- [x] Fix Channel B IEEE-754 SIMD sanitization & exact anomaly-heal counter parity (`0.00e+00` max diff).
- [x] Unify `v0.4` dual-reference 19-suite verifier with `v0.5` ARM64 NEON & Apple GCD Myelin engine (`synaxc`).
- [x] Establish honest warm-cache median benchmarking against `clang -O3 -mcpu=native` (up to `6.48x` verified speedup on `kapili_aktivasyon.sx`).
- [x] Ship standalone C11 (`include/synax.h`), C++17 (`include/synax.hpp`), and Rust (`synax-rs`) FFI SDKs.
- [x] Ship VS Code language support (`editors/vscode-synax`), cross-platform CI/Release workflows, and Apache-2.0 governance suite.

### Milestone `v0.6.0` — Multi-Architecture SIMD Parity, Reductions & LSP (Next)
- [ ] **Explicit x86_64 AVX2 / AVX-512 Intrinsics Backend:** Bring explicit bitwise IEEE-754 Immune Shield intrinsics (`__m256` / `__m512`) and Cody-Waite `expf`/`sigmoid` parity to Linux/Windows x86_64 targets under the same 19-suite gate.
- [ ] **Multi-Input DAGs, Sliding Windows & Reductions:** Extend `.sx` kernels beyond binary elementwise maps to support deterministic pairwise/tree reductions (`sum`, `mean`, `l2_norm`), sliding-window filters, and multi-parameter (`3+` tensor/scalar) signatures.
- [ ] **Neuro-Symbolic Construct Lowering:** Formalize higher-level `.sx` constructs (`neuron`, `pulse`, `channel`, `immune`, `myelin`) in the PEG/recursive-descent grammar with full static type inference.
- [ ] **Language Server Protocol (`synax-lsp`):** Real-time inline diagnostics, hover IR formula preview, and safety-policy lints inside `editors/vscode-synax`.
- [ ] **Reproducible `.sx.lock` CLI Commands:** `synax lock` and `synax verify-cache` for hermetic CI deployments.

### Biomedical Research Track — Retrospective PhysioNet VF/VT Benchmark (`v0.6` – `v0.8`)
> **Non-Clinical Boundary:** Governed strictly by [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md). Purely offline, retrospective computational research on public archival waveforms; **never** a clinical or AED medical device.

- [ ] **Open Dataset Ingestion & Reproducible Split Pipeline:** Offline loaders and patient-stratified evaluation harnesses for open **PhysioNet** repositories:
  - *Creighton University Ventricular Tachyarrhythmia Database (`CUDB`)*
  - *MIT-BIH Malignant Ventricular Ectopy Database (`VFDB`)*
  - *MIT-BIH Arrhythmia Database (`MITDB`)*
- [ ] **Verified `.sx` Signal Feature Kernels:** Implement differentially verified `.sx` kernels for band-pass preconditioning, electrode-dropout/artifact rejection (`IMMUNE`), spectral energy leakage, and time-domain ventricular fibrillation (VF) candidate features (`SHOCKABLE_CANDIDATE` vs `NON_SHOCKABLE_CANDIDATE` / `INDETERMINATE` research labels).
- [ ] **AHA Research Target Evaluation & Preprint:** Report sensitivity, specificity, false-positive rate under simulated motion/dropout artifacts, and deterministic SIMD execution latency in an open-access reproducible technical manuscript.

### Milestone `v1.0.0` — Language & ABI 1.0 LTS
- [ ] Freeze `.sx` Language Specification `1.0` and `SYNAX_ABI_VERSION 1` long-term binary compatibility guarantee.
- [ ] Verified **Tier-0 Bare-Metal `Q16.16` Fixed-Point C99 Backend** with bounded quantization-error certificates for embedded MCUs (`ARM Cortex-M` / `RISC-V`).
- [ ] Differentially verified **GPU Compute Backend** (Apple Metal / Vulkan Compute) subject to the same strict non-finite and boundary-suite elimination gate.
- [ ] Official VS Code Marketplace & crates.io / PyPI `1.0.0` stable releases.
