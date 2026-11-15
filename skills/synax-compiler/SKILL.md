---
name: synax-compiler
description: Compile, formally prove (Interval Abstract Interpretation), E-Graph saturate, and verify (.sx) kernels to C11, ARM64 NEON, x86 AVX2, LLVM IR, and Q16.16 MCU with 19-suite IEEE-754 0-ULP verification.
---

# SYNAX Compiler & Verification Skill (`synax-compiler`)

Provides deterministic compilation and 19-suite IEEE-754 0-ULP verification for `.sx` numerical kernels across C11, ARM64 NEON, x86 AVX2, LLVM IR, and Q16.16 fixed-point microcontrollers.

## Commands

```bash
./synax check examples/cerebral_perfusion.sx
./synax compile examples/cerebral_perfusion.sx
./synax build examples/cerebral_perfusion.sx --emit-c-header
./synax test
```
