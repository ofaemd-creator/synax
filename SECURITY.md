# Security Policy & Zero-Trust Architecture (`SYNAX-SEC v2.5`)

SYNAX (`.sx`) is engineered for high-integrity numerical computing, ranging from resource-constrained embedded microcontrollers to SIMD/multicore CPUs. Security, filesystem isolation, and IEEE-754 mathematical determinism are enforced across every stage of the compiler (`synaxc`) and adaptive runtime (`libsynax_myelin`).

---

## 1. Supported Versions

| Version | Status | Security Updates |
| :--- | :--- | :--- |
| **`0.5.x` (Unified Compiler & Myelin Engine)** | **Supported** | Active security & differential verification patches |
| `< 0.5.0` (Legacy prototypes) | Unsupported | Please upgrade to `>= 0.5.0` |

---

## 2. Reporting a Vulnerability

**Please do NOT open public GitHub issues for suspected security vulnerabilities.**

Report security issues privately via email to the SYNAX Security & Architecture Team:

- **Primary Security Contact:** `dev@synaxcode.com`
- **Lead Maintainer Direct Contact:** `ofaemd@gmail.com` (Dr. Ömer Faruk Aydın)

### What to Include
1. Affected component (`synax_ir.py`, `synax_security.py`, `synaxc.py`, `synax_myelin_engine.c`, SDK bindings, etc.) and version/commit hash.
2. Minimal `.sx` input, C API call, or cache payload reproducing the issue.
3. Impact assessment (e.g., sandbox/firewall bypass, memory safety defect in C FFI, cache signature bypass, or silent IEEE-754 semantic corruption).

### Response Timeline
- **Acknowledgement:** Within **48 hours** of receipt.
- **Triage & Remediation Plan:** Within **7 days**.
- **Coordinated Disclosure:** Credit is granted in release advisories once a verified fix is published.

---

## 3. Defense-in-Depth Security Controls

### 3.1 Zero-Trust AST & Code-Injection Firewall (`SynaxSecurityGuard`)
Implemented in [`synax_security.py`](synax_security.py), `SynaxSecurityGuard` inspects both lowered expressions and full C translation units prior to invoking the native C compiler:
- **Expression Verification (`verify_c_expression`):** Enforces a strict character whitelist, balanced parentheses, and payload length bounds (`1..4096` bytes). Blocks shell/process execution (`system`, `popen`, `exec*`, `fork`), dynamic loader escapes (`dlopen`), inline assembly (`asm`, `__asm__`), unsafe libc calls (`gets`, `strcpy`, `sprintf`), and preprocessor directives (`#include`, `#define`, `#pragma`).
- **Translation-Unit Verification (`verify_c_module_source`):** Inspects generated and optional LLM-mutated C11 modules (`<= 65,536` bytes) against an explicit `#include` allowlist (`stddef.h`, `stdint.h`, `stdbool.h`, `float.h`, `math.h`, `arm_neon.h`, `immintrin.h`, `dispatch/dispatch.h`, `unistd.h`, `string.h`) and rejects filesystem or network syscalls (`fopen`, `freopen`, `socket`, `connect`, `unlink`, `remove`, `rename`).

### 3.2 `0700` Cache Directory Isolation
Compiled Myelin artifacts (`~/.cache/synax/hafiza/<ir_hash>/` and per-UID fallback `/tmp/synax_<uid>`) are created with owner-only POSIX mode **`0700` (`rwx------`)** in both Python (`get_hafiza_root()`) and C (`synax_myelin_engine.c`). This prevents cross-user shared-object tampering, symlink races, and unauthorized inspection on multi-user POSIX hosts.

### 3.3 Cryptographic `SHA-256` State & Lockfile Signing
Persistent compiler metadata, lockfiles, and self-evolving runtime files carry canonical `SHA-256` digests (`_integrity_sha256` computed over sorted-key canonical JSON via `SynaxSecurityGuard.compute_canonical_sha256`):
- **`rapor.json`** — Per-kernel verification, candidate elimination, and benchmark manifest inside `~/.cache/synax/hafiza/<ir_hash>/`.
- **`.sx.lock`** — Deterministic compilation lockfiles pinning canonical `ir_hash`, safety policy, and verified artifact digests.
- **`synapse_brain.json` / `myelin_memory.json` / `synapse_weights.json`** — Persistent concept and hardware-bandit state verified via `SynaxSecurityGuard.verify_json_file()` prior to load; tampered cache entries are automatically invalidated and rebuilt from source.

### 3.4 IEEE-754 Runtime Immune Shield & 19-Suite Semantic Gate
- All non-finite (`NaN`, `±Inf`) and range-bound checks execute via unsigned 32-bit IEEE-754 bit-mask comparisons (`(bits & 0x7FFFFFFFu) <= bound_u32`), remaining 100% deterministic across scalar and SIMD lanes without `-ffast-math`.
- Every compiled candidate must pass all **19 adversarial differential test suites** against dual independent references before any `.dylib`/`.so` can enter the Myelin cache.

---

## 4. Non-Clinical Research Scope

Security hardening in SYNAX does not constitute clinical medical device certification. All biomedical pipelines are strictly governed by [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md).
