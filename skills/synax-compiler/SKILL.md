---
name: synax-compiler
description: Compile, formally prove (Interval Abstract Interpretation), E-Graph saturate, and verify (.sx) kernels to C11, ARM64 NEON, x86 AVX2, LLVM IR, and Q16.16 MCU with 19-suite IEEE-754 0-ULP verification.
---

# SYNAX v1.0.0 Compiler, Formal Prover & E-Graph Engine

Use this skill whenever the user works with `.sx` kernels, high-assurance numerical/signal processing, embedded MCU fixed-point (`Q16.16`) codegen, SIMD vectorization (`ARM64 NEON` / `x86 AVX2`), or formal interval verification.

## Core Capabilities

1. **Check & Type-Verify `.sx` Kernels:**
   ```bash
   python3 synax_cli.py check examples/synax_v1_showcase.sx
   ```
2. **Execute & Benchmark `.sx` Kernels (19-Suite 0-ULP Differential Check):**
   ```bash
   python3 synax_cli.py run examples/synax_v1_showcase.sx
   ```
3. **E-Graph Equality Saturation & Formal Interval Proof (Python SDK):**
   ```python
   import synax
   from synax.egraph import saturate_and_extract
   from synax.formal_prover import prove_kernel_safety

   ir = synax.check_sx("examples/synax_v1_showcase.sx")
   eg = saturate_and_extract(ir.expr, target="neon")
   cert = prove_kernel_safety(ir, (-500.0, 500.0), (-500.0, 500.0))
   ```
4. **Autonomous Coding Agent (`./synax code`):**
   ```bash
   ./synax code "Inspect examples/ and verify all .sx kernels"
   ```
