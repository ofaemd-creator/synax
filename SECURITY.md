# Security Policy & Zero-Trust Architecture (`SYNAX-SEC v2.0`)

SYNAX (`.sx`) is designed for mission-critical environments ranging from bare-metal medical & aerospace microcontrollers (`Tier-0 Q16.16 Integer`) to multi-GPU supercomputing clusters (`Tier-5 CUDA/Metal`). Security and mathematical determinism are enforced at every layer of the compiler and self-evolving runtime.

## 1. Zero-Trust Compiler & AST Firewall ([`synax_security.py`](synax_security.py))
- **Static Expression Verification (`SynaxSecurityGuard.verify_c_expression`):** Every lowered C89/C99/SIMD/GPU expression is inspected against a strict character whitelist and forbidden pattern matcher before compilation.
- **No Arbitrary Code / Shell Injection:** Inline assembly escapes (`__asm__`), preprocessor directives (`#include`, `#define`), dynamic loader calls (`dlopen`), and process execution (`system`, `popen`, `exec*`, `fork`) are strictly blocked inside `.sx` intent lowering.
- **Balanced Syntax & Length Enforcement:** Unbalanced parentheses and oversized payloads (`> 4096` bytes per kernel expression) are rejected prior to code generation.

## 2. Cryptographic Memory & DNA Integrity (`SHA-256`)
Because SYNAX is a self-evolving language that writes learned concepts and optimal hardware chromosomes to disk, all persistent state files are protected by canonical `SHA-256` signatures (`_integrity_sha256`):
- [`synapse_brain.json`](synapse_brain.json) — Concept & AST Dictionary
- [`myelin_memory.json`](myelin_memory.json) — UCB1 Hardware DNA Bandit Memory
- [`synapse_weights.json`](synapse_weights.json) — RLSF (Reinforcement Learning from Silicon Feedback) Policy Weights

Any unauthorized tampering or disk corruption is immediately detected by `SynaxSecurityGuard.verify_json_file()` before execution.

## 3. Autonomous Runtime Immune Shield (`Tycon ImmuneShield`)
- Every compiled SYNAX kernel includes an inline hardware-accelerated **NaN / $\pm\infty$ / Subnormal Immune Shield** (`synax_immune_scan_and_heal`), guaranteeing zero silent numerical corruption in downstream biomedical, financial, or control-loop pipelines.

## 4. Reporting a Vulnerability
To report a security issue, please contact the SYNAX Core Security Team at **`dev@synaxcode.com`**.
