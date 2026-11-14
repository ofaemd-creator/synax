# SYNAX 1.0 Language Reference

## Canonical Module Structure

```synax
synax 1.0

kernel synax_v1_showcase(
  map_mmhg: tensor<f32>,
  icp_mmhg: tensor<f32>
) -> tensor<f32> {
  intent "SYNAX 1.0 Multi-Let, Branchless Select & Sigmoid Autoregulation"

  require shape(map_mmhg) == shape(icp_mmhg)

  safety {
    nonfinite = heal(0.0)
    range_check = clamp(0.0, 250.0)
  }

  let cpp = relu(map_mmhg - icp_mmhg)
  let gate = sigmoid((cpp - 50.0) * 0.1)
  let autoreg = select(cpp - 40.0, fma(cpp, gate, 5.0), cpp * 0.5)
  return autoreg

  optimize latency
  target auto
}
```

## Primitives & Intrinsics

| Operator / Function | Description | ARM64 NEON Lowering | x86_64 AVX2 Lowering | Q16.16 MCU Lowering |
| :--- | :--- | :--- | :--- | :--- |
| `select(cond, t, f)` / `mux` | Branchless conditional (`cond > 0 ? t : f`) | `vbslq_f32(vcgtq_f32(c, 0), t, f)` | `_mm256_blendv_ps` | `((c) > 0 ? (t) : (f))` |
| `fma(a, b, c)` | Fused multiply-add (`a * b + c`) | `vfmaq_f32(c, a, b)` | `_mm256_fmadd_ps` | `(((int64_t)a * b) >> 16) + c` |
| `relu(x)` | Rectified linear unit (`max(0, x)`) | `vmaxq_f32(x, vdupq_n_f32(0))` | `_mm256_max_ps` | `((x) > 0 ? (x) : 0)` |
| `clamp(x, lo, hi)` | Bounded range projection | `vminq_f32(vmaxq_f32(x, lo), hi)` | `_mm256_min_ps` / `_max_ps` | Bounded integer clamp |
| `sum(x)`, `mean(x)`, `dot(a,b)` | Neumaier compensated dendritic reductions | Compensated SIMD reduction | Compensated AVX2 reduction | 64-bit accumulator |
