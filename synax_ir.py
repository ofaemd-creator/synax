#!/usr/bin/env python3
"""
SYNAX CANONICAL INTERMEDIATE REPRESENTATION & UNIFIED FRONTEND (synax_ir.py)
=============================================================================
Unifies all SYNAX (.sx) frontends into a single deterministic Intermediate
Representation (SynaxIR) with strict IEEE-754 floating-point semantics:

  1. Structured Kernel Syntax (`synax 0.1` / `kernel name(...) -> tensor<f32>`):
     Matches `synaxcode.online` Cloud Studio (`intent`, `require`, `safety`,
     `let` bindings, `return`, `optimize`, `target`).
  2. Declarative Intent Syntax (`niyet:` / `kural:` / `hedef:` / `formül:`):
     Matches SYNAX v0.4 (`kapili_aktivasyon.sx`, `anomali.sx`) and legacy
     neuro-symbolic scripts (`biyomedikal_kardiyo.sx`, `derin_rezonans.sx`).

Core Invariant:
  `optimization must never change semantics` — IEEE-754 NaN, +Inf, -Inf,
  signed zero, and safety-shield rules are explicitly encoded in `SafetyPolicy`
  and honored identically across Python AST, C11 Scalar, and ARM64 NEON SIMD.
=============================================================================
"""

import hashlib
import json
import math
import os
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from synax_security import SynaxSecurityGuard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRAIN_PATH = os.path.join(BASE_DIR, "synapse_brain.json")


def _f32(val: float) -> float:
    """Round a Python float64 to exact IEEE-754 binary32 single precision."""
    if math.isnan(val):
        return float("nan")
    if math.isinf(val):
        return val
    try:
        return struct.unpack("<f", struct.pack("<f", val))[0]
    except OverflowError:
        return float("inf") if val > 0 else float("-inf")


def _format_c_float(val: float) -> str:
    """Format a float literal cleanly for C11 single-precision codegen."""
    f = _f32(val)
    if math.isnan(f):
        return "NAN"
    if math.isinf(f):
        return "INFINITY" if f > 0 else "(-INFINITY)"
    s = f"{f:.9g}"
    if "." not in s and "e" not in s and "E" not in s:
        s += ".0"
    return f"{s}f"


# ─────────────────────────────────────────────────────────────────
# 1. SAFETY POLICY (IMMUNE SHIELD SEMANTICS)
# ─────────────────────────────────────────────────────────────────
@dataclass
class SafetyPolicy:
    """
    Explicit IEEE-754 & Biomedical Signal Integrity Policy.

    nonfinite_mode:
      - "preserve"    : Standard IEEE-754 propagation (NaN -> NaN, Inf -> IEEE arithmetic).
      - "heal_inputs" : Sanitize non-finite (and out-of-bound) inputs to `heal_value`
                        BEFORE evaluating `expr`, counting each sanitized channel sample.
      - "zero_output" : If either input `a[i]` or `b[i]` is non-finite (or out-of-bound),
                        write `heal_value` directly to `out[i]` without evaluating `expr`.
      - "reject"      : Preserve NaN in raw kernel output while flagging non-finite samples
                        so checked execution raises a deterministic safety rejection.
    """
    nonfinite_mode: str = "preserve"  # "preserve" | "heal_inputs" | "zero_output" | "reject"
    heal_value: float = 0.0
    input_abs_bound: Optional[float] = None
    output_clamp: Optional[Tuple[float, float]] = None

    def guarantees_finite_inputs(self) -> bool:
        return self.nonfinite_mode in ("heal_inputs", "zero_output")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nonfinite_mode": self.nonfinite_mode,
            "heal_value": _f32(self.heal_value),
            "input_abs_bound": _f32(self.input_abs_bound) if self.input_abs_bound is not None else None,
            "output_clamp": [_f32(self.output_clamp[0]), _f32(self.output_clamp[1])]
            if self.output_clamp is not None
            else None,
        }


# ─────────────────────────────────────────────────────────────────
# 2. CANONICAL AST NODE & MULTI-TARGET LOWERING
# ─────────────────────────────────────────────────────────────────
SUPPORTED_OPS = {
    "VAR", "CONST", "BIAS", "NEG",
    "ADD", "SUB", "MUL", "DIV",
    "POW2", "POW3", "SQRT", "ABS",
    "SIN", "COS", "EXP", "LOG",
    "SIGMOID", "TANH", "RELU",
    "MIN", "MAX", "CLAMP",
}

NEON_NATIVE_OPS = {
    "VAR", "CONST", "BIAS", "NEG",
    "ADD", "SUB", "MUL", "DIV",
    "POW2", "POW3", "SQRT", "ABS",
    "RELU", "MIN", "MAX", "CLAMP",
    "EXP", "SIGMOID",
}


@dataclass
class ASTNode:
    op: str
    value: Optional[str] = None
    children: List["ASTNode"] = field(default_factory=list)

    def node_count(self) -> int:
        return 1 + sum(ch.node_count() for ch in self.children)

    def uses_op(self, target_ops: set) -> bool:
        if self.op in target_ops:
            return True
        return any(ch.uses_op(target_ops) for ch in self.children)

    def uses_var(self, var_name: str) -> bool:
        if self.op == "VAR" and self.value == var_name:
            return True
        return any(ch.uses_var(var_name) for ch in self.children)

    def simplify(self, allow_nonfinite_fold: bool = False) -> "ASTNode":
        """
        Semantics-preserving algebraic simplification.
        Never applies `x * 0 -> 0` unless inputs are guaranteed finite, because
        in IEEE-754 `NaN * 0.0 == NaN` and `Inf * 0.0 == NaN`.
        """
        kids = [ch.simplify(allow_nonfinite_fold=allow_nonfinite_fold) for ch in self.children]
        node = ASTNode(self.op, self.value, kids)

        # Constant folding on pure finite constants
        if node.op in ("NEG", "ABS", "SQRT", "RELU", "POW2", "POW3") and len(kids) == 1 and kids[0].op == "CONST":
            v = _f32(float(kids[0].value))
            res = node._eval_op_f32([v])
            if math.isfinite(res):
                return ASTNode("CONST", value=f"{res:.9g}")

        if node.op in ("ADD", "SUB", "MUL", "DIV") and len(kids) == 2 and kids[0].op == "CONST" and kids[1].op == "CONST":
            v0, v1 = _f32(float(kids[0].value)), _f32(float(kids[1].value))
            res = node._eval_op_f32([v0, v1])
            if math.isfinite(res):
                return ASTNode("CONST", value=f"{res:.9g}")

        # Idempotent unary wrappers: abs(abs(u)) -> abs(u), relu(relu(u)) -> relu(u), -(-u) -> u
        if node.op in ("ABS", "RELU") and len(kids) == 1 and kids[0].op == node.op:
            return kids[0]
        if node.op == "NEG" and len(kids) == 1 and kids[0].op == "NEG":
            return kids[0].children[0]

        # Identity elimination (note: x + 0.0 changes -0.0 + 0.0 -> +0.0, fine within signed-zero tolerance,
        # and NaN + 0.0 == NaN, Inf + 0.0 == Inf, so x + 0.0 -> x is IEEE-754 NaN/Inf preserving!)
        if node.op == "ADD" and len(kids) == 2:
            l, r = kids
            if l.op == "CONST" and float(l.value) == 0.0:
                return r
            if r.op == "CONST" and float(r.value) == 0.0:
                return l

        if node.op == "SUB" and len(kids) == 2:
            l, r = kids
            if r.op == "CONST" and float(r.value) == 0.0:
                return l

        if node.op == "MUL" and len(kids) == 2:
            l, r = kids
            if l.op == "CONST" and float(l.value) == 1.0:
                return r
            if r.op == "CONST" and float(r.value) == 1.0:
                return l
            if allow_nonfinite_fold:
                if (l.op == "CONST" and float(l.value) == 0.0) or (r.op == "CONST" and float(r.value) == 0.0):
                    return ASTNode("CONST", value="0.0")

        return node

    # Legacy compatibility alias for SynapseNanoModel callers
    def evolve_and_simplify(self) -> "ASTNode":
        return self.simplify(allow_nonfinite_fold=False)

    def _eval_op_f32(self, args: List[float]) -> float:
        op = self.op
        if op == "NEG":
            return _f32(-args[0])
        if op == "ADD":
            return _f32(args[0] + args[1])
        if op == "SUB":
            return _f32(args[0] - args[1])
        if op == "MUL":
            return _f32(args[0] * args[1])
        if op == "DIV":
            a0, a1 = args[0], args[1]
            if math.isnan(a0) or math.isnan(a1):
                return float("nan")
            if a1 == 0.0:
                if a0 == 0.0:
                    return float("nan")
                sign = math.copysign(1.0, a0) * math.copysign(1.0, a1)
                return float("inf") if sign > 0 else float("-inf")
            if math.isinf(a0) and math.isinf(a1):
                return float("nan")
            if math.isinf(a1):
                sign = math.copysign(1.0, a0) * math.copysign(1.0, a1)
                return math.copysign(0.0, sign)
            return _f32(a0 / a1)
        if op == "POW2":
            return _f32(args[0] * args[0])
        if op == "POW3":
            sq = _f32(args[0] * args[0])
            return _f32(sq * args[0])
        if op == "SQRT":
            x = args[0]
            if math.isnan(x) or x < 0.0:
                return float("nan")
            if x == 0.0 or math.isinf(x):
                return x
            return _f32(math.sqrt(x))
        if op == "ABS":
            return _f32(abs(args[0])) if not math.isnan(args[0]) else float("nan")
        if op == "SIN":
            if not math.isfinite(args[0]):
                return float("nan")
            return _f32(math.sin(args[0]))
        if op == "COS":
            if not math.isfinite(args[0]):
                return float("nan")
            return _f32(math.cos(args[0]))
        if op == "EXP":
            x = args[0]
            if math.isnan(x):
                return float("nan")
            if x == float("-inf"):
                return 0.0
            if x == float("inf") or x > 88.722839:
                return float("inf")
            if x < -103.97208:
                return 0.0
            return _f32(math.exp(x))
        if op == "LOG":
            x = args[0]
            if math.isnan(x) or x < 0.0:
                return float("nan")
            if x == 0.0:
                return float("-inf")
            if math.isinf(x):
                return float("inf")
            return _f32(math.log(x))
        if op == "SIGMOID":
            x = args[0]
            if math.isnan(x):
                return float("nan")
            neg_x = _f32(-x)
            ex = ASTNode("EXP")._eval_op_f32([neg_x])
            denom = _f32(1.0 + ex)
            return ASTNode("DIV")._eval_op_f32([1.0, denom])
        if op == "TANH":
            x = args[0]
            if math.isnan(x):
                return float("nan")
            if x == float("inf"):
                return 1.0
            if x == float("-inf"):
                return -1.0
            return _f32(math.tanh(x))
        if op == "RELU":
            x = args[0]
            if math.isnan(x):
                return float("nan")
            return x if x > 0.0 else 0.0
        if op == "MIN":
            x, y = args[0], args[1]
            if math.isnan(x) or math.isnan(y):
                return float("nan")
            if x == 0.0 and y == 0.0:
                return -0.0 if (math.copysign(1.0, x) < 0 or math.copysign(1.0, y) < 0) else 0.0
            return x if x < y else y
        if op == "MAX":
            x, y = args[0], args[1]
            if math.isnan(x) or math.isnan(y):
                return float("nan")
            if x == 0.0 and y == 0.0:
                return 0.0 if (math.copysign(1.0, x) > 0 or math.copysign(1.0, y) > 0) else -0.0
            return x if x > y else y
        if op == "CLAMP":
            x, lo, hi = args[0], args[1], args[2]
            hi_clamped = ASTNode("MAX")._eval_op_f32([x, lo])
            return ASTNode("MIN")._eval_op_f32([hi_clamped, hi])
        return 0.0

    def eval_f32(self, a_val: float, b_val: float, bias_val: float = 0.25) -> float:
        """Pure-Python IEEE-754 single-precision AST evaluator (Independent Reference #1)."""
        if self.op == "VAR":
            return _f32(a_val if self.value == "a" else b_val)
        if self.op == "CONST":
            return _f32(float(self.value))
        if self.op == "BIAS":
            return _f32(bias_val)
        child_vals = [ch.eval_f32(a_val, b_val, bias_val) for ch in self.children]
        return self._eval_op_f32(child_vals)

    # ── Tier-1: IEEE-754 C11 Scalar Float32 ──
    def to_c_scalar(self, var_a: str = "a[i]", var_b: str = "b[i]", var_bias: str = "bias") -> str:
        if self.op == "VAR":
            return var_a if self.value == "a" else var_b
        if self.op == "CONST":
            return _format_c_float(float(self.value))
        if self.op == "BIAS":
            return var_bias

        c = [ch.to_c_scalar(var_a=var_a, var_b=var_b, var_bias=var_bias) for ch in self.children]
        if self.op == "NEG":     return f"(-({c[0]}))"
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"({c[0]} * {c[1]})"
        if self.op == "DIV":     return f"({c[0]} / {c[1]})"
        if self.op == "POW2":    return f"synax_sqf({c[0]})"
        if self.op == "POW3":    return f"synax_cbef({c[0]})"
        if self.op == "SQRT":    return f"sqrtf({c[0]})"
        if self.op == "ABS":     return f"fabsf({c[0]})"
        if self.op == "SIN":     return f"sinf({c[0]})"
        if self.op == "COS":     return f"cosf({c[0]})"
        if self.op == "EXP":     return f"expf({c[0]})"
        if self.op == "LOG":     return f"logf({c[0]})"
        if self.op == "SIGMOID": return f"(1.0f / (1.0f + expf(-({c[0]}))))"
        if self.op == "TANH":    return f"tanhf({c[0]})"
        if self.op == "RELU":    return f"synax_reluf({c[0]})"
        if self.op == "MIN":     return f"synax_minf({c[0]}, {c[1]})"
        if self.op == "MAX":     return f"synax_maxf({c[0]}, {c[1]})"
        if self.op == "CLAMP":   return f"synax_clampf({c[0]}, {c[1]}, {c[2]})"
        return c[0] if c else "0.0f"

    # ── Tier-2: ARM64 NEON SIMD Intrinsics (float32x4_t) ──
    def can_use_pure_neon_intrinsics(self) -> bool:
        if self.op not in NEON_NATIVE_OPS:
            return False
        return all(ch.can_use_pure_neon_intrinsics() for ch in self.children)

    def to_neon_f32x4(self, var_a: str = "va", var_b: str = "vb", var_bias: str = "vbias") -> str:
        if self.op == "VAR":
            return var_a if self.value == "a" else var_b
        if self.op == "CONST":
            return f"vdupq_n_f32({_format_c_float(float(self.value))})"
        if self.op == "BIAS":
            return var_bias

        c = [ch.to_neon_f32x4(var_a=var_a, var_b=var_b, var_bias=var_bias) for ch in self.children]
        if self.op == "NEG":     return f"vnegq_f32({c[0]})"
        if self.op == "ADD":     return f"vaddq_f32({c[0]}, {c[1]})"
        if self.op == "SUB":     return f"vsubq_f32({c[0]}, {c[1]})"
        if self.op == "MUL":     return f"vmulq_f32({c[0]}, {c[1]})"
        if self.op == "DIV":     return f"vdivq_f32({c[0]}, {c[1]})"
        if self.op == "POW2":    return f"synax_vsqq_f32({c[0]})"
        if self.op == "POW3":    return f"synax_vcbeq_f32({c[0]})"
        if self.op == "SQRT":    return f"vsqrtq_f32({c[0]})"
        if self.op == "ABS":     return f"vabsq_f32({c[0]})"
        if self.op == "RELU":    return f"vmaxq_f32(vdupq_n_f32(0.0f), {c[0]})"
        if self.op == "MIN":     return f"vminq_f32({c[0]}, {c[1]})"
        if self.op == "MAX":     return f"vmaxq_f32({c[0]}, {c[1]})"
        if self.op == "CLAMP":   return f"vminq_f32(vmaxq_f32({c[0]}, {c[1]}), {c[2]})"
        if self.op == "EXP":     return f"synax_vexpq_f32({c[0]})"
        if self.op == "SIGMOID": return f"synax_vsigmoidq_f32({c[0]})"
        return c[0] if c else "vdupq_n_f32(0.0f)"

    # ── Tier-0: Q16.16 Fixed-Point C89 (TinyMCU compatibility) ──
    def to_q16_fixed_point(self) -> str:
        if self.op == "VAR":
            return f"q_{self.value}[i]"
        if self.op == "CONST":
            q_val = int(round(float(self.value) * 65536))
            return f"((int32_t){q_val})"
        if self.op == "BIAS":
            return "q_bias"
        c = [ch.to_q16_fixed_point() for ch in self.children]
        if self.op == "NEG":     return f"(-({c[0]}))"
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"((int32_t)(((int64_t)({c[0]}) * ({c[1]})) >> 16))"
        if self.op == "DIV":     return f"((int32_t)((((int64_t)({c[0]})) << 16) / (({c[1]}) | 1)))"
        if self.op == "POW2":    return f"((int32_t)(((int64_t)({c[0]}) * ({c[0]})) >> 16))"
        if self.op == "ABS":     return f"(({c[0]}) < 0 ? -({c[0]}) : ({c[0]}))"
        if self.op == "RELU":    return f"(({c[0]}) > 0 ? ({c[0]}) : 0)"
        if self.op == "SQRT":    return f"q16_sqrt({c[0]})"
        if self.op == "SIGMOID": return f"q16_fast_sigmoid({c[0]})"
        if self.op == "TANH":    return f"q16_fast_tanh({c[0]})"
        return c[0] if c else "0"

    def to_human_formula(self, name_a: str = "a", name_b: str = "b") -> str:
        if self.op == "VAR":
            return name_a if self.value == "a" else name_b
        if self.op == "CONST":
            return f"{_f32(float(self.value)):.6g}"
        if self.op == "BIAS":
            return "bias"
        c = [ch.to_human_formula(name_a=name_a, name_b=name_b) for ch in self.children]
        if self.op == "NEG":     return f"(-{c[0]})"
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"({c[0]} * {c[1]})"
        if self.op == "DIV":     return f"({c[0]} / {c[1]})"
        if self.op == "POW2":    return f"({c[0]})²"
        if self.op == "POW3":    return f"({c[0]})³"
        if self.op == "SQRT":    return f"sqrt({c[0]})"
        if self.op == "ABS":     return f"abs({c[0]})"
        if self.op == "SIN":     return f"sin({c[0]})"
        if self.op == "COS":     return f"cos({c[0]})"
        if self.op == "EXP":     return f"exp({c[0]})"
        if self.op == "LOG":     return f"log({c[0]})"
        if self.op == "SIGMOID": return f"sigmoid({c[0]})"
        if self.op == "TANH":    return f"tanh({c[0]})"
        if self.op == "RELU":    return f"relu({c[0]})"
        if self.op == "MIN":     return f"min({c[0]}, {c[1]})"
        if self.op == "MAX":     return f"max({c[0]}, {c[1]})"
        if self.op == "CLAMP":   return f"clamp({c[0]}, {c[1]}, {c[2]})"
        return "?"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op": self.op,
            "value": self.value,
            "children": [ch.to_dict() for ch in self.children],
        }


# ─────────────────────────────────────────────────────────────────
# 3. CANONICAL SYNAX IR MODULE
# ─────────────────────────────────────────────────────────────────
@dataclass
class SynaxIR:
    name: str
    syntax_format: str            # "structured_v01" | "declarative_intent"
    version: str
    param_names: Tuple[str, str]
    intent_text: str
    rule_text: str
    target_hint: str
    optimize_goal: str
    bias_default: float
    safety: SafetyPolicy
    expr: ASTNode
    ir_hash: str = ""

    def __post_init__(self):
        if not self.ir_hash:
            self.ir_hash = self.compute_ir_hash()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "bias_default": _f32(self.bias_default),
            "safety": self.safety.to_dict(),
            "expr": self.expr.to_dict(),
        }

    def compute_ir_hash(self) -> str:
        payload = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]

    def eval_element_f32(self, raw_a: float, raw_b: float) -> Tuple[float, int]:
        """
        Evaluate 1 element `(raw_a, raw_b)` in pure-Python IEEE-754 float32
        honoring `SafetyPolicy`. Returns `(output_value, healed_count)`.
        """
        a = _f32(raw_a)
        b = _f32(raw_b)
        healed = 0
        bound = self.safety.input_abs_bound

        def is_bad(v: float) -> bool:
            if not math.isfinite(v):
                return True
            if bound is not None and abs(v) > bound:
                return True
            return False

        bad_a = is_bad(a)
        bad_b = is_bad(b)

        if self.safety.nonfinite_mode == "heal_inputs":
            hv = _f32(self.safety.heal_value)
            if bad_a:
                a = hv
                healed += 1
            if bad_b:
                b = hv
                healed += 1
        elif self.safety.nonfinite_mode == "zero_output":
            if bad_a:
                healed += 1
            if bad_b:
                healed += 1
            if bad_a or bad_b:
                out_v = _f32(self.safety.heal_value)
                if self.safety.output_clamp is not None:
                    lo, hi = self.safety.output_clamp
                    out_v = ASTNode("CLAMP")._eval_op_f32([out_v, _f32(lo), _f32(hi)])
                return out_v, healed
        elif self.safety.nonfinite_mode == "reject":
            if bad_a:
                healed += 1
            if bad_b:
                healed += 1
            if bad_a or bad_b:
                return float("nan"), healed

        val = self.expr.eval_f32(a, b, self.bias_default)
        if self.safety.output_clamp is not None:
            lo, hi = self.safety.output_clamp
            val = ASTNode("CLAMP")._eval_op_f32([val, _f32(lo), _f32(hi)])
        return val, healed


# ─────────────────────────────────────────────────────────────────
# 4. RECURSIVE-DESCENT EXPRESSION PARSER
# ─────────────────────────────────────────────────────────────────
TOKEN_REGEX = re.compile(
    r"\s*(?:(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|(\*\*|[+\-*/^(),]))\s*"
)


def parse_symbolic_expression(
    expr_src: str,
    param_map: Optional[Dict[str, str]] = None,
    let_env: Optional[Dict[str, ASTNode]] = None,
) -> ASTNode:
    """
    Deterministic recursive-descent expression parser supporting:
      - Binary `+`, `-`, `*`, `/`, power `^` / `**` (for `^2`, `^3`)
      - Unary `-`, `+`
      - Multi-arg functions: `clamp(x, lo, hi)`, `min(x, y)`, `max(x, y)`
      - Unary functions: `sqrt`, `square`/`pow2`, `cube`/`pow3`, `abs`,
        `sin`, `cos`, `exp`, `log`/`ln`, `sigmoid`, `tanh`, `relu`
      - Named kernel parameters `(dbp, cvp)` and inlined `let` bindings.
    """
    p_map = param_map or {
        "a": "a", "x": "a", "sinyal1": "a", "v1": "a", "sig_a": "a", "dbp": "a", "abp": "a", "ecg_raw": "a",
        "b": "b", "y": "b", "sinyal2": "b", "v2": "b", "sig_b": "b", "cvp": "b", "baseline": "b",
    }
    env = let_env or {}

    tokens: List[Tuple[str, str]] = []
    pos_char = 0
    src = expr_src.strip()
    while pos_char < len(src):
        m = TOKEN_REGEX.match(src, pos_char)
        if not m:
            snippet = src[pos_char:pos_char + 24]
            raise SyntaxError(f"Sözdizimi hatası (ifade çözümlenemedi): {snippet!r}")
        num, ident, sym = m.groups()
        if num is not None:
            tokens.append(("NUM", num))
        elif ident is not None:
            tokens.append(("ID", ident))
        else:
            tokens.append(("SYM", sym))
        pos_char = m.end()

    if not tokens:
        raise SyntaxError("Boş matematiksel ifade.")

    idx = [0]

    def peek() -> Optional[Tuple[str, str]]:
        return tokens[idx[0]] if idx[0] < len(tokens) else None

    def consume() -> Tuple[str, str]:
        t = tokens[idx[0]]
        idx[0] += 1
        return t

    def expect_sym(expected: str):
        t = peek()
        if t is None or t != ("SYM", expected):
            got = t[1] if t else "EOF"
            raise SyntaxError(f"'{expected}' bekleniyordu, '{got}' bulundu.")
        consume()

    def parse_add() -> ASTNode:
        node = parse_mul()
        while True:
            t = peek()
            if t and t[0] == "SYM" and t[1] in ("+", "-"):
                op = consume()[1]
                rhs = parse_mul()
                node = ASTNode("ADD" if op == "+" else "SUB", children=[node, rhs])
            else:
                break
        return node

    def parse_mul() -> ASTNode:
        node = parse_unary()
        while True:
            t = peek()
            if t and t[0] == "SYM" and t[1] in ("*", "/"):
                op = consume()[1]
                rhs = parse_unary()
                node = ASTNode("MUL" if op == "*" else "DIV", children=[node, rhs])
            else:
                break
        return node

    def parse_unary() -> ASTNode:
        t = peek()
        if t and t[0] == "SYM" and t[1] == "-":
            consume()
            operand = parse_unary()
            if operand.op == "CONST":
                return ASTNode("CONST", value=str(-float(operand.value)))
            return ASTNode("NEG", children=[operand])
        if t and t[0] == "SYM" and t[1] == "+":
            consume()
            return parse_unary()
        return parse_power()

    def parse_power() -> ASTNode:
        node = parse_primary()
        t = peek()
        if t and t[0] == "SYM" and t[1] in ("^", "**"):
            consume()
            exp_tok = peek()
            if exp_tok and exp_tok[0] == "NUM":
                p_str = consume()[1]
                if float(p_str) == 2.0:
                    return ASTNode("POW2", children=[node])
                if float(p_str) == 3.0:
                    return ASTNode("POW3", children=[node])
                raise SyntaxError(f"Desteklenmeyen üs değeri: ^{p_str} (yalnızca ^2 ve ^3 desteklenir)")
            raise SyntaxError("Üs operatöründen sonra sayısal sabit (2 veya 3) bekleniyordu.")
        return node

    def parse_primary() -> ASTNode:
        t = peek()
        if t is None:
            raise SyntaxError("Beklenmeyen ifade sonu.")
        kind, val = t
        if kind == "SYM" and val == "(":
            consume()
            node = parse_add()
            expect_sym(")")
            return node
        if kind == "NUM":
            consume()
            return ASTNode("CONST", value=val)
        if kind == "ID":
            consume()
            nxt = peek()
            if nxt and nxt == ("SYM", "("):
                consume()  # '('
                args: List[ASTNode] = []
                if peek() != ("SYM", ")"):
                    while True:
                        args.append(parse_add())
                        if peek() == ("SYM", ","):
                            consume()
                        else:
                            break
                expect_sym(")")
                fn = val.lower()
                unary_map = {
                    "sqrt": "SQRT", "square": "POW2", "pow2": "POW2",
                    "cube": "POW3", "pow3": "POW3", "abs": "ABS", "fabs": "ABS",
                    "sin": "SIN", "cos": "COS", "exp": "EXP",
                    "log": "LOG", "ln": "LOG", "sigmoid": "SIGMOID",
                    "tanh": "TANH", "relu": "RELU",
                }
                if fn in unary_map:
                    if len(args) != 1:
                        raise SyntaxError(f"'{fn}()' 1 argüman bekler, {len(args)} verildi.")
                    return ASTNode(unary_map[fn], children=args)
                if fn in ("min", "max"):
                    if len(args) != 2:
                        raise SyntaxError(f"'{fn}()' 2 argüman bekler, {len(args)} verildi.")
                    return ASTNode(fn.upper(), children=args)
                if fn == "clamp":
                    if len(args) != 3:
                        raise SyntaxError(f"'clamp(x, lo, hi)' 3 argüman bekler, {len(args)} verildi.")
                    return ASTNode("CLAMP", children=args)
                raise SyntaxError(f"Bilinmeyen yerleşik fonksiyon: '{val}()'")

            # Variable or `let` binding lookup
            if val in env:
                return env[val]
            low = val.lower()
            if low in env:
                return env[low]
            if val in p_map:
                return ASTNode("VAR", value=p_map[val])
            if low in p_map:
                return ASTNode("VAR", value=p_map[low])
            if low == "bias":
                return ASTNode("BIAS")
            raise SyntaxError(f"Tanımsız değişken veya kanal: '{val}'")

        raise SyntaxError(f"Beklenmeyen atom: '{val}'")

    root = parse_add()
    if peek() is not None:
        raise SyntaxError(f"İfade sonunda fazladan karakterler: '{peek()[1]}'")
    return root


# ─────────────────────────────────────────────────────────────────
# 5. STRUCTURED `.sx` (`synax 0.1`) & DECLARATIVE `.sx` PARSERS
# ─────────────────────────────────────────────────────────────────
def _strip_line_comments(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        # Strip // comments outside quotes and # comments
        in_quote = False
        out_chars = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_quote = not in_quote
                out_chars.append(ch)
            elif not in_quote and line[i:i + 2] == "//":
                break
            elif not in_quote and ch == "#":
                break
            else:
                out_chars.append(ch)
            i += 1
        cleaned.append("".join(out_chars))
    return "\n".join(cleaned)


def parse_structured_sx(raw_text: str) -> SynaxIR:
    """
    Parse structured `synax 0.1` kernel blocks:
      synax 0.1
      kernel name(p0: tensor<f32>, p1: tensor<f32>) -> tensor<f32> { ... }
    """
    text = _strip_line_comments(raw_text)
    ver_match = re.search(r"\bsynax\s+(\d+(?:\.\d+)?)", text)
    version = ver_match.group(1) if ver_match else "0.1"

    hdr_match = re.search(
        r"\bkernel\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*(?:->\s*[A-Za-z0-9_<>]+\s*)?\{(.*)\}",
        text,
        re.S,
    )
    if not hdr_match:
        raise SyntaxError("Yapısal .sx hatası: geçerli bir `kernel <ad>(...) -> tensor<f32> { ... }` bloğu bulunamadı.")

    kernel_name = hdr_match.group(1).strip()
    params_raw = hdr_match.group(2).strip()
    body = hdr_match.group(3)

    param_names_list: List[str] = []
    if params_raw:
        for part in params_raw.split(","):
            part = part.strip()
            if not part:
                continue
            pname = part.split(":")[0].strip()
            param_names_list.append(pname)

    if len(param_names_list) == 0:
        param_names = ("a", "b")
    elif len(param_names_list) == 1:
        param_names = (param_names_list[0], "b")
    else:
        param_names = (param_names_list[0], param_names_list[1])

    param_map = {
        param_names[0]: "a",
        param_names[1]: "b",
        "a": "a",
        "b": "b",
    }

    intent_match = re.search(r'\bintent\s+"([^"]*)"', body)
    intent_text = intent_match.group(1).strip() if intent_match else kernel_name

    safety = SafetyPolicy(nonfinite_mode="preserve")
    rule_parts: List[str] = []
    safety_match = re.search(r"\bsafety\s*\{(.*?)\}", body, re.S)
    if safety_match:
        sbody = safety_match.group(1)
        rule_parts.append(" ".join(sbody.split()))
        nf_heal = re.search(r"\bnonfinite\s*=\s*heal\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*\)", sbody)
        nf_mode = re.search(r"\bnonfinite\s*=\s*(preserve|reject|zero_output)\b", sbody)
        if nf_heal:
            safety.nonfinite_mode = "heal_inputs"
            safety.heal_value = float(nf_heal.group(1))
        elif nf_mode:
            safety.nonfinite_mode = nf_mode.group(1)

        rc_clamp = re.search(
            r"\brange_check\s*=\s*clamp\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)",
            sbody,
        )
        if rc_clamp:
            safety.output_clamp = (float(rc_clamp.group(1)), float(rc_clamp.group(2)))

        in_bound = re.search(r"\binput_bound\s*=\s*abs_max\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*\)", sbody)
        if in_bound:
            safety.input_abs_bound = float(in_bound.group(1))

    # Remove safety { ... } block so line-by-line body parsing sees let/return/optimize/target cleanly
    body_clean = re.sub(r"\bsafety\s*\{.*?\}", "", body, flags=re.S)

    let_env: Dict[str, ASTNode] = {}
    return_ast: Optional[ASTNode] = None
    optimize_goal = "latency"
    target_hint = "auto"

    for raw_line in body_clean.splitlines():
        line = raw_line.strip().rstrip(";")
        if not line:
            continue
        if line.startswith("intent ") or line.startswith("require "):
            continue
        m_opt = re.match(r"^optimize\s+([A-Za-z_]\w*)$", line)
        if m_opt:
            optimize_goal = m_opt.group(1).lower()
            continue
        m_tgt = re.match(r"^target\s+([A-Za-z_0-9\-]+)$", line)
        if m_tgt:
            target_hint = m_tgt.group(1).lower()
            continue
        m_let = re.match(r"^let\s+([A-Za-z_]\w*)\s*=\s*(.+)$", line)
        if m_let:
            var_name = m_let.group(1)
            rhs_expr = m_let.group(2)
            let_env[var_name] = parse_symbolic_expression(rhs_expr, param_map=param_map, let_env=let_env)
            continue
        m_ret = re.match(r"^return\s+(.+)$", line)
        if m_ret:
            return_ast = parse_symbolic_expression(m_ret.group(1), param_map=param_map, let_env=let_env)
            continue

    if return_ast is None:
        raise SyntaxError(f"Kernel '{kernel_name}' içinde `return <ifade>` satırı bulunamadı.")

    simplified = return_ast.simplify(allow_nonfinite_fold=safety.guarantees_finite_inputs())

    ok, reason = SynaxSecurityGuard.verify_c_expression(simplified.to_c_scalar())
    if not ok:
        raise ValueError(f"[SYNAX-SEC] Güvenli olmayan ifade engellendi: {reason}")

    return SynaxIR(
        name=kernel_name,
        syntax_format="structured_v01",
        version=version,
        param_names=param_names,
        intent_text=intent_text,
        rule_text="; ".join(rule_parts) if rule_parts else "preserve",
        target_hint=target_hint,
        optimize_goal=optimize_goal,
        bias_default=0.25,
        safety=safety,
        expr=simplified,
    )


def _load_learned_concepts() -> Dict[str, str]:
    defaults = {
        "kinetik enerji": "0.5 * a * (b * b) + bias",
        "kinetic energy": "0.5 * a * (b * b) + bias",
        "serebral perfüzyon": "relu(a - b) / (2.2 - 0.04 * relu(a - b))",
        "cpr hemodinami": "relu(a - b) / (2.2 - 0.04 * relu(a - b))",
        "harmonik osilasyon": "sin(a) * cos(b) + bias",
        "nöral kapı": "sigmoid(a * b + bias)",
        "neural gate": "sigmoid(a * b + bias)",
        "öklid enerjisi": "sqrt((a - b) * (a - b)) + bias",
        "manhattan mesafesi": "abs(a - b) + bias",
        "logaritmik kazanç": "log(abs(a * b) + 1.0) + bias",
    }
    if os.path.exists(BRAIN_PATH):
        ok, _ = SynaxSecurityGuard.verify_json_file(BRAIN_PATH)
        if ok:
            try:
                with open(BRAIN_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                merged = dict(defaults)
                merged.update(data.get("learned_concepts", {}))
                return merged
            except Exception:
                pass
    return defaults


def _infer_declarative_safety(kural_text: str) -> SafetyPolicy:
    low = kural_text.lower()
    if not low.strip():
        return SafetyPolicy(nonfinite_mode="preserve")

    if "nan girdi nan" in low or "preserve" in low or "koru" in low:
        return SafetyPolicy(nonfinite_mode="preserve")

    if "reddet" in low or "reject" in low:
        return SafetyPolicy(nonfinite_mode="reject")

    if any(p in low for p in ["çıktı 0 olsun", "cikti 0 olsun", "sonuç 0 olsun", "sonuc 0 olsun", "eleman için çıktı 0"]):
        return SafetyPolicy(nonfinite_mode="zero_output", heal_value=0.0)

    if any(p in low for p in ["ranvier", "elektrot kopması", "1000"]):
        return SafetyPolicy(nonfinite_mode="heal_inputs", heal_value=0.0, input_abs_bound=1000.0)

    if any(p in low for p in ["nan", "sonsuz", "inf", "iyileştir", "iyilestir", "onar", "bağışıklık", "bagisiklik", "kalkan", "heal"]):
        return SafetyPolicy(nonfinite_mode="heal_inputs", heal_value=0.0)

    return SafetyPolicy(nonfinite_mode="preserve")


def _infer_declarative_symbolic_expr(niyet_text: str, explicit_expr: Optional[str]) -> Tuple[str, float]:
    """
    Translate Turkish/English declarative `niyet:` into a canonical symbolic expression
    and default bias value.
    """
    bias_val = 0.25
    if explicit_expr:
        return explicit_expr.strip(), bias_val

    low = niyet_text.strip().lower()

    # 1. Learned concept memory
    learned = _load_learned_concepts()
    for concept, formula in learned.items():
        if concept in low:
            return formula, bias_val

    # 2. Direct symbolic expression without Turkish prose
    if re.search(r"[\(\)\+\-\*\/\^]", low) and not any(
        w in low for w in [
            "ile", "nin", "nın", "nun", "nün", "fark", "topla", "çarp", "carp",
            "hesapla", "uygula", "ekle", "sensör", "sensor", "sinyal", "akış",
        ]
    ):
        return low, bias_val

    # 3. Domain-specific canonical intents in SYNAX repository & v0.4 benchmark suite
    # 3a. Gated Linear Unit / Kapılı aktivasyon (v0.4 kapili_aktivasyon.sx)
    if ("sigmoid" in low and ("b ile çarp" in low or "b ile carp" in low or "kapılı aktivasyon" in low or "glu" in low)):
        if "b'nin sigmoid" in low or "bnin sigmoid" in low:
            return "sigmoid(b) * a", bias_val
        return "sigmoid(a) * b", bias_val

    # 3b. Hemodynamic CPP & Ranvier saltatory energy (biyomedikal_kardiyo.sx)
    if ("koroner perfüzyon" in low or "cpp" in low) and ("hemodinamik enerji" in low or "cvp" in low):
        if "enerji" in low:
            return "sqrt((a - b)^2 + 0.000001) + 0.5 * (a + b)", bias_val
        return "a - b", bias_val

    # 3c. Deep nonlinear polynomial resonance (derin_rezonans.sx)
    if "polinom rezonans" in low or "4 katmanlı" in low:
        poly = "((a * b + bias) * 0.95 + 0.05 * ((a * b + bias)^2))"
        if "relu" in low:
            return f"relu({poly})", bias_val
        return poly, bias_val

    # 4. General compositional NL-to-AST synthesis
    if any(w in low for w in ["fark", "çıkar", "cikar", "difference", "subtract", "mesafe"]):
        base = "(a - b)"
    elif any(w in low for w in ["oran", "böl", "bol", "divide", "ratio"]):
        base = "(a / b)"
    elif any(w in low for w in ["topla", "toplam", "sum", "add", "birleştir"]):
        base = "(a + b)"
    else:
        base = "(a * b)"

    if any(w in low for w in ["küp", "kup", "cube"]):
        base = f"pow3({base})"
    elif any(w in low for w in ["kare", "square", "l2", "enerji"]):
        # Avoid squaring if only "karekök" was mentioned without "karesinin" / "kare"
        if re.search(r"\b(karesi|karesini|karesinin|kare|square|l2)\b", low) or (
            "enerji" in low and "karekök" not in low and "karekok" not in low
        ):
            base = f"pow2({base})"

    if any(w in low for w in ["karekök", "karekok", "sqrt", "root"]):
        base = f"sqrt({base})"
    if any(w in low for w in ["mutlak", "abs", "absolute"]):
        base = f"abs({base})"
    if re.search(r"\b(sinüs|sinus|sin|dalga)\b", low):
        base = f"sin({base})"
    if re.search(r"\b(kosinüs|kosinus|cos)\b", low):
        base = f"cos({base})"
    if re.search(r"\b(logaritma|log|ln)\b", low):
        base = f"log({base})"

    # Explicit numeric bias / offset detection (e.g., "0.5 sapma ekle")
    num_bias_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:sapma|bias|eşik|esik|offset|sabit)\s*(?:ekle)?", low)
    if num_bias_match:
        c_lit = num_bias_match.group(1)
        bias_val = float(c_lit)
        base = f"({base} + {c_lit})"
    elif any(w in low for w in ["bias", "sapma", "eşik", "esik", "offset"]):
        base = f"({base} + bias)"

    if any(w in low for w in ["sigmoid", "olasılık", "olasilik", "logistic"]):
        base = f"sigmoid({base})"
    elif any(w in low for w in ["tanh", "hiperbolik"]):
        base = f"tanh({base})"
    elif any(w in low for w in ["relu", "negatifleri sıfırla", "pozitif"]):
        base = f"relu({base})"

    # Clamp detection in natural language (e.g., "0 ile 1 arasına sınırla")
    clamp_match = re.search(
        r"([+-]?\d+(?:\.\d+)?)\s*(?:ile|ve)\s*([+-]?\d+(?:\.\d+)?)\s*aras[ıi]na?\s*s[ıi]n[ıi]rla",
        low,
    )
    if clamp_match:
        lo_s, hi_s = clamp_match.group(1), clamp_match.group(2)
        base = f"clamp({base}, {lo_s}, {hi_s})"

    return base, bias_val


def parse_declarative_sx(raw_text: str, default_name: str = "intent_kernel") -> SynaxIR:
    """
    Parse declarative `.sx` scripts (`niyet:`, `kural:`, `hedef:`, `formül:`)
    or single-line natural-language/symbolic prompts.
    """
    fields: Dict[str, List[str]] = {"niyet": [], "kural": [], "hedef": [], "formul": []}
    plain_lines: List[str] = []

    for raw_line in raw_text.splitlines():
        s = raw_line.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        m = re.match(r"^(niyet|intent|kural|rule|hedef|target|formül|formul|formula|akis|flow|expr)\s*:\s*(.+)$", s, re.I)
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key in ("niyet", "intent"):
                fields["niyet"].append(val)
            elif key in ("kural", "rule"):
                fields["kural"].append(val)
            elif key in ("hedef", "target"):
                fields["hedef"].append(val)
            else:
                fields["formul"].append(val)
        else:
            plain_lines.append(s)

    niyet_str = " ".join(fields["niyet"]) if fields["niyet"] else " ".join(plain_lines)
    if not niyet_str and not fields["formul"]:
        raise SyntaxError("Boş .sx dosyası: 'niyet:' satırı veya geçerli bir ifade bulunamadı.")

    kural_str = " ".join(fields["kural"])
    hedef_str = " ".join(fields["hedef"])
    explicit_expr = " ".join(fields["formul"]) if fields["formul"] else None

    safety = _infer_declarative_safety(kural_str)
    symbolic_expr, bias_val = _infer_declarative_symbolic_expr(niyet_str, explicit_expr)

    raw_ast = parse_symbolic_expression(symbolic_expr)
    simplified = raw_ast.simplify(allow_nonfinite_fold=safety.guarantees_finite_inputs())

    ok, reason = SynaxSecurityGuard.verify_c_expression(simplified.to_c_scalar())
    if not ok:
        raise ValueError(f"[SYNAX-SEC] Güvenli olmayan ifade engellendi: {reason}")

    target_hint = "auto"
    h_low = hedef_str.lower()
    if "mcu" in h_low and "m1" not in h_low and "neon" not in h_low:
        target_hint = "scalar"
    elif h_low.strip() == "neon":
        target_hint = "neon"

    clean_name = re.sub(r"[^A-Za-z0-9_]+", "_", default_name).strip("_") or "intent_kernel"

    return SynaxIR(
        name=clean_name,
        syntax_format="declarative_intent",
        version="0.5",
        param_names=("a", "b"),
        intent_text=niyet_str or symbolic_expr,
        rule_text=kural_str or "preserve",
        target_hint=target_hint,
        optimize_goal="throughput",
        bias_default=bias_val,
        safety=safety,
        expr=simplified,
    )


def parse_sx(source_or_path: str) -> SynaxIR:
    """
    Universal entrypoint: accepts either a file path to a `.sx` file or raw `.sx` source text,
    auto-detects Structured (`synax 0.1` / `kernel ...`) vs Declarative (`niyet:` / `kural:`),
    and returns a validated `SynaxIR`.
    """
    default_name = "synax_program"
    if "\n" not in source_or_path and os.path.exists(source_or_path):
        p = Path(source_or_path)
        default_name = p.stem
        raw_text = p.read_text(encoding="utf-8")
    elif "\n" not in source_or_path and source_or_path.strip().lower().endswith(".sx"):
        raise FileNotFoundError(f".sx kaynak dosyası bulunamadı: {source_or_path}")
    else:
        raw_text = source_or_path

    stripped = _strip_line_comments(raw_text).strip()
    if re.search(r"^\s*synax\s+\d", stripped) or re.search(r"\bkernel\s+[A-Za-z_]\w*\s*\(", stripped):
        return parse_structured_sx(raw_text)
    return parse_declarative_sx(raw_text, default_name=default_name)
