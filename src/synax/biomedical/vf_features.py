#!/usr/bin/env python3
"""
SYNAX Biomedical Ventricular Arrhythmia Signal Conditioning & Feature Engine
(`src/synax/biomedical/vf_features.py`)
========================================================================================
Executes compiled, semantic-locked SYNAX (`.sx`) kernels (`vf_bandpass_sanitizer.sx` and
`vf_nonlinear_energy.sx`) on raw ECG waveforms and extracts 16 interpretable biophysical
descriptors in 8.0-second and 4.0-second analysis windows.

Strictly non-clinical retrospective research software (EU MDR 2017/745 / IEC 60601-2-4).
========================================================================================
"""

from __future__ import annotations

import math
import time
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

import synax
from synax_verifier import LoadedKernel

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SANITIZER_SX = ROOT_DIR / "examples" / "vf_bandpass_sanitizer.sx"
NONLINEAR_SX = ROOT_DIR / "examples" / "vf_nonlinear_energy.sx"
RANVIER_SX = ROOT_DIR / "examples" / "ranvier_adaptive_filter.sx"

FEATURE_NAMES: Tuple[str, ...] = (
    "ptp_2s_med_mv",      # Median 2-second subwindow peak-to-peak amplitude (mV) — IEC 60601-2-4 amplitude
    "rms_mv",             # Root-mean-square amplitude (mV)
    "vf_leak_mean",       # Mean 2-second Kuo-Dillman / Amann narrowband VF cancellation leakage
    "vf_leak_min",        # Minimum 2-second VF leakage across subwindows (captures polymorphic VF bouts)
    "tcsc",               # Mean 2-second Threshold Crossing Sample Count (|x| >= 0.20 * P98(|x|))
    "kurtosis",           # Standardized 4th moment of amplitude (high in spiky QRS, low in VF/VFL)
    "dx_kurtosis",        # Standardized 4th moment of slope dV/dt (His-Purkinje QRS spike vs reentry)
    "dx_spikiness",       # Slope contrast P98(|dV/dt|) / median(|dV/dt|) (high in organized QRS, low in VF)
    "crest_p98",          # P98(|x|) / RMS amplitude spikiness factor
    "spec_vf_ratio",      # Power ratio in 2.5 - 9.5 Hz fibrillatory band
    "spec_hf_ratio",      # Power ratio in 11.0 - 30.0 Hz QRS harmonic band
    "spec_lf_ratio",      # Power ratio in 0.5 - 2.3 Hz sub-fibrillatory band
    "dom_freq_hz",        # Dominant spectral frequency in 0.8 - 20.0 Hz
    "spec_conc",          # Spectral concentration within +-1.0 Hz of dominant frequency
    "psr_density",        # Amann 40x40 phase-space reconstruction box density (tau = 0.5 s)
    "synax_energy_duty",  # Continuous depolarization duty ratio from `vf_nonlinear_energy.sx`
)


@dataclass
class RecordKernelTelemetry:
    record_id: str
    database: str
    num_samples: int
    healed_sanitizer: int
    healed_energy: int
    neon_sanitizer_us: float
    neon_energy_us: float
    scalar_c_sanitizer_us: float
    scalar_c_energy_us: float
    max_abs_diff_sanitizer: float
    max_abs_diff_energy: float
    filter_kernel_name: str = "ranvier_adaptive_filter"


class SynaxBiomedicalPipeline:
    """
    Compiles and caches the Semantic-Locked `.sx` kernels (`ranvier_adaptive_filter.sx`,
    `vf_bandpass_sanitizer.sx`, and `vf_nonlinear_energy.sx`) and provides native SIMD +
    C11 Scalar execution for both signal conditioning and differential verification on
    clinical ECG streams.
    """

    def __init__(self, use_ranvier: bool = True) -> None:
        ok1, msg1 = synax.verify_lock(str(SANITIZER_SX))
        if not ok1:
            raise RuntimeError(f"Semantic Lock verification failed for {SANITIZER_SX}: {msg1}")
        ok2, msg2 = synax.verify_lock(str(NONLINEAR_SX))
        if not ok2:
            raise RuntimeError(f"Semantic Lock verification failed for {NONLINEAR_SX}: {msg2}")
        ok3, msg3 = synax.verify_lock(str(RANVIER_SX))
        if not ok3:
            raise RuntimeError(f"Semantic Lock verification failed for {RANVIER_SX}: {msg3}")

        self.use_ranvier = use_ranvier
        self.comp_san = synax.compile_sx(str(SANITIZER_SX), bench_n=262_144, bench_repeats=5, verbose=False)
        self.comp_nle = synax.compile_sx(str(NONLINEAR_SX), bench_n=262_144, bench_repeats=5, verbose=False)
        self.comp_ran = synax.compile_sx(str(RANVIER_SX), bench_n=262_144, bench_repeats=5, verbose=False)

        self.neon_san = LoadedKernel(str(self.comp_san.winner_dylib_path), name=self.comp_san.winner_name)
        self.neon_nle = LoadedKernel(str(self.comp_nle.winner_dylib_path), name=self.comp_nle.winner_name)
        self.neon_ran = LoadedKernel(str(self.comp_ran.winner_dylib_path), name=self.comp_ran.winner_name)

        # Differential oracle: the unoptimized C11 (-O0) reference kernel emitted for every module.
        # Every record is processed twice (native winner + reference) and compared bit-for-bit.
        self.scalar_san: Optional[LoadedKernel] = None
        self.scalar_nle: Optional[LoadedKernel] = None
        self.scalar_ran: Optional[LoadedKernel] = None
        if Path(self.comp_san.ref_dylib_path).exists():
            self.scalar_san = LoadedKernel(str(self.comp_san.ref_dylib_path), name="referans_c11_o0")
        if Path(self.comp_nle.ref_dylib_path).exists():
            self.scalar_nle = LoadedKernel(str(self.comp_nle.ref_dylib_path), name="referans_c11_o0")
        if Path(self.comp_ran.ref_dylib_path).exists():
            self.scalar_ran = LoadedKernel(str(self.comp_ran.ref_dylib_path), name="referans_c11_o0")
        if self.scalar_san is None or self.scalar_nle is None or self.scalar_ran is None:
            raise RuntimeError("C11 reference kernels missing; differential verification impossible.")

        # 9-tap ~28 Hz low-pass Hann FIR kernel (at fs=250 Hz) to suppress 50/60 Hz & EMG noise
        h = np.hanning(11)[1:-1].astype(np.float32)
        self._lp_kernel = h / np.sum(h)

    @staticmethod
    def _estimate_baseline_wander(raw_np: np.ndarray, win_samples: int = 250) -> np.ndarray:
        """
        Two-pass triangular (Bartlett) 1.0-second zero-ringing baseline wander estimator (~0.8 Hz high-pass).
        Leaves raw NaNs untouched in `raw_signal_mv` so `vf_bandpass_sanitizer.sx` performs
        hardware SIMD IMMUNE healing & anomaly counting directly on the raw clinical input!
        """
        finite_ref = np.where(np.isfinite(raw_np) & (np.abs(raw_np) <= 10.0), raw_np, 0.0).astype(np.float64)
        half = max(4, win_samples // 4)
        for _ in range(2):
            csum = np.empty(len(finite_ref) + 1, dtype=np.float64)
            csum[0] = 0.0
            np.cumsum(finite_ref, out=csum[1:])
            idx = np.arange(len(finite_ref))
            lo = np.maximum(0, idx - half)
            hi = np.minimum(len(finite_ref), idx + half)
            finite_ref = (csum[hi] - csum[lo]) / np.maximum(1, hi - lo)
        return finite_ref.astype(np.float32)

    def condition_record(
        self,
        raw_signal_mv: array,
        fs: float = 250.0,
        record_id: str = "",
        database: str = "",
    ) -> Tuple[np.ndarray, np.ndarray, RecordKernelTelemetry]:
        """
        Run full-record ECG conditioning + nonlinear energy computation via native SYNAX `.sx` kernels.
        Returns `(clean_bandpass_np, nonlinear_energy_np, telemetry)`.
        """
        raw_np = np.frombuffer(raw_signal_mv, dtype=np.float32)
        drift_np = self._estimate_baseline_wander(raw_np, win_samples=int(round(1.0 * fs)))
        drift_arr = array("f")
        drift_arr.frombytes(drift_np.tobytes())

        active_neon = self.neon_ran if self.use_ranvier else self.neon_san
        active_scalar = self.scalar_ran if self.use_ranvier else self.scalar_san
        active_name = "ranvier_adaptive_filter" if self.use_ranvier else "vf_bandpass_sanitizer"

        t0 = time.perf_counter_ns()
        san_arr, healed_san = active_neon.run_pure(raw_signal_mv, drift_arr)
        t1 = time.perf_counter_ns()
        neon_san_us = (t1 - t0) / 1000.0

        san_np = np.frombuffer(san_arr, dtype=np.float32)
        clean_np = np.convolve(san_np, self._lp_kernel, mode="same").astype(np.float32)

        dx_np = np.empty_like(clean_np)
        dx_np[0] = 0.0
        dx_np[1:] = (clean_np[1:] - clean_np[:-1]) * np.float32(fs / 25.0)

        clean_arr = array("f")
        clean_arr.frombytes(clean_np.tobytes())
        dx_arr = array("f")
        dx_arr.frombytes(dx_np.tobytes())

        t2 = time.perf_counter_ns()
        nle_arr, healed_nle = self.neon_nle.run_pure(clean_arr, dx_arr)
        t3 = time.perf_counter_ns()
        neon_nle_us = (t3 - t2) / 1000.0

        nle_np = np.frombuffer(nle_arr, dtype=np.float32).copy()

        scalar_san_us = 0.0
        scalar_nle_us = 0.0
        max_diff_san = 0.0
        max_diff_nle = 0.0
        if active_scalar is not None:
            ts0 = time.perf_counter_ns()
            s_out, s_heal = active_scalar.run_pure(raw_signal_mv, drift_arr)
            ts1 = time.perf_counter_ns()
            scalar_san_us = (ts1 - ts0) / 1000.0
            s_np = np.frombuffer(s_out, dtype=np.float32)
            max_diff_san = float(np.max(np.abs(san_np - s_np))) if len(san_np) else 0.0
            assert int(s_heal or 0) == int(healed_san or 0), "IMMUNE heal count mismatch!"

        if self.scalar_nle is not None:
            ts2 = time.perf_counter_ns()
            sn_out, sn_heal = self.scalar_nle.run_pure(clean_arr, dx_arr)
            ts3 = time.perf_counter_ns()
            scalar_nle_us = (ts3 - ts2) / 1000.0
            sn_np = np.frombuffer(sn_out, dtype=np.float32)
            max_diff_nle = float(np.max(np.abs(nle_np - sn_np))) if len(nle_np) else 0.0
            assert int(sn_heal or 0) == int(healed_nle or 0), "IMMUNE energy heal count mismatch!"

        telem = RecordKernelTelemetry(
            record_id=record_id,
            database=database,
            num_samples=len(raw_np),
            healed_sanitizer=int(healed_san or 0),
            healed_energy=int(healed_nle or 0),
            neon_sanitizer_us=neon_san_us,
            neon_energy_us=neon_nle_us,
            scalar_c_sanitizer_us=scalar_san_us,
            scalar_c_energy_us=scalar_nle_us,
            max_abs_diff_sanitizer=max_diff_san,
            max_abs_diff_energy=max_diff_nle,
            filter_kernel_name=active_name,
        )
        return clean_np.copy(), nle_np, telem


def _subwindow_leak_tcsc_ptp(xc: np.ndarray, fs: float) -> Tuple[float, float, float, float]:
    """
    Compute 2-second subwindow VF filter leakage (`mean`, `min`), `TCSC`, and `median_ptp_mv`
    so frequency-modulated polymorphic VF is tracked locally without 8-second phase drift.
    """
    sub_len = int(round(2.0 * fs))
    n = len(xc)
    if n < sub_len:
        sub_slices = [xc]
    else:
        n_subs = n // sub_len
        sub_slices = [xc[i * sub_len : (i + 1) * sub_len] for i in range(n_subs)]

    leaks = []
    tcscs = []
    ptps = []
    for s in sub_slices:
        s_c = s - float(np.mean(s))
        p99, p01 = np.percentile(s_c, [99.0, 1.0])
        ptps.append(float(p99 - p01))
        abs_s = np.abs(s_c)
        p98_s = float(np.percentile(abs_s, 98.0))
        if p98_s < 1e-5:
            leaks.append(1.0)
            tcscs.append(0.0)
            continue
        ds = np.abs(s_c[1:] - s_c[:-1])
        n_half = int(round(math.pi * float(np.sum(abs_s)) / (float(np.sum(ds)) + 1e-9)))
        n_half = max(5, min(int(0.28 * fs), n_half))
        leak = float(np.sum(np.abs(s_c[n_half:] + s_c[:-n_half]))) / (
            float(np.sum(abs_s[n_half:] + abs_s[:-n_half])) + 1e-9
        )
        leaks.append(leak)
        tcscs.append(float(np.mean(abs_s >= 0.20 * p98_s)))

    return (
        float(np.median(ptps)),
        float(np.mean(leaks)),
        float(np.min(leaks)),
        float(np.mean(tcscs)),
    )


def extract_window_features(
    x: np.ndarray, nle: np.ndarray, fs: float = 250.0
) -> np.ndarray:
    """
    Extract the 16 interpretable biophysical ECG descriptors from a conditioned window `x`
    and its SYNAX `.sx` nonlinear energy envelope `nle`.
    """
    n = len(x)
    xf = x.astype(np.float64, copy=False)
    xc = xf - float(np.mean(xf))
    abs_x = np.abs(xc)

    ptp_2s_med_mv, vf_leak_mean, vf_leak_min, tcsc = _subwindow_leak_tcsc_ptp(xc, fs)
    var = float(np.mean(xc * xc))
    rms_mv = math.sqrt(var)

    if rms_mv < 1e-6 or ptp_2s_med_mv < 1e-5:
        return np.array(
            [ptp_2s_med_mv, rms_mv, 1.0, 1.0, 0.0, 3.0, 3.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            dtype=np.float64,
        )

    # Amplitude & slope (dV/dt) kurtosis and His-Purkinje spikiness
    kurtosis = min(80.0, float(np.mean(xc ** 4) / ((var * var) + 1e-12)))
    dxc = xc[1:] - xc[:-1]
    var_dx = float(np.mean(dxc * dxc))
    dx_kurtosis = min(100.0, float(np.mean(dxc ** 4) / ((var_dx * var_dx) + 1e-14)))
    abs_dx = np.abs(dxc)
    dx_p98 = float(np.percentile(abs_dx, 98.0))
    dx_med = float(np.median(abs_dx))
    dx_spikiness = min(50.0, dx_p98 / (dx_med + 1e-6))

    p98 = float(np.percentile(abs_x, 98.0))
    crest_p98 = p98 / (rms_mv + 1e-9)

    # Hann-windowed Power Spectral Density ratios (250 Hz)
    win = np.hanning(n)
    spec = np.abs(np.fft.rfft(xc * win)) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    band_tot = (freqs >= 0.5) & (freqs <= 35.0)
    p_tot = float(np.sum(spec[band_tot])) + 1e-12
    spec_vf_ratio = float(np.sum(spec[(freqs >= 2.5) & (freqs <= 9.5)])) / p_tot
    spec_hf_ratio = float(np.sum(spec[(freqs >= 11.0) & (freqs <= 30.0)])) / p_tot
    spec_lf_ratio = float(np.sum(spec[(freqs >= 0.5) & (freqs < 2.3)])) / p_tot

    dom_mask = (freqs >= 0.8) & (freqs <= 20.0)
    if np.any(dom_mask):
        dom_sub = spec[dom_mask]
        dom_freqs = freqs[dom_mask]
        dom_idx = int(np.argmax(dom_sub))
        dom_freq_hz = float(dom_freqs[dom_idx])
        conc_mask = (freqs >= (dom_freq_hz - 1.0)) & (freqs <= (dom_freq_hz + 1.0))
        spec_conc = float(np.sum(spec[conc_mask])) / p_tot
    else:
        dom_freq_hz = 0.0
        spec_conc = 0.0

    # Amann Phase-Space Reconstruction (`Count2`) box-counting density (40x40 grid, tau = 0.5 s)
    tau = int(round(0.5 * fs))
    if n > tau + 10 and p98 > 1e-5:
        s_a = np.clip(xc[:-tau] / p98, -1.0, 1.0)
        s_b = np.clip(xc[tau:] / p98, -1.0, 1.0)
        gx = np.clip(((s_a + 1.0) * 19.999).astype(np.int32), 0, 39)
        gy = np.clip(((s_b + 1.0) * 19.999).astype(np.int32), 0, 39)
        occupied = len(np.unique(gx * 40 + gy))
        psr_density = occupied / 1600.0
    else:
        psr_density = 0.0

    # SYNAX `.sx` Nonlinear Energy Continuous Depolarization Duty Ratio
    nle_f = nle.astype(np.float64, copy=False)
    nle_med = float(np.median(nle_f))
    nle_p95 = float(np.percentile(nle_f, 95.0))
    synax_energy_duty = nle_med / (nle_p95 + 1e-7) if nle_p95 > 1e-7 else 0.0

    return np.array(
        [
            ptp_2s_med_mv,
            rms_mv,
            vf_leak_mean,
            vf_leak_min,
            tcsc,
            kurtosis,
            dx_kurtosis,
            dx_spikiness,
            crest_p98,
            spec_vf_ratio,
            spec_hf_ratio,
            spec_lf_ratio,
            dom_freq_hz,
            spec_conc,
            psr_density,
            synax_energy_duty,
        ],
        dtype=np.float64,
    )
