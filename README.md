# ⚡ SYNAX (`.sx`) — Neuro-Symbolic Language & Biologically-Inspired Adaptive Engine

[![Platform](https://img.shields.io/badge/Platform-synaxcode.com-10b981?style=for-the-badge)](https://synaxcode.com)
[![Whitepaper](https://img.shields.io/badge/Whitepaper-synaxcode.org-06b6d4?style=for-the-badge)](https://synaxcode.org)
[![Cloud IDE](https://img.shields.io/badge/Cloud_IDE-synaxcode.online-a855f7?style=for-the-badge)](https://synaxcode.online)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)

> **"Don't Write Syntax. Express Your Intent. Watch It Adapt & Accelerate."**  
> **"Kod Yazmayın. Niyetinizi Söyleyin. Çalıştıkça Donanıma Uyarlansın."**

**SYNAX (`.sx`)** is an experimental **neuro-symbolic programming language and adaptive runtime system**. Taking inspiration from biological neurobiology (action potential propagation, activity-dependent myelin plasticity, and saltatory conduction across Ranvier nodes), SYNAX translates declarative computational intents into verified symbolic ASTs and specializes hot paths into hardware-accelerated SIMD blocks across Universal Silicon (from TinyMCUs to ARM64 NEON, x86_64 AVX-512, and Apple Metal).

---

## 🌌 Core Architecture (`Synapse` • `Axon` • `Tycon` • `Myelin`)

| Core Layer | Biological Metaphor | Engineering Mechanism |
| :--- | :--- | :--- |
| **1. 🧠 SYNAPSE** | *Intent & Kernel Frontend* | Unified dual-format frontend (`synax_ir.py`). Lowers both structured `synax 0.1 kernel` blocks and declarative `niyet:/kural:` files into a canonical IEEE-754 `SynaxIR`. |
| **2. 🛡️ IMMUNE SHIELD** | *Membrane Selectivity* | Dual-Reference Semantic Gate + 19-suite differential verifier (`synax_verifier.py`) + branchless bitwise IEEE-754 validation (`preserve`, `heal_inputs`, `zero_output`, `reject`). |
| **3. 🦎 AXON** | *Hardware Chameleon* | Probes hardware topology and synthesizes targets for **Tier-0 Q16.16 Fixed-Point (TinyMCU)**, **C11 Scalar**, **ARM64 NEON (`float32x4_t`)**, **x86 AVX-512**, and **Apple GCD Multicore**. |
| **4. ⚡ TYCON** | *Candidate Synthesis & Elimination* | Unified compiler (`synaxc.py`) generating scalar, unrolled, NEON, 4-accumulator prefetch, and multicore variants; eliminates any candidate failing 19 adversarial test suites (`rtol=1e-5`, exact `NaN`/`±Inf` parity). |
| **5. 🧬 MYELIN** | *Saltatory Hot-Swap & Cache* | Cryptographically signed cache (`~/.cache/synax/hafiza/<ir_hash>/`) + O(1) C function-pointer hot-swap (`synax_myelin_engine.c`) transitioning live `SynaxAxonChannel` streams from scalar to verified SIMD. |

---

## 🚀 Quick Install & Usage

### 1. One-Line Official Installer
```bash
curl -sSf https://synaxcode.com/install.sh | sh
```

### 2. Standalone Unified CLI (`synax`)
```bash
# 1. Statically inspect canonical IR, C11/NEON lowering & Dual-Reference check:
./synax check examples/hemodynamic_cpp.sx

# 2. Compile, verify across 19 adversarial suites, benchmark & cache winner:
./synax compile examples/kapili_aktivasyon.sx

# 3. Stream bursts through C SynaxAxonChannel with automatic function-pointer hot-swap:
./synax run examples/biyomedikal_kardiyo.sx

# 4. Run full differential & unified compiler regression test suites:
./synax test

# 5. View hardware profile and cryptographically signed Myelin cache:
./synax status
```

---

## 📊 Hardware Benchmarks (Apple Silicon M1, Apple Clang 21, `N = 4,000,000` float32)

All candidates are compiled **without `-ffast-math`** (preserving exact IEEE-754 `NaN`/`±Inf` semantics), verified across 19 edge-case suites (`n=0..100,003`, subnormals `1e-40`, `±3.4e38`, `12x12` special-value Cartesian product), and timed with pre-allocated warm-cache buffers (median of 15 runs):

| `.sx` Workload | Safety Policy | Scalar C11 (`-O1`) | `clang -O3` Baseline | SYNAX Verified Winner | vs `clang -O3` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `kapili_aktivasyon.sx` (`sigmoid(a) * b`) | `preserve` | `7.92 ms` | `7.10 ms` | **`3.39 ms`** (1C NEON) / **`1.10 ms`** (GCD+NEON) | **`2.10x` (1C) / `6.48x` (MC)** |
| `biyomedikal_kardiyo.sx` (`sqrt(Δ²+ε)+0.5(a+b)`) | `heal_inputs (±1000)` | `6.18 ms` | `1.70 ms` | **`1.57 ms`** (1C NEON) / **`1.30 ms`** (GCD+NEON) | **`1.31x`** |
| `hemodynamic_cpp.sx` (`clamp(dbp - cvp)`) | `heal_inputs + clamp` | `5.30 ms` | `1.05 ms` | **`0.97 ms`** (`v2_neon_simd`) | **`1.09x`** |
| `normalized_difference.sx` (`clamp(\|a-b\|, 0, 1)`) | `reject` | `5.57 ms` | `1.58 ms` | **`1.33 ms`** (`v4_gcd_multicore_neon`) | **`1.18x`** |

*Engineering Invariant: `optimization must never change semantics`. Memory-bandwidth-bound kernels saturate Apple M1 DRAM near ~1.0 ms for 4M floats (48 MB traffic), where `TYCON` honestly selects whichever verified candidate wins empirically.*

---

## ⚖️ License & Policies

- **License:** Open source under the [Apache License, Version 2.0](LICENSE).
- **Attribution & Notice:** See [NOTICE](NOTICE).
- **Trademark Policy:** The names SYNAX, SYNAXCODE, and associated logos are reserved trademarks. See [TRADEMARKS.md](TRADEMARKS.md).
- **Medical Research Disclaimer:** SYNAX biomedical modules are for retrospective academic research only and are **not** clinically validated medical devices. See [MEDICAL_RESEARCH_DISCLAIMER.md](MEDICAL_RESEARCH_DISCLAIMER.md).

---

## 🌐 Official Ecosystem

- **Main Platform & Web:** [synaxcode.com](https://synaxcode.com)
- **Documentation & Whitepaper:** [synaxcode.org](https://synaxcode.org)
- **Beginner Guide:** [synaxcode.org/guide.html](https://synaxcode.org/guide.html)
- **Cloud Studio IDE:** [synaxcode.online](https://synaxcode.online)
- **GitHub Repository:** [github.com/ofaemd-creator/synax](https://github.com/ofaemd-creator/synax)
- **Contact:** `dev@synaxcode.com` | `ofaemd@gmail.com`
