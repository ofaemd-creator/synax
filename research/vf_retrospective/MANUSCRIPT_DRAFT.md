# Retrospective Evaluation of a Semantically-Verified Adaptive Runtime for Ventricular Arrhythmia Signal Processing

**Manuscript draft v0.1 — SYNAX Issue #6** · Author: Ömer Faruk Aydın, MD · Status: *pre-submission draft, not peer reviewed*

> [!CAUTION]
> Non-clinical research. The described software is not a medical device and must not be used for diagnosis or defibrillation decisions (EU MDR 2017/745; IEC 60601-2-4). All numbers below are reproduced by `research/vf_retrospective/run_evaluation.py`; see `results/EVALUATION_REPORT.md`.

## Abstract (draft)

**Background.** Optimizing compilers and SIMD runtimes can silently change numerical behaviour, which is unacceptable in physiological signal processing. SYNAX is an open-source (Apache-2.0) kernel language whose compiler emits multiple native variants and accepts a variant only if it matches a reference implementation on a semantic test set (“Semantic Lock”).

**Objective.** (1) To test whether SYNAX-optimized kernels preserve semantics on real clinical ECG, including invalid ADC samples; (2) to report, honestly and with leakage-free validation, how an interpretable feature-based shockable-rhythm detector built on this runtime performs against AHA AED performance goals.

**Methods.** 57 public records (PhysioNet CUDB, n=35; VFDB, n=22; 250 Hz, channel 0) were read with a dependency-free WFDB reader whose per-channel 16-bit checksums were verified (79/79 channels). Two Semantic-Locked `.sx` kernels performed sanitation (invalid-sample healing, ±10 mV bound, baseline removal) and nonlinear-energy computation. Every record was processed by the selected native kernel (Apple M-series, NEON + multicore) and by the unoptimized C11 reference kernel. 6,869 non-overlapping 8-s windows were labelled per Kerber et al. (AHA 1997). An L2-regularised logistic model on 16 interpretable descriptors was evaluated with 5-fold record-grouped cross-validation; the operating threshold was chosen by a nested inner record-grouped CV targeting 99 % NSR specificity.

**Results.** Across 16,003,120 samples (35,662 invalid samples healed), native and reference outputs were bit-identical for the sanitizer and differed by at most 1.5·10⁻⁵ (absolute; output range 0–250) for the energy kernel, with identical heal counts on every record. The detector reached AUC 0.982; rapid-VT sensitivity 88.2 % (goal 75 %), other-non-shockable specificity 99.8 % (goal 95 %), asystole specificity 97.8 % (goal 95 %), NSR specificity 99.0 % (at, but not above, the 99 % goal), and coarse-VF sensitivity **73.5 %, failing the 90 % goal**. Removing the SYNAX nonlinear-energy descriptor did not change performance (AUC 0.9825), i.e. that descriptor added **no** measurable discriminative value. Single-feature baselines (TCSC, VF-filter leakage) were markedly worse (coarse-VF sensitivity 37.7 % and 44.9 %).

**Conclusions.** The runtime preserved semantics on real ECG, which is the primary engineering claim. The detector does **not** meet AHA coarse-VF goals under strict patient-wise validation and should be viewed as a transparent baseline, not a candidate device algorithm.

## 1. Contributions
1. A zero-dependency WFDB (Format 212/16/61, MIT annotation) reader with checksum verification and explicit mapping of WFDB invalid samples to IEEE-754 NaN.
2. Evidence that SIMD/multicore kernel selection under Semantic Lock preserves outputs on 16 M real ECG samples, including corrupted ones.
3. A leakage-free (record-grouped, nested-threshold) evaluation protocol with ablation and baselines, reported including negative results.

## 2. Methods (details)
- **Labels.** Rhythm intervals from `+` AUX labels and CUDB `[`/`]` markers; `~` with subtype −1 (unreadable) intervals excluded as noise. Coarse VF: median 2-s peak-to-peak ≥ 200 µV. Rapid VT: dominant frequency ≥ 2.5 Hz (≈150 bpm; spectral proxy). Fine VF and other VT are reported but never used for training.
- **Descriptors (16).** Amplitude (2-s median p-p, RMS), VF-filter leakage (mean/min over 2-s subwindows), TCSC, amplitude and slope kurtosis, slope spikiness, crest factor, three band-power ratios, dominant frequency, spectral concentration, phase-space box density, SYNAX energy duty ratio.
- **Model.** Logistic regression with linear + squared standardized terms and engineered ratios (L2 = 4, positive weight 2) plus an explicit symbolic asystole guard (p-p < 0.18 mV or RMS < 0.055 mV ⇒ non-shockable).
- **Validation.** Outer 5-fold record-grouped CV; threshold from inner 4-fold record-grouped CV on training records only.

## 3. Results
See `results/EVALUATION_REPORT.md` (auto-generated tables with Wilson 95 % CIs and record counts).

## 4. Limitations (must accompany any presentation)
- Window-level CIs ignore within-record correlation and are optimistic.
- Rapid-VT definition uses a spectral proxy instead of annotated rate.
- CUDB/VFDB are small, decades-old monitor/Holter recordings, not AED pad signals; no CPR artefact; single channel; no external test set.
- Only 3 fine-VF windows exist after amplitude labelling; no conclusion on fine VF is possible.
- The kernels evaluated are arithmetically simple; semantic preservation for transcendental-heavy kernels is covered separately by the SYNAX fuzz suite, not by this study.

## 5. Next steps (pre-registered here)
1. External validation on an independent database (e.g., AHA DB or MIT-BIH Arrhythmia for non-shockable specificity) without re-tuning.
2. Record-level bootstrap CIs.
3. CPR-artefact-contaminated evaluation before any further claims.
4. Report the energy descriptor as non-contributory unless a future pre-specified analysis shows otherwise.

## Data & code availability
Code: https://github.com/ofaemd-creator/synax (Apache-2.0). Data: PhysioNet CUDB 1.0.0 and VFDB 1.0.0 (ODC-By 1.0), downloaded by `download_physionet.py` with a SHA-256 manifest; not redistributed.

## References
1. Kerber RE, et al. Automatic external defibrillators for public access defibrillation: recommendations for specifying and reporting arrhythmia analysis algorithm performance. *Circulation* 1997;95:1677–1682.
2. Goldberger AL, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 2000;101:e215–e220.
3. Nolle FM, et al. CREI-GARD, a new concept in computerized arrhythmia monitoring systems. *Computers in Cardiology* 1986;13:515–518.
4. Greenwald SD. *Development and analysis of a ventricular fibrillation detector.* MIT, 1986.
5. Kuo S, Dillman R. Computer detection of ventricular fibrillation. *Computers in Cardiology* 1978:347–349.
6. Amann A, Tratnig R, Unterkofler K. Reliability of old and new ventricular fibrillation detection algorithms for automated external defibrillators. *BioMed Eng OnLine* 2005;4:60.
7. Amann A, et al. Detecting ventricular fibrillation by time-delay methods. *IEEE TBME* 2007;54:174–177.
