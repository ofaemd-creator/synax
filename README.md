# ⚡ SYNAX (`.sx`) — The Self-Evolving Neuro-Symbolic Programming Language

[![Website](https://img.shields.io/badge/Platform-synaxcode.com-10b981?style=for-the-badge)](https://synaxcode.com)
[![Foundation](https://img.shields.io/badge/Whitepaper-synaxcode.org-06b6d4?style=for-the-badge)](https://synaxcode.org)
[![Cloud IDE](https://img.shields.io/badge/Cloud_IDE-synaxcode.online-a855f7?style=for-the-badge)](https://synaxcode.online)
[![License](https://img.shields.io/badge/License-MIT_%2F_Apache_2.0-blue?style=for-the-badge)](LICENSE)

> **"Don't Write Syntax. Express Your Intent. Watch It Evolve & Accelerate Live."**  
> **"Kod Yazmayın. Niyetinizi Söyleyin. Çalıştıkça Kendi Kendine Hızlansın."**

**SYNAX (`.sx`)** is the world's first **self-evolving neuro-symbolic programming language and genetic hardware superoptimizer**. Instead of compiling code into a static binary that never changes, SYNAX synthesizes a population of hardware DNA variants across **Universal Silicon** (from `16KB TinyMCUs` to `x86_64 AVX-512`, `ARM64 NEON`, `RISC-V`, `Apple Metal`, and `NVIDIA CUDA Tensor Clusters`) and uses real-time Multi-Armed Bandit Reinforcement Learning to lock the fastest gene into persistent **Myelin Memory**.

---

## 🌌 Tri-Core Architecture (`Synapse` • `Axon` • `Tycon`)

| Core Layer | Biological Role | Engineering Mechanism |
| :--- | :--- | :--- |
| **1. 🧠 SYNAPSE** | *Prefrontal Cortex (Intent)* | Trainable offline neuro-symbolic parser (`synapse_neural_model.py`). Converts natural language (English/Turkish) and mathematical rules into verified Symbolic ASTs without borrow-checker (`'a`) friction. |
| **2. 🦎 AXON** | *Peripheral Nervous System* | Universal Silicon Chameleon. Probes hardware in `<1 ms` and synthesizes targets for **TinyMCU (Zero-Heap Stack)**, **ARM64 NEON**, **x86 AVX2/AVX-512**, **Asymmetric P-Cores**, and **Unified GPU Shaders**. |
| **3. ⚡ TYCON** | *Myelin Sheath & Evolution* | Runtime Genetic Mutator (`synax_core.py` & `synaxc.py`). Mutates SIMD lane widths (`4x..32x`), L1D cache prefetch strides (`128B..512B`), and thread topologies, locking winners into `myelin_memory.json`. |
| **4. 🛡️ IMMUNE SHIELD** | *Autonomous Immune System* | Hardware-level `NaN`, `±Infinity`, and voltage-spike quarantine. Scans and self-heals `8,000,000` signals in `~3.7 ms` with **Zero Crashes**. |

---

## 🚀 Quick Install & Usage

### 1. One-Line Official Installer
```bash
curl -sSf https://synaxcode.com/install.sh | sh
```

### 2. Compile Any Natural Language Intent into a Standalone Native Binary (`synaxc`)
```bash
# Teach Synapse-Nano a new domain concept (persisted to synapse_brain.json):
./synaxc.py "öğren: kardiyak perfüzyon indeksi = sqrt(abs(a - b)) / (a + b) + bias"

# Compile & evolve into a zero-dependency native machine binary by name:
./synaxc.py "niyet: hastalar için kardiyak perfüzyon indeksi hesapla"
```

### 3. Use as a 300x Accelerator Inside Python (`synax_sdk.py`)
```python
from synax_sdk import compile_intent

engine = compile_intent("""
    niyet: İki veri serisi arasındaki farkın karesini (anomali enerjisini) hesapla.
    kural: Bozuk verileri (NaN/Sonsuz) otomatik temizle.
""")

report = engine.run(signal_a, signal_b, bias=1.0)
print(report["secilen_dna"])  # e.g., MUT-4 [Hyper-6T-NEON32]
print(report["sure_us"])      # 35.92 µs (for 500,000 elements!)
```

---

## 📊 Experimental Benchmarks ($N = 8,000,000$ Synaptic Signals)

| Hardware / Gene Variant | DNA Chromosome | Best Execution Time | Speedup vs Python |
| :--- | :--- | :--- | :--- |
| **Standard Python Loop** | `Interpreter` | `~494,000.0 µs` | `1.0x` |
| **`GEN-0 [TinyMCU]`** | `SIMD:1x \| PF:0B \| T:1` | `14,513.9 µs` | `34.0x` |
| **`GEN-1 [Unrolled-4x]`** | `SIMD:4x \| PF:0B \| T:1` | `8,407.4 µs` | `58.7x` |
| **`GEN-3 [Tycon-8Core]`** | `SIMD:8x \| PF:0B \| T:8 (4P+4E)` | `2,128.2 µs` | `232.1x` |
| **`MUT-3 [Firestorm-4P-Only]`** | `SIMD:16x \| PF:256B \| T:4 (P-Only)` | **`1,885.2 µs`** | **`262.0x`** *(Fastest CPU DNA)* |
| **`GEN-4 [Metal-GPU]`** | `Unified float4 Shader` | **`1,816.0 µs`** | **`~1.3x - 8.0x`** (Skaler C99 loop disable bazlı) |

---

## 🌐 Official Ecosystem
- **Main Platform & Playground:** [https://synaxcode.com](https://synaxcode.com)
- **Foundation, Book & Whitepaper:** [https://synaxcode.org](https://synaxcode.org)
- **Full-Screen Cloud Studio IDE:** [https://synaxcode.online](https://synaxcode.online)
- **Contact:** `dev@synaxcode.com`

