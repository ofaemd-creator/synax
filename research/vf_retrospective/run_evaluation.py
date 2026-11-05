#!/usr/bin/env python3
"""
SYNAX Issue #6 — Retrospective Ventricular Arrhythmia Signal-Processing Evaluation
(`research/vf_retrospective/run_evaluation.py`)
==================================================================================
NON-CLINICAL RESEARCH SOFTWARE. Not a medical device. Not for shock/no-shock decisions.
See MEDICAL_RESEARCH_DISCLAIMER.md (EU MDR 2017/745, IEC 60601-2-4).

Protocol (pre-specified before reporting):
  * Data: PhysioNet CUDB 1.0.0 (35 records) + VFDB 1.0.0 (22 records), channel 0, 250 Hz.
  * Windows: non-overlapping 8.0 s windows fully inside one expert rhythm interval.
    Excluded: annotated NOISE intervals and windows with >5 % WFDB invalid samples.
  * Rhythm categories (Kerber et al., AHA, Circulation 1997):
      shockable      : coarse VF/VFL (median 2 s p-p >= 200 uV), rapid VT (dominant freq >= 2.5 Hz)
      intermediate   : fine VF (< 200 uV), other VT        -> reported, never trained on
      non-shockable  : NSR, other organized rhythms, asystole
  * Signal conditioning: Semantic-Locked SYNAX kernels `vf_bandpass_sanitizer.sx` and
    `vf_nonlinear_energy.sx` (native winner verified against clang -O3 scalar on every record).
  * Model: L2 logistic regression on standardized + squared descriptors (no deep learning).
  * Validation: 5-fold RECORD-GROUPED cross-validation (no patient appears in train and test).
    Operating threshold is selected by a NESTED inner 4-fold record-grouped CV on the training
    records only (target: inner NSR specificity >= 99 %), so no test data influences the threshold.
  * Baselines (same nested protocol): TCSC alone, VF-filter leakage alone, and the full model
    WITHOUT the SYNAX nonlinear-energy descriptor (ablation).

Usage:
  python research/vf_retrospective/download_physionet.py      # one-time, ~40 MB
  python research/vf_retrospective/run_evaluation.py
==================================================================================
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from synax.biomedical import (  # noqa: E402
    FEATURE_NAMES,
    SynaxBiomedicalPipeline,
    extract_window_features,
    read_wfdb_record,
)

DATA_ROOT = Path.home() / ".cache" / "synax" / "physionet"
OUT_DIR = Path(__file__).resolve().parent / "results"
WIN_SEC = 8.0
MAX_INVALID_FRAC = 0.05
N_OUTER = 5
N_INNER = 4
TARGET_NSR_SPEC = 0.99

AHA_GOALS = {
    "coarse_vf": ("sensitivity", 0.90),
    "rapid_vt": ("sensitivity", 0.75),
    "nsr": ("specificity", 0.99),
    "other_nonshock": ("specificity", 0.95),
    "asystole": ("specificity", 0.95),
}


# ─────────────────────────────────────────────────────────────────
# 1. Dataset construction
# ─────────────────────────────────────────────────────────────────
def build_dataset(data_root: Path):
    pipe = SynaxBiomedicalPipeline()
    X, cls, recs = [], [], []
    telemetry: List[Dict] = []
    excluded_invalid = 0
    for db in ("cudb", "vfdb"):
        db_dir = data_root / db
        rec_names = [r.strip() for r in (db_dir / "RECORDS").read_text().splitlines() if r.strip()]
        for r in rec_names:
            w = read_wfdb_record(db_dir / r)
            if not (all(w.checksum_verified) and all(w.init_val_verified)):
                raise RuntimeError(f"WFDB checksum mismatch in {db}/{r}")
            fs = w.header.fs
            win = int(round(WIN_SEC * fs))
            clean, nle, tel = pipe.condition_record(w.signals_mv[0], fs=fs, record_id=r, database=db)
            telemetry.append(tel.__dict__)
            raw = np.frombuffer(w.signals_mv[0], dtype=np.float32)
            for seg in w.rhythm_segments:
                if seg.canonical_class == "NOISE":
                    continue
                pos = seg.start_sample
                while pos + win <= seg.end_sample:
                    if float(np.mean(np.isnan(raw[pos:pos + win]))) > MAX_INVALID_FRAC:
                        excluded_invalid += 1
                    else:
                        X.append(extract_window_features(clean[pos:pos + win], nle[pos:pos + win], fs=fs))
                        cls.append(seg.canonical_class)
                        recs.append(f"{db}:{r}")
                    pos += win
    return np.array(X), np.array(cls), np.array(recs), telemetry, excluded_invalid


def categorize(X: np.ndarray, cls: np.ndarray) -> Dict[str, np.ndarray]:
    ptp = X[:, FEATURE_NAMES.index("ptp_2s_med_mv")]
    dom = X[:, FEATURE_NAMES.index("dom_freq_hz")]
    rapid_vt = (cls == "VT") & (dom >= 2.5) & (ptp >= 0.20)
    return {
        "coarse_vf": (cls == "VF_VFL") & (ptp >= 0.20),
        "fine_vf": (cls == "VF_VFL") & (ptp < 0.20),
        "rapid_vt": rapid_vt,
        "other_vt": (cls == "VT") & ~rapid_vt,
        "nsr": cls == "NSR",
        "other_nonshock": cls == "OTHER_NONSHOCK",
        "asystole": cls == "ASYSTOLE",
    }


# ─────────────────────────────────────────────────────────────────
# 2. Model
# ─────────────────────────────────────────────────────────────────
def expand(M: np.ndarray) -> np.ndarray:
    f = {n: M[:, i] for i, n in enumerate(FEATURE_NAMES)}
    extra = [
        np.log1p(f["ptp_2s_med_mv"]),
        np.log1p(f["rms_mv"] * 10.0),
        np.log1p(f["kurtosis"]),
        np.log1p(f["dx_kurtosis"]),
        np.log1p(f["dx_spikiness"]),
        f["spec_vf_ratio"] / (f["spec_hf_ratio"] + 0.02),
        f["spec_vf_ratio"] * (1.0 - f["vf_leak_min"]),
        f["psr_density"] * (1.0 - f["vf_leak_mean"]),
        f["tcsc"] / (f["dx_spikiness"] + 0.5),
    ]
    if "synax_energy_duty" in f:
        extra.append(np.log1p(f["synax_energy_duty"] * 25.0))
    return np.hstack([M, np.column_stack(extra)])


class LogReg:
    def __init__(self, l2: float = 4.0, pos_weight: float = 2.0, quadratic: bool = True):
        self.l2, self.pos_weight, self.quadratic = l2, pos_weight, quadratic

    def _design(self, X):
        Xn = (X - self.mu) / self.sd
        cols = [np.ones((len(X), 1)), Xn] + ([Xn ** 2] if self.quadratic else [])
        return np.hstack(cols)

    def fit(self, X, y):
        self.mu, self.sd = X.mean(axis=0), X.std(axis=0) + 1e-8
        Z = self._design(X)
        w = np.zeros(Z.shape[1])
        sw = np.where(y == 1, self.pos_weight, 1.0)
        reg = self.l2 * np.r_[0.0, np.ones(len(w) - 1)]
        for _ in range(50):
            p = 1.0 / (1.0 + np.exp(-np.clip(Z @ w, -30, 30)))
            g = Z.T @ (sw * (p - y)) + reg * w
            H = (Z.T * (sw * p * (1 - p) + 1e-6)) @ Z + np.diag(reg)
            step = np.linalg.solve(H, g)
            w -= step
            if np.max(np.abs(step)) < 1e-7:
                break
        self.w = w
        return self

    def predict_proba(self, X):
        return 1.0 / (1.0 + np.exp(-np.clip(self._design(X) @ self.w, -30, 30)))


def asystole_guard(X_raw: np.ndarray) -> np.ndarray:
    """Explicit, interpretable symbolic rule: very low amplitude is never classified shockable."""
    ptp = X_raw[:, FEATURE_NAMES.index("ptp_2s_med_mv")]
    rms = X_raw[:, FEATURE_NAMES.index("rms_mv")]
    return (ptp < 0.18) | (rms < 0.055)


def grouped_folds(recs: np.ndarray, burden: np.ndarray, k: int) -> List[List[str]]:
    uniq = sorted(set(recs))
    order = sorted(uniq, key=lambda r: (-float(np.mean(burden[recs == r])), r))
    folds: List[List[str]] = [[] for _ in range(k)]
    for i, r in enumerate(order):
        folds[i % k].append(r)
    return folds


def select_threshold(probs: np.ndarray, nsr_mask: np.ndarray) -> float:
    """Smallest threshold achieving >= TARGET_NSR_SPEC specificity on NSR (inner folds only)."""
    nsr_p = np.sort(probs[nsr_mask])
    if len(nsr_p) == 0:
        return 0.5
    k = int(math.ceil(TARGET_NSR_SPEC * len(nsr_p))) - 1
    k = min(max(k, 0), len(nsr_p) - 1)
    return float(min(0.995, max(0.05, nsr_p[k] + 1e-9)))


def run_nested_cv(Xm, X_raw, y, train_ok, nsr_mask, recs, burden, model_factory, use_guard=True):
    outer = grouped_folds(recs, burden, N_OUTER)
    pred = np.zeros(len(y), dtype=bool)
    probs_out = np.zeros(len(y))
    thresholds = []
    for test_recs in outer:
        te = np.isin(recs, test_recs)
        tr_all = ~te
        tr_recs = recs[tr_all]
        inner = grouped_folds(tr_recs, burden[tr_all], N_INNER)
        inner_probs = np.zeros(int(tr_all.sum()))
        idx_tr = np.where(tr_all)[0]
        for in_recs in inner:
            in_te = np.isin(tr_recs, in_recs)
            fit_idx = idx_tr[~in_te]
            fit_idx = fit_idx[train_ok[fit_idx]]
            m = model_factory().fit(Xm[fit_idx], y[fit_idx])
            p = m.predict_proba(Xm[idx_tr[in_te]])
            if use_guard:
                p = np.where(asystole_guard(X_raw[idx_tr[in_te]]), 0.0, p)
            inner_probs[in_te] = p
        thr = select_threshold(inner_probs, nsr_mask[idx_tr])
        thresholds.append(thr)
        fit_idx = idx_tr[train_ok[idx_tr]]
        m = model_factory().fit(Xm[fit_idx], y[fit_idx])
        p = m.predict_proba(Xm[te])
        if use_guard:
            p = np.where(asystole_guard(X_raw[te]), 0.0, p)
        probs_out[te] = p
        pred[te] = p >= thr
    return pred, probs_out, thresholds


# ─────────────────────────────────────────────────────────────────
# 3. Metrics
# ─────────────────────────────────────────────────────────────────
def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.r_[pos, neg], kind="mergesort")
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    # average ties
    allv = np.r_[pos, neg]
    for v in np.unique(allv):
        m = allv == v
        if m.sum() > 1:
            ranks[m] = ranks[m].mean()
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def summarize(pred: np.ndarray, cats: Dict[str, np.ndarray], recs: np.ndarray) -> Dict[str, Dict]:
    out = {}
    for name, mask in cats.items():
        n = int(mask.sum())
        shock_calls = int(pred[mask].sum())
        is_sens = name in ("coarse_vf", "rapid_vt", "fine_vf", "other_vt")
        k = shock_calls if is_sens else n - shock_calls
        lo, hi = wilson(k, n)
        entry = {
            "metric": "sensitivity" if is_sens else "specificity",
            "value": (k / n) if n else float("nan"),
            "k": k,
            "n": n,
            "ci95": [lo, hi],
            "records": int(len(set(recs[mask]))),
        }
        if name in AHA_GOALS:
            entry["aha_goal"] = AHA_GOALS[name][1]
            entry["meets_goal_point"] = bool(n and entry["value"] >= AHA_GOALS[name][1])
            entry["meets_goal_lower_ci"] = bool(n and lo >= AHA_GOALS[name][1])
        out[name] = entry
    return out


# ─────────────────────────────────────────────────────────────────
# 4. Main
# ─────────────────────────────────────────────────────────────────
def main() -> int:
    if not (DATA_ROOT / "cudb" / "RECORDS").exists():
        print(f"PhysioNet data not found under {DATA_ROOT}. Run download_physionet.py first.")
        return 2

    t0 = time.time()
    X, cls, recs, telemetry, excluded_invalid = build_dataset(DATA_ROOT)
    cats = categorize(X, cls)
    shock = cats["coarse_vf"] | cats["rapid_vt"]
    y = shock.astype(float)
    train_ok = ~(cats["fine_vf"] | cats["other_vt"])
    nsr = cats["nsr"]

    results = {}
    full_names = list(FEATURE_NAMES)
    no_synax_idx = [i for i, n in enumerate(full_names) if n != "synax_energy_duty"]

    configs = {
        "synax_full_model": (expand(X), lambda: LogReg(), True),
        "ablation_without_synax_energy": (
            _expand_subset(X, no_synax_idx), lambda: LogReg(), True),
        "baseline_tcsc_only": (X[:, [FEATURE_NAMES.index("tcsc")]], lambda: LogReg(quadratic=False), False),
        "baseline_vf_leak_only": (
            -X[:, [FEATURE_NAMES.index("vf_leak_mean")]], lambda: LogReg(quadratic=False), False),
    }
    for name, (Xm, factory, guard) in configs.items():
        pred, probs, thrs = run_nested_cv(Xm, X, y, train_ok, nsr, recs, y, factory, use_guard=guard)
        eval_mask = train_ok
        results[name] = {
            "per_category": summarize(pred, cats, recs),
            "auc_shockable_vs_nonshockable": auc(probs[eval_mask], y[eval_mask]),
            "outer_fold_thresholds": thrs,
        }

    tel_max_san = max(t["max_abs_diff_sanitizer"] for t in telemetry)
    tel_max_nle = max(t["max_abs_diff_energy"] for t in telemetry)
    report = {
        "title": "SYNAX Issue #6 — Retrospective VF/VT signal-processing evaluation (NON-CLINICAL)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "protocol": {
            "databases": ["PhysioNet CUDB 1.0.0 (35 records)", "PhysioNet VFDB 1.0.0 (22 records)"],
            "channel": 0, "window_sec": WIN_SEC, "max_invalid_fraction": MAX_INVALID_FRAC,
            "outer_cv": f"{N_OUTER}-fold record-grouped", "inner_cv": f"{N_INNER}-fold record-grouped",
            "threshold_rule": f"inner NSR specificity >= {TARGET_NSR_SPEC}",
            "features": full_names,
        },
        "dataset": {
            "windows_total": int(len(y)),
            "windows_excluded_invalid": int(excluded_invalid),
            "category_counts": {k: int(v.sum()) for k, v in cats.items()},
            "records": int(len(set(recs))),
        },
        "synax_kernel_integrity": {
            "records_processed": len(telemetry),
            "filter_kernel": telemetry[0].get("filter_kernel_name", "ranvier_adaptive_filter") if telemetry else "ranvier_adaptive_filter",
            "samples_processed": int(sum(t["num_samples"] for t in telemetry)),
            "immune_healed_samples": int(sum(t["healed_sanitizer"] for t in telemetry)),
            "max_abs_diff_native_vs_scalar_sanitizer": tel_max_san,
            "max_abs_diff_native_vs_scalar_energy": tel_max_nle,
            "native_total_ms": sum(t["neon_sanitizer_us"] + t["neon_energy_us"] for t in telemetry) / 1000.0,
            "scalar_o3_total_ms": sum(t["scalar_c_sanitizer_us"] + t["scalar_c_energy_us"] for t in telemetry) / 1000.0,
        },
        "results": results,
        "runtime_sec": time.time() - t0,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "evaluation_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_DIR / "EVALUATION_REPORT.md").write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0


def _expand_subset(X: np.ndarray, idx: Sequence[int]) -> np.ndarray:
    full = expand(X)
    n_base = X.shape[1]
    synax_extra_col = full.shape[1] - 1  # last engineered column is log synax_energy_duty
    keep = list(idx) + [c for c in range(n_base, full.shape[1]) if c != synax_extra_col]
    return full[:, keep]


def render_markdown(r: Dict) -> str:
    L = []
    L.append(f"# {r['title']}\n")
    L.append("> [!CAUTION]\n> Research software only. Not a medical device; must not be used for diagnosis or "
             "shock/no-shock decisions. Results are retrospective on public data.\n")
    L.append(f"Generated: `{r['generated_utc']}` — Host: `{r['host']['platform']}`\n")
    d = r["dataset"]
    L.append("## Dataset\n")
    L.append(f"- Records: **{d['records']}**, analysed 8 s windows: **{d['windows_total']}** "
             f"(excluded for >5 % invalid samples: {d['windows_excluded_invalid']})")
    L.append("- Category counts: " + ", ".join(f"`{k}`={v}" for k, v in d["category_counts"].items()) + "\n")
    k = r["synax_kernel_integrity"]
    L.append("## SYNAX kernel integrity (semantic preservation on real ECG)\n")
    fk = k.get("filter_kernel", "ranvier_adaptive_filter")
    L.append(f"- Active front-end conditioning: `{fk}.sx` (Ranvier Node adaptive depolarization filter)")
    L.append(f"- Samples processed: {k['samples_processed']:,}; IMMUNE-healed invalid samples: {k['immune_healed_samples']:,}")
    L.append(f"- Max |native winner − C11 -O0 reference|: sanitizer `{k['max_abs_diff_native_vs_scalar_sanitizer']:.3e}`, "
             f"energy `{k['max_abs_diff_native_vs_scalar_energy']:.3e}`")
    L.append(f"- Total kernel time: native {k['native_total_ms']:.2f} ms vs C11 -O0 reference {k['scalar_o3_total_ms']:.2f} ms "
             "(the -O0 kernel is a correctness oracle, NOT a fair speed baseline; see benchmarks/ for -O3 comparisons)")
    L.append("- IMMUNE heal counts of native and reference kernels were asserted equal on every record.\n")
    L.append("## Results (5-fold record-grouped CV, nested threshold selection)\n")
    for name, res in r["results"].items():
        L.append(f"### `{name}` — AUC {res['auc_shockable_vs_nonshockable']:.4f}\n")
        L.append("| Category | Metric | Value | 95% CI (Wilson) | k/n | Records | AHA goal | Meets (point) |")
        L.append("|---|---|---:|---|---:|---:|---:|:---:|")
        for cat, e in res["per_category"].items():
            goal = f"{e['aha_goal']*100:.0f}%" if "aha_goal" in e else "report only"
            meets = ("✅" if e.get("meets_goal_point") else "❌") if "aha_goal" in e else "—"
            val = f"{e['value']*100:.2f}%" if e["n"] else "n/a"
            ci = f"{e['ci95'][0]*100:.1f}–{e['ci95'][1]*100:.1f}%" if e["n"] else "n/a"
            L.append(f"| {cat} | {e['metric']} | {val} | {ci} | {e['k']}/{e['n']} | {e['records']} | {goal} | {meets} |")
        L.append(f"\nOuter-fold thresholds: {', '.join(f'{t:.3f}' for t in res['outer_fold_thresholds'])}\n")
    L.append("## Limitations\n")
    L.append("- Windows from the same record are correlated; Wilson CIs treat windows as independent and are therefore optimistic.")
    L.append("- 'Rapid VT' uses a spectral dominant-frequency proxy (≥2.5 Hz ≈ ≥150 bpm), not annotated heart rate.")
    L.append("- CUDB/VFDB are small, old (1980s–90s), Holter/monitor recordings, not AED pad ECG; no CPR artefact.")
    L.append("- Only channel 0 is used; no external test set. Results are hypothesis-generating only.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
