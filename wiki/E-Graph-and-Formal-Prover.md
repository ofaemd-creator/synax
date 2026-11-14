# E-Graph Equality Saturation & Formal Interval Prover

## 1. E-Graph Equality Saturation (`src/synax/egraph.py`)

Classical compilers suffer from the **phase-ordering problem**: applying one destructive peephole rewrite can block a better hardware fusion rule later.

SYNAX `v1.0.0` uses an **Equivalence Graph (E-Graph)** with congruence closure (`UnionFind` + hashconsing):
1. All algebraic and hardware-fusion equivalences (`(a * b) + c <=> fma(a, b, c)`, `x * x <=> pow2(x)`, `relu(relu(x)) <=> relu(x)`, `select(c, x, x) <=> x`, exact power-of-two reciprocal multiplication) are added simultaneously into equivalence classes (`E-Classes`).
2. Bottom-up dynamic programming (`extract_best`) selects the lowest-cycle AST according to the target silicon cost model (`neon` vs `mcu_q16`).

## 2. Formal Interval Abstract Interpretation (`src/synax/formal_prover.py`)

Before executing a kernel on hardware, `prove_kernel_safety(ir, a_bounds, b_bounds)` propagates IEEE-754 interval bounds `[lo, hi]` through every AST node and `SafetyPolicy` rule to issue a SHA-256 signed `FormalProofCertificate` verifying:
- `div_by_zero_free`: Denominator intervals never cross `0.0`.
- `domain_error_free`: `sqrt(x)` and `log(x)` inputs remain strictly within valid real domains.
- `overflow_free`: Output bounds remain strictly within finite IEEE-754 `binary32` limits (`[-3.4028e38, +3.4028e38]`).
