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
| **1. 🧠 SYNAPSE** | *Intent Parser* | Trainable offline neuro-symbolic parser (`synapse_neural_model.py`). Converts natural language (English/Turkish) into verified Symbolic ASTs with algebraic reduction passes (`sqrt(u^2) -> abs(u)`). |
| **2. 🛡️ IMMUNE SHIELD** | *Membrane Selectivity* | Hardware-level signal sanitizer. IEEE 754 bit-mask validation (`(abs_bits <= 0x447A0000)`) catching `NaN`, `±Infinity`, and out-of-range sensor spikes across both channels with branchless SIMD. |
| **3. 🦎 AXON** | *Hardware Chameleon* | Probes hardware topology in `<1 ms` and synthesizes targets for **Tier-0 Q16.16 Fixed-Point (TinyMCU)**, **Tier-2 ARM64 NEON**, **Tier-3 x86 AVX2/AVX-512**, and **Tier-4 Apple Metal GPU**. |
| **4. ⚡ TYCON / JIT** | *Adaptive Plasticity* | Activity-dependent runtime specialized kernel synthesis (`synax_myelin_engine.c`). Generates and hot-swaps vector kernels when invocation frequency crosses the threshold. |
| **5. 🧬 MYELIN** | *Saltatory Conduction* | Persistent optimization cache (`myelin_memory.json`). Remembers winning hardware parameters, skipping generic dynamic dispatch and leaping directly across L1-aligned vector blocks. |

---

## 🚀 Quick Install & Usage

### 1. One-Line Official Installer
```bash
curl -sSf https://synaxcode.com/install.sh | sh
```

### 2. Standalone Unified CLI (`synax`)
```bash
# 1. Run a .sx intent script:
./synax run examples/biyomedikal_kardiyo.sx

# 2. Run the adaptive myelination differential test (Ranvier vs Scalar):
./synax myelin

# 3. Stream real-time biomedical signals (ABP / CVP / CPP):
./synax stream 3.0

# 4. View hardware profile and status:
./synax status
```

---

## 📊 Hardware Benchmarks (Apple Silicon M1, Clang 21 Native)

Measurements conducted under controlled, warm-cache conditions (median of 201 runs, $N = 32,768$ float elements):

| Implementation | Latency (Median) | Acceleration | Method |
| :--- | :--- | :--- | :--- |
| **Interpreted Scalar Loop (Baseline)** | `~420 µs` | `1.0x` | Scalar element-by-element branch checks |
| **Native Clang `-O3` (Auto-vectorized)** | `~120 µs` | `~3.5x` | Standard compiler vectorization |
| **SYNAX Ranvier Saltatory JIT (NEON)** | `~100 µs` | `~4.2x` | 128-bit NEON unrolled + bitwise Immune Shield |

*Note: Speedups against pure Python interpreted loops range between 50x–250x, but rigorous systems benchmarks compare directly against native compiled C (`clang -O3`).*

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
