"""
SYNAX Canonical Source Formatter (`src/synax/formatter.py`)
===========================================================
Formats SYNAX (`.sx`) programs into canonical, deterministic source text:
  - Structured `synax 0.1` / `synax 0.5` modules: 2-space indentation,
    preserved `//` header and statement comments, canonicalized `safety { ... }`,
    `let`, `return`, `optimize`, `target`, and precedence-exact expressions.
  - Declarative `niyet:/kural:/hedef:/formül:` files: normalized directive
    spacing and comments without altering semantics.

Guarantees:
  1. Strict idempotence: `format_sx(format_sx(src)) == format_sx(src)`
  2. Strict semantic invariance: `parse_sx(format_sx(src)).ir_hash == parse_sx(src).ir_hash`
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional

from .parser import (
    BinaryExpr,
    BoolLit,
    CallExpr,
    Expr,
    KernelDecl,
    NumberLit,
    PowerExpr,
    RequireDecl,
    SafetyDecl,
    ShapeExpr,
    UnaryExpr,
    VarRef,
    is_structured_source,
    parse_module,
)

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# Operator precedence levels (matching `spec/synax.ebnf` and `parser.py`)
_PREC_ADD = 10
_PREC_MUL = 20
_PREC_UNARY = 30
_PREC_POW = 40
_PREC_ATOM = 50

_DECLARATIVE_KEY_RE = re.compile(
    r"^(niyet|intent|kural|rule|hedef|target|formül|formul|formula|akis|flow|expr)\s*:\s*(.*)$",
    re.IGNORECASE,
)


def _normalize_structured_comment(raw_comment: str) -> str:
    """Normalize a `//` or `#` line comment into canonical `// ...` syntax."""
    s = raw_comment.strip()
    if s.startswith("//"):
        body = s[2:].strip()
    elif s.startswith("#"):
        body = s[1:].strip()
    else:
        body = s
    return f"// {body}" if body else "//"


def _escape_string_literal(text: str) -> str:
    """Escape a string value into a canonical double-quoted SYNAX string literal."""
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _format_safety_number(val: float, raw: Optional[str]) -> str:
    """
    Format a numeric constant inside `safety { ... }` in clean decimal form
    (compatible with both `parser.py` and `synax_ir.parse_structured_sx` regexes).
    """
    if raw is not None:
        cleaned = raw.strip()
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]
        if re.match(r"^-?\d+\.\d+$", cleaned):
            return cleaned
        if re.match(r"^-?\d+$", cleaned):
            return f"{cleaned}.0"

    # Convert scientific notation or general float to clean decimal representation
    s = f"{val:.9f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    if s == "-0.0" and not str(val).startswith("-"):
        s = "0.0"
    return s


def _expr_precedence(expr: Expr) -> int:
    if isinstance(expr, BinaryExpr):
        return _PREC_ADD if expr.op in ("+", "-") else _PREC_MUL
    if isinstance(expr, UnaryExpr):
        if expr.op == "+":
            return _expr_precedence(expr.operand)
        return _PREC_UNARY
    if isinstance(expr, PowerExpr):
        return _PREC_POW
    return _PREC_ATOM


def _format_expr(expr: Expr) -> str:
    """Pretty-print an `Expr` AST preserving exact IEEE-754 evaluation grouping."""
    if isinstance(expr, NumberLit):
        return expr.raw_text.strip()

    if isinstance(expr, BoolLit):
        return "true" if expr.value else "false"

    if isinstance(expr, VarRef):
        return expr.name

    if isinstance(expr, CallExpr):
        args_str = ", ".join(_format_expr(a) for a in expr.args)
        return f"{expr.func_name}({args_str})"

    if isinstance(expr, UnaryExpr):
        if expr.op == "+":
            return _format_expr(expr.operand)
        inner = expr.operand
        inner_str = _format_expr(inner)
        inner_prec = _expr_precedence(inner)
        if isinstance(inner, UnaryExpr) or inner_prec < _PREC_UNARY:
            return f"-({inner_str})"
        return f"-{inner_str}"

    if isinstance(expr, PowerExpr):
        base_str = _format_expr(expr.base)
        if _expr_precedence(expr.base) < _PREC_POW or isinstance(expr.base, UnaryExpr):
            base_str = f"({base_str})"
        exp_str = _format_expr(expr.exponent)
        if exp_str in ("2", "2.0"):
            exp_str = "2"
        elif exp_str in ("3", "3.0"):
            exp_str = "3"
        elif _expr_precedence(expr.exponent) < _PREC_ATOM:
            exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"

    if isinstance(expr, BinaryExpr):
        my_prec = _expr_precedence(expr)
        left_str = _format_expr(expr.left)
        right_str = _format_expr(expr.right)

        # Left-associative binary ops: wrap left iff strictly lower precedence
        if _expr_precedence(expr.left) < my_prec:
            left_str = f"({left_str})"

        # Wrap right if lower OR equal precedence to preserve exact IEEE-754 tree grouping
        # (e.g., `a - (b - c)` and `a + (b + c)` remain right-grouped, while `a + b + c` stays flat!)
        if _expr_precedence(expr.right) <= my_prec or isinstance(expr.right, UnaryExpr):
            right_str = f"({right_str})"

        return f"{left_str} {expr.op} {right_str}"

    raise TypeError(f"Unsupported expression node in formatter: {type(expr).__name__}")


def _format_shape_expr(se: ShapeExpr) -> str:
    if se.param_name is not None:
        return f"shape({se.param_name})"
    return str(se.dim_literal)


def _format_require(req: RequireDecl) -> str:
    return f"  require {_format_shape_expr(req.lhs)} == {_format_shape_expr(req.rhs)}"


def _format_safety(safety: SafetyDecl) -> List[str]:
    lines = ["  safety {"]
    has_any = False

    if safety.has_nonfinite:
        has_any = True
        if safety.nonfinite_mode == "heal_inputs":
            h_str = _format_safety_number(safety.heal_value, safety.heal_raw)
            lines.append(f"    nonfinite = heal({h_str})")
        else:
            lines.append(f"    nonfinite = {safety.nonfinite_mode}")

    if safety.input_abs_bound is not None:
        has_any = True
        b_str = _format_safety_number(safety.input_abs_bound, safety.input_abs_bound_raw)
        lines.append(f"    input_bound = abs_max({b_str})")

    if safety.output_clamp is not None:
        has_any = True
        lo_raw = safety.output_clamp_raw[0] if safety.output_clamp_raw else None
        hi_raw = safety.output_clamp_raw[1] if safety.output_clamp_raw else None
        lo_str = _format_safety_number(safety.output_clamp[0], lo_raw)
        hi_str = _format_safety_number(safety.output_clamp[1], hi_raw)
        lines.append(f"    range_check = clamp({lo_str}, {hi_str})")

    if not has_any:
        lines.append("    nonfinite = preserve")

    lines.append("  }")
    return lines


def _format_structured_kernel(kernel: KernelDecl, version: str) -> str:
    out_lines: List[str] = []

    # 1. Header comments
    for c in kernel.header_comments:
        out_lines.append(_normalize_structured_comment(c))

    # 2. Version header
    out_lines.append(f"synax {version}")
    out_lines.append("")

    # 3. Kernel signature
    ret_str = kernel.return_type.format_canonical()
    if not kernel.params:
        out_lines.append(f"kernel {kernel.name}() -> {ret_str} {{")
    else:
        out_lines.append(f"kernel {kernel.name}(")
        for idx, p in enumerate(kernel.params):
            comma = "," if idx < len(kernel.params) - 1 else ""
            out_lines.append(f"  {p.name}: {p.type_annotation.format_canonical()}{comma}")
        out_lines.append(f") -> {ret_str} {{")

    # 4. Kernel body groups (separated by a single blank line)
    body_groups: List[List[str]] = []

    if kernel.intent is not None:
        body_groups.append([f"  intent {_escape_string_literal(kernel.intent)}"])

    if kernel.requires:
        body_groups.append([_format_require(req) for req in kernel.requires])

    if kernel.safety is not None:
        body_groups.append(_format_safety(kernel.safety))

    # Computation statements (`let`s + `return`)
    comp_lines: List[str] = []
    for let_stmt in kernel.lets:
        for c in let_stmt.leading_comments:
            comp_lines.append(f"  {_normalize_structured_comment(c)}")
        if let_stmt.type_annotation is not None:
            t_str = let_stmt.type_annotation.format_canonical()
            comp_lines.append(f"  let {let_stmt.name}: {t_str} = {_format_expr(let_stmt.expr)}")
        else:
            comp_lines.append(f"  let {let_stmt.name} = {_format_expr(let_stmt.expr)}")

    for c in kernel.return_stmt.leading_comments:
        comp_lines.append(f"  {_normalize_structured_comment(c)}")
    comp_lines.append(f"  return {_format_expr(kernel.return_stmt.expr)}")
    body_groups.append(comp_lines)

    # Backend directives (`optimize`, `target`)
    directives: List[str] = []
    if kernel.optimize is not None:
        directives.append(f"  optimize {kernel.optimize}")
    if kernel.target is not None:
        directives.append(f"  target {kernel.target}")
    if directives:
        body_groups.append(directives)

    # Trailing comments right before `}`
    if kernel.trailing_comments:
        body_groups.append([f"  {_normalize_structured_comment(c)}" for c in kernel.trailing_comments])

    for g_idx, grp in enumerate(body_groups):
        if g_idx > 0:
            out_lines.append("")
        out_lines.extend(grp)

    out_lines.append("}")
    return "\n".join(out_lines) + "\n"


def _format_declarative(raw_source: str) -> str:
    """
    Canonicalize a declarative `.sx` script (`niyet:`, `kural:`, `hedef:`, `formül:`):
      - Normalizes line endings, trims trailing whitespace, collapses blank-line runs
      - Normalizes `#` and `//` comments cleanly
      - Normalizes `<key> : <value>` spacing to `<key>: <normalized_value>`
    """
    normalized_lines: List[str] = []
    prev_blank = True  # suppresses leading blank lines

    for raw_line in raw_source.splitlines():
        s = raw_line.strip()
        if not s:
            if not prev_blank:
                normalized_lines.append("")
                prev_blank = True
            continue

        prev_blank = False

        if s.startswith("#"):
            body = s[1:].strip()
            normalized_lines.append(f"# {body}" if body else "#")
            continue

        if s.startswith("//"):
            body = s[2:].strip()
            normalized_lines.append(f"// {body}" if body else "//")
            continue

        m = _DECLARATIVE_KEY_RE.match(s)
        if m:
            key = m.group(1).lower()
            val = re.sub(r"[ \t]+", " ", m.group(2).strip())
            normalized_lines.append(f"{key}: {val}")
            continue

        normalized_lines.append(re.sub(r"[ \t]+", " ", s))

    while normalized_lines and normalized_lines[-1] == "":
        normalized_lines.pop()

    if not normalized_lines:
        return ""
    return "\n".join(normalized_lines) + "\n"


def format_sx(source: str) -> str:
    """
    Format raw `.sx` source text into canonical, idempotent SYNAX code while
    strictly preserving `SynaxIR` semantics and `ir_hash`.
    """
    if is_structured_source(source):
        mod = parse_module(source, include_comments=True, check_types=False)
        if mod.kernel is not None:
            return _format_structured_kernel(mod.kernel, mod.version)
    return _format_declarative(source)
