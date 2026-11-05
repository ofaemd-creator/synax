# SYNAX Issue #6 — Retrospective VF/VT signal-processing evaluation (NON-CLINICAL)

> [!CAUTION]
> Research software only. Not a medical device; must not be used for diagnosis or shock/no-shock decisions. Results are retrospective on public data.

Generated: `2026-11-05T18:27:38.537857+00:00` — Host: `macOS-27.0.1-arm64-arm-64bit`

## Dataset

- Records: **57**, analysed 8 s windows: **6869** (excluded for >5 % invalid samples: 43)
- Category counts: `coarse_vf`=750, `fine_vf`=3, `rapid_vt`=431, `other_vt`=183, `nsr`=3690, `other_nonshock`=1720, `asystole`=92

## SYNAX kernel integrity (semantic preservation on real ECG)

- Active front-end conditioning: `ranvier_adaptive_filter.sx` (Ranvier Node adaptive depolarization filter)
- Samples processed: 16,003,120; IMMUNE-healed invalid samples: 35,662
- Max |native winner − C11 -O0 reference|: sanitizer `0.000e+00`, energy `1.526e-05`
- Total kernel time: native 17.67 ms vs C11 -O0 reference 410.49 ms (the -O0 kernel is a correctness oracle, NOT a fair speed baseline; see benchmarks/ for -O3 comparisons)
- IMMUNE heal counts of native and reference kernels were asserted equal on every record.

## Results (5-fold record-grouped CV, nested threshold selection)

### `synax_full_model` — AUC 0.9823

| Category | Metric | Value | 95% CI (Wilson) | k/n | Records | AHA goal | Meets (point) |
|---|---|---:|---|---:|---:|---:|:---:|
| coarse_vf | sensitivity | 73.47% | 70.2–76.5% | 551/750 | 41 | 90% | ❌ |
| fine_vf | sensitivity | 0.00% | 0.0–56.2% | 0/3 | 1 | report only | — |
| rapid_vt | sensitivity | 88.17% | 84.8–90.9% | 380/431 | 16 | 75% | ✅ |
| other_vt | sensitivity | 84.70% | 78.8–89.2% | 155/183 | 8 | report only | — |
| nsr | specificity | 99.00% | 98.6–99.3% | 3653/3690 | 50 | 99% | ❌ |
| other_nonshock | specificity | 99.77% | 99.4–99.9% | 1716/1720 | 16 | 95% | ✅ |
| asystole | specificity | 97.83% | 92.4–99.4% | 90/92 | 6 | 95% | ✅ |

Outer-fold thresholds: 0.922, 0.805, 0.865, 0.980, 0.905

### `ablation_without_synax_energy` — AUC 0.9825

| Category | Metric | Value | 95% CI (Wilson) | k/n | Records | AHA goal | Meets (point) |
|---|---|---:|---|---:|---:|---:|:---:|
| coarse_vf | sensitivity | 74.80% | 71.6–77.8% | 561/750 | 41 | 90% | ❌ |
| fine_vf | sensitivity | 0.00% | 0.0–56.2% | 0/3 | 1 | report only | — |
| rapid_vt | sensitivity | 88.63% | 85.3–91.3% | 382/431 | 16 | 75% | ✅ |
| other_vt | sensitivity | 85.79% | 80.0–90.1% | 157/183 | 8 | report only | — |
| nsr | specificity | 98.94% | 98.6–99.2% | 3651/3690 | 50 | 99% | ❌ |
| other_nonshock | specificity | 99.77% | 99.4–99.9% | 1716/1720 | 16 | 95% | ✅ |
| asystole | specificity | 97.83% | 92.4–99.4% | 90/92 | 6 | 95% | ✅ |

Outer-fold thresholds: 0.909, 0.767, 0.838, 0.969, 0.892

### `baseline_tcsc_only` — AUC 0.9631

| Category | Metric | Value | 95% CI (Wilson) | k/n | Records | AHA goal | Meets (point) |
|---|---|---:|---|---:|---:|---:|:---:|
| coarse_vf | sensitivity | 37.73% | 34.3–41.3% | 283/750 | 41 | 90% | ❌ |
| fine_vf | sensitivity | 0.00% | 0.0–56.2% | 0/3 | 1 | report only | — |
| rapid_vt | sensitivity | 40.37% | 35.8–45.1% | 174/431 | 16 | 75% | ❌ |
| other_vt | sensitivity | 69.40% | 62.4–75.6% | 127/183 | 8 | report only | — |
| nsr | specificity | 98.83% | 98.4–99.1% | 3647/3690 | 50 | 99% | ❌ |
| other_nonshock | specificity | 99.88% | 99.6–100.0% | 1718/1720 | 16 | 95% | ✅ |
| asystole | specificity | 95.65% | 89.3–98.3% | 88/92 | 6 | 95% | ✅ |

Outer-fold thresholds: 0.902, 0.886, 0.835, 0.858, 0.865

### `baseline_vf_leak_only` — AUC 0.9656

| Category | Metric | Value | 95% CI (Wilson) | k/n | Records | AHA goal | Meets (point) |
|---|---|---:|---|---:|---:|---:|:---:|
| coarse_vf | sensitivity | 44.93% | 41.4–48.5% | 337/750 | 41 | 90% | ❌ |
| fine_vf | sensitivity | 0.00% | 0.0–56.2% | 0/3 | 1 | report only | — |
| rapid_vt | sensitivity | 61.02% | 56.3–65.5% | 263/431 | 16 | 75% | ❌ |
| other_vt | sensitivity | 36.07% | 29.5–43.2% | 66/183 | 8 | report only | — |
| nsr | specificity | 95.80% | 95.1–96.4% | 3535/3690 | 50 | 99% | ❌ |
| other_nonshock | specificity | 100.00% | 99.8–100.0% | 1720/1720 | 16 | 95% | ✅ |
| asystole | specificity | 100.00% | 96.0–100.0% | 92/92 | 6 | 95% | ✅ |

Outer-fold thresholds: 0.787, 0.939, 0.914, 0.943, 0.926

## Limitations

- Windows from the same record are correlated; Wilson CIs treat windows as independent and are therefore optimistic.
- 'Rapid VT' uses a spectral dominant-frequency proxy (≥2.5 Hz ≈ ≥150 bpm), not annotated heart rate.
- CUDB/VFDB are small, old (1980s–90s), Holter/monitor recordings, not AED pad ECG; no CPR artefact.
- Only channel 0 is used; no external test set. Results are hypothesis-generating only.
