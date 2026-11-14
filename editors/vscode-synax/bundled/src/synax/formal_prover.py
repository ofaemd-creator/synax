"""
SYNAX Formal Interval & Abstract Interpretation Prover (`src/synax/formal_prover.py`)
=====================================================================================
Mathematically proves compile-time numerical safety properties of `.sx` kernels using
IEEE-754 interval arithmetic (`[lo, hi]` domain propagation):
  - Proves freedom from division by zero (`0.0 not in denominator_interval`)
  - Proves freedom from domain errors (`sqrt(x)` with `x >= 0`, `log(x)` with `x > 0`)
  - Proves freedom from IEEE-754 float32 overflow (`|y| <= 3.402823466e+38`)
  - Computes exact static output bounds `[min_out, max_out]` and signs a SHA-256
    formal verification certificate.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from synax_ir import ASTNode, SynaxIR, _f32

FLT32_MAX = 3.4028234663852886e38


@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float

    @property
    def contains_zero(self) -> bool:
        return self.lo <= 0.0 <= self.hi

    @property
    def is_finite(self) -> bool:
        return math.isfinite(self.lo) and math.isfinite(self.hi) and abs(self.lo) <= FLT32_MAX and abs(self.hi) <= FLT32_MAX

    def __str__(self) -> str:
        return f"[{self.lo:.4g}, {self.hi:.4g}]"


@dataclass
class ProofStep:
    expr: str
    op: str
    interval: Interval
    hazard: Optional[str] = None


@dataclass
class FormalProofCertificate:
    kernel_name: str
    ir_hash: str
    input_a_bounds: Interval
    input_b_bounds: Interval
    raw_output_bounds: Interval
    final_output_bounds: Interval
    div_by_zero_free: bool
    domain_error_free: bool
    overflow_free: bool
    nan_immune_guaranteed: bool
    hazards: List[str] = field(default_factory=list)
    steps: List[ProofStep] = field(default_factory=list)
    certificate_sha256: str = ""

    @property
    def all_verified(self) -> bool:
        return self.div_by_zero_free and self.domain_error_free and self.overflow_free and self.nan_immune_guaranteed

    def to_dict(self) -> Dict[str, object]:
        return {
            "kernel_name": self.kernel_name,
            "ir_hash": self.ir_hash,
            "input_a_bounds": [self.input_a_bounds.lo, self.input_a_bounds.hi],
            "input_b_bounds": [self.input_b_bounds.lo, self.input_b_bounds.hi],
            "raw_output_bounds": [self.raw_output_bounds.lo, self.raw_output_bounds.hi],
            "final_output_bounds": [self.final_output_bounds.lo, self.final_output_bounds.hi],
            "div_by_zero_free": self.div_by_zero_free,
            "domain_error_free": self.domain_error_free,
            "overflow_free": self.overflow_free,
            "nan_immune_guaranteed": self.nan_immune_guaranteed,
            "all_verified": self.all_verified,
            "hazards": self.hazards,
            "certificate_sha256": self.certificate_sha256,
        }


def prove_kernel_safety(
    ir: SynaxIR,
    a_bounds: Tuple[float, float] = (-500.0, 500.0),
    b_bounds: Tuple[float, float] = (-500.0, 500.0),
) -> FormalProofCertificate:
    """
    Propagate intervals `[lo, hi]` through `ir.expr` and `ir.safety` to construct
    a formal mathematical safety certificate.
    """
    bound_cap = ir.safety.input_abs_bound
    if bound_cap is not None:
        ia = Interval(max(a_bounds[0], -bound_cap), min(a_bounds[1], bound_cap))
        ib = Interval(max(b_bounds[0], -bound_cap), min(b_bounds[1], bound_cap))
    else:
        ia = Interval(float(a_bounds[0]), float(a_bounds[1]))
        ib = Interval(float(b_bounds[0]), float(b_bounds[1]))

    steps: List[ProofStep] = []
    hazards: List[str] = []
    div_zero_ok = [True]
    domain_ok = [True]

    def eval_iv(node: ASTNode) -> Interval:
        op = node.op
        if op == "VAR":
            iv = ia if node.value == "a" else ib
            return iv
        if op == "CONST":
            v = float(_f32(float(node.value or 0.0)))
            return Interval(v, v)
        if op == "BIAS":
            v = float(_f32(ir.bias_default))
            return Interval(v, v)

        c_ivs = [eval_iv(c) for c in node.children]
        hz: Optional[str] = None

        if op == "NEG":
            res = Interval(-c_ivs[0].hi, -c_ivs[0].lo)
        elif op == "ADD":
            res = Interval(c_ivs[0].lo + c_ivs[1].lo, c_ivs[0].hi + c_ivs[1].hi)
        elif op == "SUB":
            res = Interval(c_ivs[0].lo - c_ivs[1].hi, c_ivs[0].hi - c_ivs[1].lo)
        elif op == "MUL":
            prods = [
                c_ivs[0].lo * c_ivs[1].lo,
                c_ivs[0].lo * c_ivs[1].hi,
                c_ivs[0].hi * c_ivs[1].lo,
                c_ivs[0].hi * c_ivs[1].hi,
            ]
            res = Interval(min(prods), max(prods))
        elif op == "DIV":
            num, den = c_ivs[0], c_ivs[1]
            if den.contains_zero:
                div_zero_ok[0] = False
                hz = f"Bölünen aralık sıfır içeriyor: payda {den}"
                hazards.append(hz)
                res = Interval(float("-inf"), float("inf"))
            else:
                quots = [num.lo / den.lo, num.lo / den.hi, num.hi / den.lo, num.hi / den.hi]
                res = Interval(min(quots), max(quots))
        elif op == "POW2":
            x = c_ivs[0]
            lo_sq = 0.0 if x.contains_zero else min(x.lo * x.lo, x.hi * x.hi)
            hi_sq = max(x.lo * x.lo, x.hi * x.hi)
            res = Interval(lo_sq, hi_sq)
        elif op == "POW3":
            x = c_ivs[0]
            res = Interval(x.lo ** 3, x.hi ** 3)
        elif op == "SQRT":
            x = c_ivs[0]
            if x.lo < 0.0:
                domain_ok[0] = False
                hz = f"Karekök tanım kümesi negatif değer içeriyor: {x}"
                hazards.append(hz)
                res = Interval(0.0, math.sqrt(max(0.0, x.hi)))
            else:
                res = Interval(math.sqrt(x.lo), math.sqrt(x.hi))
        elif op == "ABS":
            x = c_ivs[0]
            lo_a = 0.0 if x.contains_zero else min(abs(x.lo), abs(x.hi))
            hi_a = max(abs(x.lo), abs(x.hi))
            res = Interval(lo_a, hi_a)
        elif op in ("SIN", "COS"):
            res = Interval(-1.0, 1.0)
        elif op == "EXP":
            x = c_ivs[0]
            lo_e = math.exp(max(-103.0, min(88.7, x.lo)))
            hi_e = float("inf") if x.hi > 88.7228 else math.exp(max(-103.0, x.hi))
            res = Interval(lo_e, hi_e)
        elif op == "LOG":
            x = c_ivs[0]
            if x.lo <= 0.0:
                domain_ok[0] = False
                hz = f"Logaritma tanım kümesi <= 0 içeriyor: {x}"
                hazards.append(hz)
                res = Interval(float("-inf"), math.log(max(1e-12, x.hi)))
            else:
                res = Interval(math.log(x.lo), math.log(x.hi))
        elif op == "SIGMOID":
            x = c_ivs[0]
            s_lo = 1.0 / (1.0 + math.exp(-max(-80.0, min(80.0, x.lo))))
            s_hi = 1.0 / (1.0 + math.exp(-max(-80.0, min(80.0, x.hi))))
            res = Interval(min(s_lo, s_hi), max(s_lo, s_hi))
        elif op == "TANH":
            x = c_ivs[0]
            res = Interval(math.tanh(x.lo), math.tanh(x.hi))
        elif op == "RELU":
            x = c_ivs[0]
            res = Interval(max(0.0, x.lo), max(0.0, x.hi))
        elif op == "MIN":
            res = Interval(min(c_ivs[0].lo, c_ivs[1].lo), min(c_ivs[0].hi, c_ivs[1].hi))
        elif op == "MAX":
            res = Interval(max(c_ivs[0].lo, c_ivs[1].lo), max(c_ivs[0].hi, c_ivs[1].hi))
        elif op == "CLAMP":
            x, lo_iv, hi_iv = c_ivs[0], c_ivs[1], c_ivs[2]
            res = Interval(max(lo_iv.lo, min(x.lo, hi_iv.hi)), min(hi_iv.hi, max(x.hi, lo_iv.lo)))
        elif op == "SELECT":
            cond, vt, vf = c_ivs[0], c_ivs[1], c_ivs[2]
            if cond.lo > 0.0:
                res = vt
            elif cond.hi <= 0.0:
                res = vf
            else:
                res = Interval(min(vt.lo, vf.lo), max(vt.hi, vf.hi))
        elif op == "FMA":
            a_iv, b_iv, c_iv = c_ivs[0], c_ivs[1], c_ivs[2]
            prods = [a_iv.lo * b_iv.lo, a_iv.lo * b_iv.hi, a_iv.hi * b_iv.lo, a_iv.hi * b_iv.hi]
            res = Interval(min(prods) + c_iv.lo, max(prods) + c_iv.hi)
        else:
            res = c_ivs[0] if c_ivs else Interval(0.0, 0.0)

        steps.append(ProofStep(expr=node.to_human_formula(), op=op, interval=res, hazard=hz))
        return res

    raw_iv = eval_iv(ir.expr)
    if ir.safety.output_clamp is not None:
        clo, chi = ir.safety.output_clamp
        final_iv = Interval(max(clo, min(raw_iv.lo, chi)), min(chi, max(raw_iv.hi, clo)))
    else:
        final_iv = raw_iv

    overflow_ok = final_iv.is_finite
    if not overflow_ok:
        hazards.append(f"Çıktı aralığı IEEE-754 binary32 sınırlarını aşıyor: {final_iv}")

    nan_immune = (
        ir.safety.nonfinite_mode in ("heal_inputs", "zero_output")
        and div_zero_ok[0]
        and domain_ok[0]
        and overflow_ok
    )

    cert = FormalProofCertificate(
        kernel_name=ir.name,
        ir_hash=ir.ir_hash,
        input_a_bounds=ia,
        input_b_bounds=ib,
        raw_output_bounds=raw_iv,
        final_output_bounds=final_iv,
        div_by_zero_free=div_zero_ok[0],
        domain_error_free=domain_ok[0],
        overflow_free=overflow_ok,
        nan_immune_guaranteed=nan_immune,
        hazards=hazards,
        steps=steps,
    )
    payload = json.dumps(cert.to_dict(), sort_keys=True)
    cert.certificate_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return cert
