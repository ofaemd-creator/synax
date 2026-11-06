"""
SYNAX Step-by-Step IEEE-754 Debugger & Roofline Profiler (`src/synax/profiler_debugger.py`)
=============================================================================
Provides two developer diagnostics engines for `.sx` kernels:
  1. `SynaxDebugger`: Traces AST sub-expression evaluation node-by-node in
     exact IEEE-754 `binary32` (with hex bit patterns `0xXXXXXXXX`), tracks
     IMMUNE Shield interventions (`heal_inputs`, `zero_output`, `reject`,
     `input_abs_bound`, `output_clamp`), and cross-checks against native SIMD.
  2. `SynaxProfiler`: Profiles compiled candidate kernels across warm-cache
     distributions (median, IQR, P95, ns/elem, effective GB/s).
=============================================================================
"""

from __future__ import annotations

import ctypes
import math
import os
import statistics
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from synax_ir import ASTNode, SynaxIR, _f32, parse_sx
from synax_verifier import LoadedKernel


def f32_hex(val: float) -> str:
    """Return IEEE-754 binary32 bit pattern as `0xXXXXXXXX`."""
    vf = _f32(val) if not math.isnan(val) else float("nan")
    bits = struct.unpack("<I", struct.pack("<f", vf))[0]
    return f"0x{bits:08X}"


@dataclass
class TraceStep:
    step_id: int
    stage: str
    expression: str
    value_f32: float
    bits_hex: str
    note: str = ""


@dataclass
class ElementDebugReport:
    kernel_name: str
    ir_hash: str
    index: int
    raw_a: float
    raw_b: float
    healed_count: int
    final_ref_f32: float
    final_ref_hex: str
    native_f32: Optional[float] = None
    native_hex: Optional[str] = None
    parity_ok: bool = True
    steps: List[TraceStep] = field(default_factory=list)

    def format_table(self) -> str:
        lines = [
            "=" * 84,
            f"🔬 SYNAX IEEE-754 ADIM ADIM HATA AYIKLAYICI (DEBUG TRACE) — {self.kernel_name} [#{self.ir_hash}]",
            f"   Örnek İndeksi: [{self.index}] | Ham Girdiler: a={self.raw_a} ({f32_hex(self.raw_a)}), b={self.raw_b} ({f32_hex(self.raw_b)})",
            "=" * 84,
            f"  {'#':<3} {'AŞAMA':<12} {'ALT İFADE / KURAL':<30} {'DEĞER (f32)':<14} {'IEEE-754 HEX':<12} {'NOT'}",
            "-" * 84,
        ]
        for s in self.steps:
            val_str = f"{s.value_f32:.6g}" if math.isfinite(s.value_f32) else str(s.value_f32)
            lines.append(
                f"  {s.step_id:<3} {s.stage:<12} {s.expression[:30]:<30} {val_str:<14} {s.bits_hex:<12} {s.note}"
            )
        lines.append("-" * 84)
        lines.append(
            f"  Referans Çıktı : {self.final_ref_f32} ({self.final_ref_hex}) | Onarılan Anomali: {self.healed_count}"
        )
        if self.native_f32 is not None:
            status = "✓ BİREBİR EŞLEŞTİ" if self.parity_ok else "✗ UYUŞMAZLIK!"
            lines.append(
                f"  Native Çıktı   : {self.native_f32} ({self.native_hex}) [{status}]"
            )
        lines.append("=" * 84)
        return "\n".join(lines)


class SynaxDebugger:
    """Step-by-step IEEE-754 `binary32` AST & IMMUNE Shield tracer."""

    @staticmethod
    def _is_valid(val: float, bound: Optional[float]) -> bool:
        if not math.isfinite(val):
            return False
        if bound is not None and abs(val) > _f32(abs(bound)):
            return False
        return True

    @classmethod
    def trace_element(
        cls,
        source_or_ir: str | SynaxIR,
        a_val: float,
        b_val: float,
        index: int = 0,
        native_dylib: Optional[str | Path] = None,
    ) -> ElementDebugReport:
        ir = source_or_ir if isinstance(source_or_ir, SynaxIR) else parse_sx(source_or_ir)
        p0, p1 = ir.param_names
        steps: List[TraceStep] = []
        sid = 0

        def add_step(stage: str, expr_s: str, val: float, note: str = "") -> float:
            nonlocal sid
            sid += 1
            vf = _f32(val)
            steps.append(TraceStep(sid, stage, expr_s, vf, f32_hex(vf), note))
            return vf

        ai = add_step("INPUT", p0, a_val, "Girdi kanalı 0")
        bi = add_step("INPUT", p1, b_val, "Girdi kanalı 1")

        mode = ir.safety.nonfinite_mode
        bound = ir.safety.input_abs_bound
        heal_v = _f32(ir.safety.heal_value)
        healed = 0

        ok_a = cls._is_valid(ai, bound)
        ok_b = cls._is_valid(bi, bound)

        if mode != "preserve":
            if not ok_a:
                healed += 1
            if not ok_b:
                healed += 1
            if mode == "heal_inputs":
                if not ok_a:
                    ai = add_step("IMMUNE", f"heal({p0})", heal_v, f"Anomali onarıldı -> {heal_v}")
                if not ok_b:
                    bi = add_step("IMMUNE", f"heal({p1})", heal_v, f"Anomali onarıldı -> {heal_v}")
            elif mode in ("zero_output", "reject") and (not ok_a or not ok_b):
                add_step("IMMUNE", "guard(a, b)", float("nan"), f"Politika={mode} tetiklendi")

        def eval_traced(node: ASTNode) -> float:
            if node.op == "CONST":
                return _f32(float(node.value or 0.0))
            if node.op == "VAR":
                if node.value == "a":
                    return ai
                if node.value == "b":
                    return bi
                return _f32(ir.bias_default)
            if node.op == "BIAS":
                return _f32(ir.bias_default)
            for ch in node.children:
                eval_traced(ch)
            res = node.eval_f32(ai, bi, _f32(ir.bias_default))
            stage = "AST_BIN" if len(node.children) == 2 else ("AST_UNARY" if len(node.children) == 1 else "AST_CALL")
            return add_step(stage, node.to_human_formula(p0, p1), res, f"op={node.op}")

        raw_out = eval_traced(ir.expr)
        final_out = raw_out

        if mode == "zero_output" and not (ok_a and ok_b):
            final_out = add_step("IMMUNE_OUT", "zero_output", heal_v, "Bozuk girdi -> güvenli çıktı")
        elif mode == "reject" and not (ok_a and ok_b):
            final_out = add_step("IMMUNE_OUT", "reject -> NaN", float("nan"), "Sert ret politikası")

        if ir.safety.output_clamp is not None and not (mode == "reject" and not (ok_a and ok_b)):
            lo, hi = _f32(ir.safety.output_clamp[0]), _f32(ir.safety.output_clamp[1])
            if math.isnan(final_out):
                clamped = float("nan")
            else:
                clamped = min(max(final_out, lo), hi)
            final_out = add_step("CLAMP", f"clamp([{lo:g}, {hi:g}])", clamped, "Çıktı sınırlandırma")

        native_val: Optional[float] = None
        native_hex: Optional[str] = None
        parity_ok = True

        if native_dylib is not None and os.path.exists(native_dylib):
            from array import array
            lk = LoadedKernel(str(native_dylib), name="debug_native")
            arr_o, n_healed = lk.run_pure(array("f", [_f32(a_val)]), array("f", [_f32(b_val)]))
            native_val = _f32(float(arr_o[0]))
            native_hex = f32_hex(native_val)
            nh = n_healed if n_healed is not None else healed
            if math.isnan(final_out) and math.isnan(native_val):
                parity_ok = (nh == healed)
            else:
                rel = abs(final_out - native_val) / max(1.0, abs(final_out))
                parity_ok = (rel <= 1e-5) and (nh == healed)

        return ElementDebugReport(
            kernel_name=ir.name,
            ir_hash=ir.ir_hash,
            index=index,
            raw_a=_f32(a_val),
            raw_b=_f32(b_val),
            healed_count=healed,
            final_ref_f32=final_out,
            final_ref_hex=f32_hex(final_out),
            native_f32=native_val,
            native_hex=native_hex,
            parity_ok=parity_ok,
            steps=steps,
        )


@dataclass
class ProfileEntry:
    name: str
    median_ms: float
    iqr_ms: float
    p95_ms: float
    min_ms: float
    ns_per_elem: float
    gb_per_sec: float
    speedup_vs_o3: float


class SynaxProfiler:
    """High-precision warm-cache profiler for compiled `.dylib` / `.so` kernels."""

    @staticmethod
    def profile_dylibs(
        named_dylibs: Sequence[Tuple[str, str | Path]],
        n: int = 4_000_000,
        warmup: int = 4,
        repeats: int = 21,
    ) -> List[ProfileEntry]:
        buf_a = (ctypes.c_float * n)()
        buf_b = (ctypes.c_float * n)()
        buf_out = (ctypes.c_float * n)()
        for i in range(min(n, 4096)):
            buf_a[i] = 0.25 + (i % 97) * 0.03125
            buf_b[i] = -0.5 + (i % 53) * 0.0625
        if n > 4096:
            src_a = ctypes.addressof(buf_a)
            src_b = ctypes.addressof(buf_b)
            chunk_bytes = 4096 * ctypes.sizeof(ctypes.c_float)
            offset = 4096
            while offset < n:
                copy_elems = min(4096, n - offset)
                ctypes.memmove(
                    ctypes.addressof(buf_a) + offset * 4, src_a, copy_elems * 4
                )
                ctypes.memmove(
                    ctypes.addressof(buf_b) + offset * 4, src_b, copy_elems * 4
                )
                offset += copy_elems

        raw_stats: List[Tuple[str, float, float, float, float]] = []
        o3_ms: Optional[float] = None

        for label, path in named_dylibs:
            if not os.path.exists(path):
                continue
            lk = LoadedKernel(str(path), name=label)
            for _ in range(warmup):
                lk._fn_basic(buf_a, buf_b, buf_out, n)
            samples_ms: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                lk._fn_basic(buf_a, buf_b, buf_out, n)
                samples_ms.append((time.perf_counter() - t0) * 1000.0)
            samples_ms.sort()
            med = statistics.median(samples_ms)
            q1 = samples_ms[len(samples_ms) // 4]
            q3 = samples_ms[(3 * len(samples_ms)) // 4]
            iqr = q3 - q1
            p95 = samples_ms[min(len(samples_ms) - 1, int(len(samples_ms) * 0.95))]
            mn = samples_ms[0]
            if label == "v0_clang_o3_scalar":
                o3_ms = med
            raw_stats.append((label, med, iqr, p95, mn))

        if o3_ms is None and raw_stats:
            o3_ms = raw_stats[0][1]

        total_bytes = float(n) * 3.0 * 4.0  # 2 float32 reads + 1 float32 write
        entries: List[ProfileEntry] = []
        for label, med, iqr, p95, mn in raw_stats:
            sec = max(med / 1000.0, 1e-12)
            gb_s = (total_bytes / sec) / 1e9
            ns_el = (med * 1e6) / max(n, 1)
            sp_o3 = (o3_ms or med) / max(med, 1e-9)
            entries.append(
                ProfileEntry(
                    name=label,
                    median_ms=med,
                    iqr_ms=iqr,
                    p95_ms=p95,
                    min_ms=mn,
                    ns_per_elem=ns_el,
                    gb_per_sec=gb_s,
                    speedup_vs_o3=sp_o3,
                )
            )
        entries.sort(key=lambda e: e.median_ms)
        return entries
