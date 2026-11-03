# SYNAX Project Governance

This document defines the governance structure, decision-making procedures, language specification RFC workflow, and regulatory boundaries of the **SYNAX (`.sx`)** open-source project.

---

## 1. Governance Philosophy & Leadership

SYNAX follows an **open, meritocratic Apache-2.0 contribution model** combined with clear architectural stewardship:

- **Founder & Lead Architect:** **Dr. Ömer Faruk Aydın** (`ofaemd@gmail.com` / `dev@synaxcode.com`) — stewards the overall neuro-symbolic vision, `.sx` language specification, C ABI stability, and biomedical research ethics boundary.
- **Open Permissive Licensing:** All source code, compiler passes, SDK headers, and test suites are permanently licensed under the [Apache License, Version 2.0](LICENSE). There will never be proprietary "open-core" bait-and-switch relicensing of the core compiler or runtime.

---

## 2. Contributor Roles

1. **Users & Researchers:** Community members using SYNAX for numerical computing, compiler experimentation, or retrospective academic studies, reporting bugs, and sharing reproducible benchmarks.
2. **Contributors:** Anyone whose pull requests (code, SIMD backends, verification suites, documentation, or editor tooling) have been merged into the official repository.
3. **Subsystem Reviewers:** Experienced contributors granted review responsibilities over specific layers (e.g., Lexer/Parser/IR, SIMD Codegen, Rust/C++ SDKs, VS Code Extension, or PhysioNet Research Benchmarks).
4. **Core Maintainers:** Individuals with commit and release privileges who uphold the 19-suite differential verification gate, security policy (`SECURITY.md`), and semantic invariants.

Progression across roles is strictly meritocratic—earned through sustained, technically rigorous, and honest engineering contributions.

---

## 3. Decision-Making & `.sx` RFC Process

### Routine Engineering Changes
Bug fixes, additional adversarial test cases, documentation improvements, and new optimization candidates that preserve existing IR/ABI semantics are merged via standard GitHub Pull Requests using **lazy consensus** once CI passes on macOS, Linux, and Windows.

### Language Specification & ABI Changes (`SYNAX-RFC`)
Changes affecting any of the following require a written **RFC Proposal** (submitted as a GitHub Discussion/Issue or `docs/rfcs/` PR) and explicit approval from the Lead Architect:
1. `.sx` surface grammar keywords (`synax`, `kernel`, `safety`, `neuron`, `pulse`, `channel`, `immune`, `myelin`, or declarative `niyet:/kural:` semantics).
2. `SynaxIR` canonical hash computation or IEEE-754 `SafetyPolicy` semantics (`preserve`, `heal_inputs`, `zero_output`, `reject`).
3. Public C ABI structures or function signatures in [`include/synax.h`](include/synax.h) (`SYNAX_ABI_VERSION`).

---

## 4. Non-Negotiable Engineering & Regulatory Guardrails

No vote or pull request may override these three foundational project rules:

1. **Semantic Equivalence Invariant (`optimization must never change semantics`):** Any optimization pass or hardware backend failing differential verification against the IEEE-754 reference specification is rejected, regardless of speedup.
2. **Empirical Benchmark Honesty:** Published performance numbers must reflect reproducible warm-cache medians compared fairly against optimizing native compilers (`clang -O3`).
3. **Strict Clinical & Medical Non-Device Boundary:**
   - Per [`MEDICAL_RESEARCH_DISCLAIMER.md`](MEDICAL_RESEARCH_DISCLAIMER.md), SYNAX is **strictly academic and computational research software**.
   - It is **NOT** a certified medical device under EU MDR 2017/745, U.S. FDA 21 CFR, or IEC 60601-2-4, and must **NEVER** be marketed, documented, or deployed for clinical diagnosis, patient monitoring, CPR guidance, or automated external defibrillation (AED).
   - Maintainers will immediately reject any contribution that removes research disclaimers or introduces clinical treatment assertions.

---

## 5. Official Infrastructure & Trademarks

- **Primary GitHub Repository:** <https://github.com/ofaemd-creator/synax>
- **Sovereign Git Mirror:** <https://synaxcode.org/git/synax.git>
- **Documentation & Specification:** <https://synaxcode.org>
- **Cloud Studio IDE:** <https://synaxcode.online>
- **Trademarks:** Governed by [`TRADEMARKS.md`](TRADEMARKS.md) under Section 6 of the Apache License 2.0.
