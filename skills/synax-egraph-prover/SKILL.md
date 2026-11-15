---
name: synax-egraph-prover
description: Optimize mathematical expressions with E-Graph Equality Saturation (FMA, pow2, pow3, ReLU fusion) and prove static IEEE-754 interval safety bounds ([lo, hi], division-by-zero freedom, overflow freedom).
---

# SYNAX E-Graph & Formal Interval Prover Skill (`synax-egraph-prover`)

Provides two next-generation compiler passes (`src/synax/egraph.py` and `src/synax/formal_prover.py`) for Claude Code, OpenAI Codex, Google Antigravity, and SYNAX.

## Python Usage

```python
from synax.egraph import saturate_and_extract
from synax.formal_prover import prove_sx_kernel_safety

res = saturate_and_extract("(a * b + c) + (x - x)")
print(res["optimized_expr"])  # fma(a, b, c)
```
