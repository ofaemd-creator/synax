# ⚡ SYNAX (`.sx`) — Neuro-Symbolic Kernel Language, E-Graph Optimizer, Formal Prover & Multi-Agent Ecosystem

[![CI](https://img.shields.io/github/actions/workflow/status/ofaemd-creator/synax/ci.yml?branch=main&style=for-the-badge&label=Cross-Platform_CI)](https://github.com/ofaemd-creator/synax/actions)
[![CodeQL](https://img.shields.io/badge/CodeQL_Security-Active-10b981?style=for-the-badge)](https://github.com/ofaemd-creator/synax/security)
[![Platform](https://img.shields.io/badge/Platform-synaxcode.com-10b981?style=for-the-badge)](https://synaxcode.com)
[![Docs & Wiki](https://img.shields.io/badge/Wiki_&_Spec-synaxcode.org-06b6d4?style=for-the-badge)](https://github.com/ofaemd-creator/synax/wiki)
[![Cloud IDE](https://img.shields.io/badge/Cloud_Studio-synaxcode.online-a855f7?style=for-the-badge)](https://synaxcode.online)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)

> **Core Engineering Invariant:** `optimization must never change semantics`  
> **"Ne yapmak istediğinizi semantik olarak tanımlayın; sistem bunu matematiksel olarak kanıtlasın, E-Graph ile en düşük çevrimli donanım koduna indirgesin, 19 IEEE-754 uç kümesinde doğrulasın ve en iyisini hatırlasın."**

**SYNAX (`.sx`)** is an open-source **neuro-symbolic kernel language, E-Graph equality saturation optimizer, static IEEE-754 interval formal prover, differential verification compiler (`synaxc`), and multi-model agent skill ecosystem**. SYNAX lowers `.sx` programs into a canonical IEEE-754 Intermediate Representation (`SynaxIR`), proves static interval safety bounds (`[lo, hi]`), synthesizes multi-target native code (**C11 Scalar**, **ARM64 NEON**, **x86_64 AVX2+FMA**, **Apple GCD Multicore**, **SSA LLVM IR**, and **Q16.16 Fixed-Point MCU C99**), eliminates any candidate that deviates across **19 adversarial IEEE-754 test suites**, and integrates natively with **Claude Code, OpenAI Codex, Google Antigravity, Cursor, and Telegram**.

---

## 🧩 Modular Sub-Repositories & Multi-Model Skill Ecosystem

SYNAX is architected as a core compiler repository paired with specialized standalone sub-repositories and agent skills for **Claude Code**, **OpenAI Codex**, **Google Antigravity**, and **Cursor**:

| Repository / Module | Specialization | Supported AI Agents | Status |
| :--- | :--- | :--- | :--- |
| **[`ofaemd-creator/synax`](https://github.com/ofaemd-creator/synax)** | Core `.sx` Compiler (`synaxc`), 19-Suite IEEE-754 Verifier, `libsynax_myelin` Runtime & SDKs | SYNAX, Claude Code, Codex, Antigravity, Cursor | **Active (`v1.0.0`)** |
| **[`ofaemd-creator/synax-telegram-bot`](https://github.com/ofaemd-creator/synax-telegram-bot)** | Zero-Dependency Telegram Bot & Remote Compiler/Agent Bridge (`/egraph`, `/prove`, `/check`, `/run`, `/code`) | Claude Code, Codex, Antigravity, SYNAX | **Active (`v1.0.0`)** |
| **[`ofaemd-creator/synax-egraph-prover`](https://github.com/ofaemd-creator/synax-egraph-prover)** | Standalone E-Graph Equality Saturation Optimizer & Static IEEE-754 Interval Formal Prover (`[lo, hi]`) | Claude Code, Codex, Antigravity, SYNAX | **Active (`v1.0.0`)** |
| **[`ofaemd-creator/synax-studio`](https://github.com/ofaemd-creator/synax-studio)** | Standalone `SYNAX Studio IDE` Desktop App (`macOS .app`), Web Workbench & VS Code Extension | SYNAX Studio, VS Code, Cursor | **Active (`v1.0.0`)** |

---

## 🏗️ 10-Layer Platform Architecture (`v1.0.0`)

| Layer | Subsystem | Repository Implementation |
| :--- | :--- | :--- |
| **1. Language & Spec** | ISO-14977 EBNF grammar, Lexer, Typed AST Parser, Static `TypeChecker` | [`spec/synax.ebnf`](spec/synax.ebnf), [`spec/LANGUAGE_SPEC.md`](spec/LANGUAGE_SPEC.md), [`src/synax/lexer.py`](src/synax/lexer.py), [`src/synax/parser.py`](src/synax/parser.py), [`src/synax/type_system.py`](src/synax/type_system.py) |
| **2. E-Graph & Formal Prover** | Equality Saturation (`UnionFind`, congruence closure, `fma`/`pow2`/`pow3`/`relu` fusion) & Static Interval Prover (`[lo, hi]`) | [`src/synax/egraph.py`](src/synax/egraph.py), [`src/synax/formal_prover.py`](src/synax/formal_prover.py), [`tests/test_nextgen_2050.py`](tests/test_nextgen_2050.py) |
| **3. Compiler & Backends** | IEEE-754 `ReferenceInterpreter`, C11, ARM64 NEON, x86_64 AVX2+FMA, SSA LLVM IR (`.ll`), Q16.16 MCU, `.sx.lock` | [`synaxc.py`](synaxc.py), [`src/synax/interpreter.py`](src/synax/interpreter.py), [`src/synax/backends/`](src/synax/backends/), [`src/synax/semantic_lock.py`](src/synax/semantic_lock.py) |
| **4. TYCON / MYELIN** | Multi-variant synthesis, warm-cache median benchmark, `hw_fingerprint`, SHA-256 signed persistent cache | [`src/synax/hardware.py`](src/synax/hardware.py), [`src/synax/myelin_store.py`](src/synax/myelin_store.py), [`synax_verifier.py`](synax_verifier.py) |
| **5. Autonomous Coding Agent** | Multi-turn tool-calling agent (`list_files`, `read_file`, `write_file`, `edit_file`, `grep`, `bash`, `sx_check`, `sx_run`) | [`src/synax/agent.py`](src/synax/agent.py), [`SYNAX.md`](SYNAX.md), [`tests/test_agent.py`](tests/test_agent.py) |
| **6. Telegram Bot & Skills** | Zero-dependency Telegram Bot API client & MCP skill bridge (`/status`, `/egraph`, `/prove`, `/check`, `/run`, `/code`) | [`src/synax/telegram_bot.py`](src/synax/telegram_bot.py), [`skills/synax-telegram-bot/SKILL.md`](skills/synax-telegram-bot/SKILL.md), [`tests/test_telegram_bot.py`](tests/test_telegram_bot.py) |
| **7. AI Plugin Ecosystem** | Native manifests for Claude Code, OpenAI Codex, Google Antigravity, Cursor, and OpenCode | [`src/synax/ecosystem.py`](src/synax/ecosystem.py), [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json), [`.mcp.json`](.mcp.json), [`AGENTS.md`](AGENTS.md), [`.codex/config.toml`](.codex/config.toml) |
| **8. Multi-Language SDKs** | `pip install synax` (zero-dep PEP 517/660), Python API (`import synax`), C11 ABI (`synax.h`), C++17 RAII (`synax.hpp`), Rust FFI | [`pyproject.toml`](pyproject.toml), [`src/synax/sdk.py`](src/synax/sdk.py), [`include/synax.h`](include/synax.h), [`include/synax.hpp`](include/synax.hpp), [`bindings/rust/`](bindings/rust/) |
| **9. SYNAX Studio IDE** | Standalone macOS Desktop App (`SYNAX Studio.app`), Web Workbench, LSP 3.17 Server, and VS Code Full-Screen App | [`src/synax/studio_app.py`](src/synax/studio_app.py), [`editors/vscode-synax/`](editors/vscode-synax/), [`src/synax/lsp/server.py`](src/synax/lsp/server.py) |
| **10. Governance & Security** | Apache-2.0 License, CodeQL, Dependabot, Secret Scanning, Security Policy, CFF Citation, Medical Disclaimer | [`LICENSE`](LICENSE), [`SECURITY.md`](SECURITY.md), [`.github/dependabot.yml`](.github/dependabot.yml), [`CITATION.cff`](CITATION.cff), [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md) |

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
from synax.egraph import saturate_and_extract
from synax.formal_prover import prove_kernel_safety
from synax_ir import parse_sx

# 1. Parse and verify .sx kernel across 19 IEEE-754 suites
ir = parse_sx(open("examples/cerebral_perfusion.sx").read())
out, healed = synax.eval_sx("examples/cerebral_perfusion.sx", [95.0, float("nan")], [15.0, 12.0])

# 2. Run E-Graph Equality Saturation & Formal Interval Prover
egraph_report = saturate_and_extract(ir.expr, target="neon")
proof_cert = prove_kernel_safety(ir, a_bounds=(0.0, 250.0), b_bounds=(0.0, 100.0))
print("Optimal AST:", egraph_report.optimized_ast.to_human_formula())
print("Formal Proof SHA-256:", proof_cert.certificate_sha256)
```

### 2. Developer CLI, Autonomous Agent & Telegram Bot (`./synax`)
```bash
# Static type-check, canonical IR & Dual-Reference IEEE-754 verification:
./synax check examples/hemodynamic_cpp.sx

# Launch the Autonomous Tool-Calling Coding Agent:
./synax code

# Test the Telegram Bot Skill locally or start Long-Polling:
./synax telegram --status
./synax telegram --cmd "/egraph (a * b + 1.0) + (a - a)"
./synax telegram --cmd "/prove relu(a - b)"
./synax telegram --poll

# Launch SYNAX Studio IDE or build the standalone macOS .app bundle:
./synax studio --build-app
./synax studio

# Install plugins for Claude Code, OpenAI Codex, Google Antigravity & Cursor:
./synax ecosystem

# Run all 15 verification suites (Lexer/Parser, LSP, C/C++17 SDK, Differential, Fuzzer, E-Graph, Prover, Agent, Telegram):
./synax test
```

---

## 📊 Reproducible Benchmarks (Apple Silicon M1, Clang 17, `N = 4,000,000` `float32`)

Measured under warm-cache conditions (21 timed runs, pre-allocated buffers, zero `-ffast-math`, 19/19 IEEE-754 edge suites verified — see [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md)):

| `.sx` Workload | Safety Policy | Scalar C11 (`-O1`) | `clang -O3` | Verified Winner | Median Latency (IQR) | Throughput | Speedup vs `clang -O3` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `kapili_aktivasyon.sx` (`sigmoid(a)*b`) | `preserve` | `7.92 ms` | `6.91 ms` | `v4_gcd_multicore_neon` | **`1.01 ms` (`0.08 ms`)** | **`47.5 GB/s`** | **`6.84x`** |
| `biyomedikal_kardiyo.sx` (`sqrt(d^2+eps)+0.5(a+b)`) | `heal_inputs (1000)` | `6.18 ms` | `1.70 ms` | `v4_gcd_multicore_neon` | **`1.30 ms` (`0.05 ms`)** | **`36.9 GB/s`** | **`1.31x`** |
| `hemodynamic_cpp.sx` (`clamp(dbp - cvp)`) | `heal_inputs + clamp` | `5.30 ms` | `1.05 ms` | `v2_neon_simd` | **`0.97 ms` (`0.02 ms`)** | **`49.5 GB/s`** | **`1.09x`** |
| `anomali_v04.sx` (`(a-b)^2 + 0.5`) | `zero_output` | `3.61 ms` | `0.93 ms` | `v3_neon_4acc_prefetch` | **`0.93 ms` (`0.01 ms`)** | **`51.5 GB/s`** | **`1.00x`** (DRAM limit) |

---

## ⚖️ License, Governance & Medical Research Disclaimer

- **License:** Open source under the [Apache License, Version 2.0](LICENSE) ([NOTICE](NOTICE), [LICENSING.md](LICENSING.md)).
- **Trademarks:** `SYNAX`, `SYNAXCODE`, and official marks are governed by [TRADEMARKS.md](TRADEMARKS.md).
- **Governance & Security:** See [GOVERNANCE.md](GOVERNANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [GitHub Wiki](https://github.com/ofaemd-creator/synax/wiki).
- **Medical Research Disclaimer:** SYNAX is **experimental academic/computational research software** and is **NOT** a certified medical device (EU MDR 2017/745, FDA 21 CFR, IEC 60601-2-4). Never use for clinical diagnosis, patient monitoring, or defibrillation decisions. See [MEDICAL_RESEARCH_DISCLAIMER.md](MEDICAL_RESEARCH_DISCLAIMER.md).

---

## 🌐 Official Ecosystem

- **Platform:** https://synaxcode.com
- **Specification & Docs:** https://synaxcode.org | [GitHub Wiki](https://github.com/ofaemd-creator/synax/wiki) | [Formal EBNF](spec/synax.ebnf) | [Language Spec](spec/LANGUAGE_SPEC.md)
- **Cloud Studio IDE:** https://synaxcode.online
- **GitHub Repository:** https://github.com/ofaemd-creator/synax
- **Contact:** `dev@synaxcode.com` | `ofaemd@gmail.com`
