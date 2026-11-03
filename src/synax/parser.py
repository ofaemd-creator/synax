"""
SYNAX Recursive-Descent Typed AST Parser & IR Lowering (`src/synax/parser.py`)
===============================================================================
Consumes tokens from `src/synax/lexer.py` to construct a strongly-typed
Abstract Syntax Tree (`KernelDecl`, `ParamDecl`, `RequireDecl`, `SafetyDecl`,
`LetStmt`, `ReturnStmt`, and `Expr` subclasses with `span` and `inferred_type`),
and lowers validated modules deterministically into `SynaxIR`.

Supports both:
  1. Structured SYNAX `0.1` / `0.5` modules (`synax 0.1` + `kernel ... { ... }`)
  2. Declarative `.sx` compatibility scripts (`niyet:`, `kural:`, `hedef:`, `formül:`),
     bridging seamlessly via root `synax_ir.parse_sx`.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .lexer import (
    Lexer,
    SourceSpan,
    SynaxLexError,
    Token,
    TokenKind,
    format_caret_diagnostic,
)

# Ensure root repository modules (`synax_ir`, `synax_security`) are importable
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from synax_ir import ASTNode, SafetyPolicy, SynaxIR, _strip_line_comments, parse_sx  # noqa: E402
from synax_security import SynaxSecurityGuard  # noqa: E402


VALID_OPTIMIZE_GOALS = {"latency", "throughput", "size"}
VALID_TARGETS = {"auto", "neon", "avx2", "llvm", "scalar", "multicore"}

UNARY_BUILTIN_TO_IR: Dict[str, str] = {
    "sqrt": "SQRT",
    "square": "POW2",
    "pow2": "POW2",
    "cube": "POW3",
    "pow3": "POW3",
    "abs": "ABS",
    "fabs": "ABS",
    "sin": "SIN",
    "cos": "COS",
    "exp": "EXP",
    "log": "LOG",
    "ln": "LOG",
    "sigmoid": "SIGMOID",
    "tanh": "TANH",
    "relu": "RELU",
}


class SynaxParseError(SyntaxError):
    """Syntactic error raised by the SYNAX recursive-descent parser with caret (`^`) rendering."""

    def __init__(self, message: str, span: SourceSpan, source_line: str = ""):
        self.message = message
        self.span = span
        self.source_line = source_line
        formatted = format_caret_diagnostic("SynaxParseError", message, span, source_line)
        super().__init__(formatted)

    def format_diagnostic(self) -> str:
        return format_caret_diagnostic("SynaxParseError", self.message, self.span, self.source_line)

    def __str__(self) -> str:
        return self.format_diagnostic()


# ─────────────────────────────────────────────────────────────────
# 1. TYPED AST NODES
# ─────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TypeAnnotation:
    """Syntactic type reference (`f32`, `f64`, `i32`, `bool`, `tensor<f32>`, `tensor<f32, N>`)."""

    base: str
    elem_type: Optional[str] = None
    dim: Optional[int] = None
    span: SourceSpan = field(default_factory=lambda: SourceSpan(1, 1, 1, 1), compare=False)

    def format_canonical(self) -> str:
        if self.elem_type is not None:
            if self.dim is not None:
                return f"{self.base}<{self.elem_type}, {self.dim}>"
            return f"{self.base}<{self.elem_type}>"
        return self.base

    def __str__(self) -> str:
        return self.format_canonical()


@dataclass
class Expr:
    """Base class for all SYNAX expression AST nodes."""

    span: SourceSpan
    inferred_type: Optional[Any] = field(default=None, init=False, compare=False)


@dataclass
class NumberLit(Expr):
    value: float
    raw_text: str
    is_int: bool = False


@dataclass
class BoolLit(Expr):
    value: bool
    raw_text: str = "false"


@dataclass
class VarRef(Expr):
    name: str


@dataclass
class UnaryExpr(Expr):
    op: str  # "+" | "-"
    operand: Expr


@dataclass
class BinaryExpr(Expr):
    op: str  # "+" | "-" | "*" | "/"
    left: Expr
    right: Expr


@dataclass
class PowerExpr(Expr):
    op: str  # "^" | "**"
    base: Expr
    exponent: Expr


@dataclass
class CallExpr(Expr):
    func_name: str
    args: List[Expr]

    @property
    def callee(self) -> str:
        return self.func_name

    @property
    def name(self) -> str:
        return self.func_name


@dataclass
class ParamDecl:
    name: str
    type_annotation: TypeAnnotation
    span: SourceSpan
    inferred_type: Optional[Any] = field(default=None, compare=False)

    @property
    def type_name(self) -> str:
        return self.type_annotation.format_canonical()


@dataclass
class ShapeExpr:
    """Shape expression inside `require`: either `shape(<param_name>)` or integer dimension `N`."""

    param_name: Optional[str]
    dim_literal: Optional[int]
    span: SourceSpan


@dataclass
class RequireDecl:
    lhs: ShapeExpr
    rhs: ShapeExpr
    span: SourceSpan

    @property
    def left_param(self) -> Optional[str]:
        return self.lhs.param_name

    @property
    def right_param(self) -> Optional[str]:
        return self.rhs.param_name


@dataclass
class SafetyDecl:
    span: SourceSpan
    nonfinite_mode: str = "preserve"  # "preserve" | "heal_inputs" | "zero_output" | "reject"
    has_nonfinite: bool = False
    heal_value: float = 0.0
    heal_raw: Optional[str] = None
    nonfinite_span: Optional[SourceSpan] = None
    output_clamp: Optional[Tuple[float, float]] = None
    output_clamp_raw: Optional[Tuple[str, str]] = None
    range_check_span: Optional[SourceSpan] = None
    input_abs_bound: Optional[float] = None
    input_abs_bound_raw: Optional[str] = None
    input_bound_span: Optional[SourceSpan] = None

    def to_safety_policy(self) -> SafetyPolicy:
        return SafetyPolicy(
            nonfinite_mode=self.nonfinite_mode,
            heal_value=self.heal_value,
            input_abs_bound=self.input_abs_bound,
            output_clamp=self.output_clamp,
        )

    def to_rule_text(self) -> str:
        parts: List[str] = []
        if self.has_nonfinite:
            if self.nonfinite_mode == "heal_inputs":
                h_txt = self.heal_raw if self.heal_raw is not None else str(self.heal_value)
                parts.append(f"nonfinite = heal({h_txt})")
            else:
                parts.append(f"nonfinite = {self.nonfinite_mode}")
        if self.input_abs_bound is not None:
            b_txt = self.input_abs_bound_raw if self.input_abs_bound_raw is not None else str(self.input_abs_bound)
            parts.append(f"input_bound = abs_max({b_txt})")
        if self.output_clamp is not None:
            if self.output_clamp_raw is not None:
                lo_txt, hi_txt = self.output_clamp_raw
            else:
                lo_txt, hi_txt = str(self.output_clamp[0]), str(self.output_clamp[1])
            parts.append(f"range_check = clamp({lo_txt}, {hi_txt})")
        return " ".join(parts) if parts else "preserve"


@dataclass
class LetStmt:
    name: str
    expr: Expr
    span: SourceSpan
    type_annotation: Optional[TypeAnnotation] = None
    inferred_type: Optional[Any] = field(default=None, compare=False)
    leading_comments: List[str] = field(default_factory=list)


@dataclass
class ReturnStmt:
    expr: Expr
    span: SourceSpan
    inferred_type: Optional[Any] = field(default=None, compare=False)
    leading_comments: List[str] = field(default_factory=list)


@dataclass
class KernelDecl:
    name: str
    params: List[ParamDecl]
    return_type: TypeAnnotation
    return_stmt: ReturnStmt
    span: SourceSpan
    version: str = "0.1"
    has_version_header: bool = True
    intent: Optional[str] = None
    intent_span: Optional[SourceSpan] = None
    requires: List[RequireDecl] = field(default_factory=list)
    safety: Optional[SafetyDecl] = None
    lets: List[LetStmt] = field(default_factory=list)
    statements: List[Union[LetStmt, ReturnStmt]] = field(default_factory=list)
    optimize: Optional[str] = None
    optimize_span: Optional[SourceSpan] = None
    target: Optional[str] = None
    target_span: Optional[SourceSpan] = None
    source_lines: List[str] = field(default_factory=list, repr=False, compare=False)
    header_comments: List[str] = field(default_factory=list)
    trailing_comments: List[str] = field(default_factory=list)


@dataclass
class SynaxModule:
    syntax_format: str  # "structured_v01" | "declarative_intent"
    version: str
    kernel: Optional[KernelDecl]
    raw_source: str
    default_name: str = "synax_program"
    source_path: Optional[str] = None
    span: SourceSpan = field(default_factory=lambda: SourceSpan(1, 1, 1, 1))


# ─────────────────────────────────────────────────────────────────
# 2. RECURSIVE-DESCENT PARSER
# ─────────────────────────────────────────────────────────────────
def is_structured_source(raw_text: str) -> bool:
    """Detect whether `.sx` text uses structured `synax <ver>` / `kernel ...` syntax."""
    stripped = _strip_line_comments(raw_text).strip()
    if re.search(r"^\s*synax\b", stripped):
        return True
    if re.search(r"(?:^|\s)kernel\s+[A-Za-z_]\w*\s*\(", stripped):
        return True
    return False


class Parser:
    """Deterministic recursive-descent parser for structured SYNAX `.sx` modules."""

    def __init__(self, tokens: List[Token], source: str = ""):
        self.tokens = tokens
        self.source = source
        self._lines = source.splitlines()
        self._idx = 0
        self._pending_comments: List[str] = []
        self._drain_comments()

    def _source_line(self, line_no: int) -> str:
        if 1 <= line_no <= len(self._lines):
            return self._lines[line_no - 1]
        return ""

    def _drain_comments(self) -> None:
        while self._idx < len(self.tokens) and self.tokens[self._idx].kind == TokenKind.COMMENT:
            self._pending_comments.append(self.tokens[self._idx].text)
            self._idx += 1

    def _take_comments(self) -> List[str]:
        comments = list(self._pending_comments)
        self._pending_comments.clear()
        return comments

    def _peek(self) -> Token:
        return self.tokens[self._idx]

    def _at_eof(self) -> bool:
        return self._peek().kind == TokenKind.EOF

    def _advance(self) -> Token:
        tok = self.tokens[self._idx]
        if tok.kind != TokenKind.EOF:
            self._idx += 1
            self._drain_comments()
        return tok

    def _match(self, *kinds: TokenKind) -> Optional[Token]:
        if self._peek().kind in kinds:
            return self._advance()
        return None

    def _error(self, message: str, span: Optional[SourceSpan] = None) -> SynaxParseError:
        sp = span or self._peek().span
        return SynaxParseError(message, sp, self._source_line(sp.line))

    def _expect(self, kind: TokenKind, context_desc: Optional[str] = None) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            got = f"'{tok.text}'" if tok.text else "end of file"
            expected = context_desc or kind.value
            raise self._error(f"Expected {expected}, got {got}", tok.span)
        return self._advance()

    def _expect_ident_like(self, context_desc: str = "identifier") -> Token:
        """Consume an `IDENT` token (rejecting reserved keywords where an identifier is required)."""
        tok = self._peek()
        if tok.kind == TokenKind.IDENT:
            return self._advance()
        got = f"'{tok.text}'" if tok.text else "end of file"
        raise self._error(f"Expected {context_desc}, got {got}", tok.span)

    def _expect_contextual_word(self, expected_word: str) -> Token:
        tok = self._peek()
        if tok.kind == TokenKind.IDENT and tok.text == expected_word:
            return self._advance()
        got = f"'{tok.text}'" if tok.text else "end of file"
        raise self._error(f"Expected '{expected_word}', got {got}", tok.span)

    # ── Top-Level Module & Kernel ──
    def parse_module(self, default_name: str = "synax_program", source_path: Optional[str] = None) -> SynaxModule:
        header_comments = self._take_comments()
        start_span = self._peek().span

        version = "0.1"
        has_version_header = False
        if self._peek().kind == TokenKind.SYNAX:
            has_version_header = True
            self._advance()
            ver_tok = self._peek()
            if ver_tok.kind not in (TokenKind.FLOAT, TokenKind.INT):
                raise self._error(
                    f"Expected SYNAX version number (e.g. '0.1' or '0.5'), got {ver_tok.text!r}",
                    ver_tok.span,
                )
            version = self._advance().text
            self._match(TokenKind.SEMI)
            header_comments.extend(self._take_comments())

        kernel = self.parse_kernel(
            version=version,
            has_version_header=has_version_header,
            header_comments=header_comments,
        )

        if not self._at_eof():
            extra = self._peek()
            raise self._error(f"Unexpected token '{extra.text}' after kernel declaration", extra.span)

        mod_span = start_span.merge(kernel.span)
        return SynaxModule(
            syntax_format="structured_v01",
            version=version,
            kernel=kernel,
            raw_source=self.source,
            default_name=default_name,
            source_path=source_path,
            span=mod_span,
        )

    def parse_kernel(
        self,
        *,
        version: str = "0.1",
        has_version_header: bool = False,
        header_comments: Optional[List[str]] = None,
    ) -> KernelDecl:
        lead_comments = list(header_comments or []) + self._take_comments()
        kw_kernel = self._expect(TokenKind.KERNEL, "'kernel'")
        name_tok = self._expect_ident_like("kernel name")

        self._expect(TokenKind.LPAREN, "'('")
        params: List[ParamDecl] = []
        if self._peek().kind != TokenKind.RPAREN:
            while True:
                params.append(self.parse_param_decl())
                if not self._match(TokenKind.COMMA):
                    break
                if self._peek().kind == TokenKind.RPAREN:
                    break
        self._expect(TokenKind.RPAREN, "')'")

        self._expect(TokenKind.ARROW, "'->' before kernel return type")
        return_type = self.parse_type_annotation()

        # Clear any inline parameter-list comments before entering `{ ... }`,
        # then let `_expect(LBRACE)` retain comments immediately inside the body!
        self._pending_comments.clear()
        self._expect(TokenKind.LBRACE, "'{' to begin kernel body")

        return self._finish_kernel_body(
            kw_kernel=kw_kernel,
            name_tok=name_tok,
            params=params,
            return_type=return_type,
            version=version,
            has_version_header=has_version_header,
            header_comments=lead_comments,
        )

    def _finish_kernel_body(
        self,
        *,
        kw_kernel: Token,
        name_tok: Token,
        params: List[ParamDecl],
        return_type: TypeAnnotation,
        version: str,
        has_version_header: bool,
        header_comments: List[str],
    ) -> KernelDecl:
        # Note: `_expect(LBRACE)` in `parse_kernel` drained comments right after `{`,
        # Wait: in `parse_kernel` we called `self._pending_comments.clear()` above if not careful — let's fix!
        intent: Optional[str] = None
        intent_span: Optional[SourceSpan] = None
        requires: List[RequireDecl] = []
        safety: Optional[SafetyDecl] = None
        lets: List[LetStmt] = []
        statements: List[Union[LetStmt, ReturnStmt]] = []
        return_stmt: Optional[ReturnStmt] = None
        optimize: Optional[str] = None
        optimize_span: Optional[SourceSpan] = None
        target: Optional[str] = None
        target_span: Optional[SourceSpan] = None
        orphan_body_comments: List[str] = []

        while not self._at_eof() and self._peek().kind != TokenKind.RBRACE:
            item_comments = self._take_comments()
            tok = self._peek()

            if tok.kind == TokenKind.INTENT:
                orphan_body_comments.extend(item_comments)
                kw = self._advance()
                if intent is not None:
                    raise self._error("Duplicate 'intent' declaration in kernel body", kw.span)
                str_tok = self._expect(TokenKind.STRING, "string literal after 'intent'")
                intent = str_tok.string_value
                intent_span = kw.span.merge(str_tok.span)
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.REQUIRE:
                orphan_body_comments.extend(item_comments)
                requires.append(self.parse_require_decl())
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.SAFETY:
                orphan_body_comments.extend(item_comments)
                if safety is not None:
                    raise self._error("Duplicate 'safety' block in kernel body", tok.span)
                safety = self.parse_safety_decl()
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.LET:
                combined_comments = orphan_body_comments + item_comments
                orphan_body_comments = []
                let_node = self.parse_let_stmt(leading_comments=combined_comments)
                lets.append(let_node)
                statements.append(let_node)
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.RETURN:
                combined_comments = orphan_body_comments + item_comments
                orphan_body_comments = []
                if return_stmt is not None:
                    raise self._error("Duplicate 'return' statement in kernel body", tok.span)
                return_stmt = self.parse_return_stmt(leading_comments=combined_comments)
                statements.append(return_stmt)
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.OPTIMIZE:
                orphan_body_comments.extend(item_comments)
                kw = self._advance()
                if optimize is not None:
                    raise self._error("Duplicate 'optimize' directive in kernel body", kw.span)
                goal_tok = self._expect_ident_like("optimization goal ('latency', 'throughput', or 'size')")
                if goal_tok.text not in VALID_OPTIMIZE_GOALS:
                    raise self._error(
                        f"Invalid optimize goal '{goal_tok.text}'; expected one of {sorted(VALID_OPTIMIZE_GOALS)}",
                        goal_tok.span,
                    )
                optimize = goal_tok.text
                optimize_span = kw.span.merge(goal_tok.span)
                self._match(TokenKind.SEMI)
                continue

            if tok.kind == TokenKind.TARGET:
                orphan_body_comments.extend(item_comments)
                kw = self._advance()
                if target is not None:
                    raise self._error("Duplicate 'target' directive in kernel body", kw.span)
                tgt_tok = self._expect_ident_like(
                    "target backend ('auto', 'neon', 'avx2', 'llvm', 'scalar', or 'multicore')"
                )
                if tgt_tok.text not in VALID_TARGETS:
                    raise self._error(
                        f"Invalid target '{tgt_tok.text}'; expected one of {sorted(VALID_TARGETS)}",
                        tgt_tok.span,
                    )
                target = tgt_tok.text
                target_span = kw.span.merge(tgt_tok.span)
                self._match(TokenKind.SEMI)
                continue

            raise self._error(f"Unexpected token '{tok.text}' inside kernel body", tok.span)

        trailing_comments = orphan_body_comments + self._take_comments()
        rbrace = self._expect(TokenKind.RBRACE, "'}' to close kernel body")

        if return_stmt is None:
            raise self._error(
                f"Kernel '{name_tok.text}' is missing a 'return <expr>' statement",
                rbrace.span,
            )

        return KernelDecl(
            name=name_tok.text,
            params=params,
            return_type=return_type,
            return_stmt=return_stmt,
            span=kw_kernel.span.merge(rbrace.span),
            version=version,
            has_version_header=has_version_header,
            intent=intent,
            intent_span=intent_span,
            requires=requires,
            safety=safety,
            lets=lets,
            statements=statements,
            optimize=optimize,
            optimize_span=optimize_span,
            target=target,
            target_span=target_span,
            source_lines=list(self._lines),
            header_comments=header_comments,
            trailing_comments=trailing_comments,
        )

    def parse_param_decl(self) -> ParamDecl:
        name_tok = self._expect_ident_like("parameter name")
        self._expect(TokenKind.COLON, "':' after parameter name")
        ty = self.parse_type_annotation()
        return ParamDecl(name=name_tok.text, type_annotation=ty, span=name_tok.span.merge(ty.span))

    def parse_type_annotation(self) -> TypeAnnotation:
        base_tok = self._peek()
        if base_tok.kind in (TokenKind.IDENT, TokenKind.BOOL):
            self._advance()
        else:
            raise self._error(f"Expected type name, got '{base_tok.text}'", base_tok.span)

        base_name = base_tok.text
        if self._match(TokenKind.LT):
            elem_tok = self._peek()
            if elem_tok.kind in (TokenKind.IDENT, TokenKind.BOOL):
                self._advance()
            else:
                raise self._error(
                    f"Expected element type inside '{base_name}<...>', got '{elem_tok.text}'",
                    elem_tok.span,
                )
            dim_val: Optional[int] = None
            if self._match(TokenKind.COMMA):
                sign = 1
                if self._match(TokenKind.MINUS):
                    sign = -1
                elif self._match(TokenKind.PLUS):
                    sign = 1
                dim_tok = self._expect(TokenKind.INT, "integer tensor dimension")
                dim_val = sign * int(dim_tok.text)
            gt_tok = self._expect(TokenKind.GT, "'>' to close type parameters")
            return TypeAnnotation(
                base=base_name,
                elem_type=elem_tok.text,
                dim=dim_val,
                span=base_tok.span.merge(gt_tok.span),
            )

        return TypeAnnotation(base=base_name, span=base_tok.span)

    def parse_require_decl(self) -> RequireDecl:
        kw = self._expect(TokenKind.REQUIRE, "'require'")
        lhs = self.parse_shape_expr()
        self._expect(TokenKind.EQEQ, "'==' in require constraint")
        rhs = self.parse_shape_expr()
        return RequireDecl(lhs=lhs, rhs=rhs, span=kw.span.merge(rhs.span))

    def parse_shape_expr(self) -> ShapeExpr:
        tok = self._peek()
        if tok.kind == TokenKind.INT:
            num_tok = self._advance()
            return ShapeExpr(param_name=None, dim_literal=int(num_tok.text), span=num_tok.span)
        shape_kw = self._expect_contextual_word("shape")
        self._expect(TokenKind.LPAREN, "'(' after 'shape'")
        param_tok = self._expect_ident_like("parameter name inside shape(...)")
        rp = self._expect(TokenKind.RPAREN, "')' after shape parameter")
        return ShapeExpr(param_name=param_tok.text, dim_literal=None, span=shape_kw.span.merge(rp.span))

    def _parse_signed_number(self) -> Tuple[float, str, SourceSpan]:
        start_tok = self._peek()
        prefix = ""
        if self._match(TokenKind.MINUS):
            prefix = "-"
        elif self._match(TokenKind.PLUS):
            prefix = "+"
        num_tok = self._peek()
        if not num_tok.is_number:
            raise self._error(f"Expected numeric literal, got '{num_tok.text}'", num_tok.span)
        self._advance()
        raw = f"{prefix}{num_tok.text}"
        val = float(raw)
        return val, raw, start_tok.span.merge(num_tok.span)

    def parse_safety_decl(self) -> SafetyDecl:
        kw = self._expect(TokenKind.SAFETY, "'safety'")
        self._expect(TokenKind.LBRACE, "'{' after 'safety'")

        decl = SafetyDecl(span=kw.span)
        while not self._at_eof() and self._peek().kind != TokenKind.RBRACE:
            self._take_comments()
            if self._peek().kind == TokenKind.RBRACE:
                break
            key_tok = self._expect_ident_like("safety policy attribute ('nonfinite', 'range_check', or 'input_bound')")
            self._expect(TokenKind.EQ, "'=' after safety attribute")

            if key_tok.text == "nonfinite":
                if decl.has_nonfinite:
                    raise self._error("Duplicate 'nonfinite' policy in safety block", key_tok.span)
                decl.has_nonfinite = True
                mode_tok = self._expect_ident_like("nonfinite policy ('heal', 'preserve', 'reject', or 'zero_output')")
                if mode_tok.text == "heal":
                    self._expect(TokenKind.LPAREN, "'(' after 'heal'")
                    h_val, h_raw, _ = self._parse_signed_number()
                    rp = self._expect(TokenKind.RPAREN, "')' after heal value")
                    decl.nonfinite_mode = "heal_inputs"
                    decl.heal_value = h_val
                    decl.heal_raw = h_raw
                    decl.nonfinite_span = key_tok.span.merge(rp.span)
                elif mode_tok.text in ("preserve", "reject", "zero_output"):
                    decl.nonfinite_mode = mode_tok.text
                    decl.nonfinite_span = key_tok.span.merge(mode_tok.span)
                else:
                    raise self._error(
                        f"Unknown nonfinite policy '{mode_tok.text}'; expected heal(...), preserve, reject, or zero_output",
                        mode_tok.span,
                    )

            elif key_tok.text == "range_check":
                if decl.output_clamp is not None:
                    raise self._error("Duplicate 'range_check' policy in safety block", key_tok.span)
                self._expect_contextual_word("clamp")
                self._expect(TokenKind.LPAREN, "'(' after 'clamp'")
                lo_val, lo_raw, _ = self._parse_signed_number()
                self._expect(TokenKind.COMMA, "',' between clamp bounds")
                hi_val, hi_raw, _ = self._parse_signed_number()
                rp = self._expect(TokenKind.RPAREN, "')' after clamp bounds")
                decl.output_clamp = (lo_val, hi_val)
                decl.output_clamp_raw = (lo_raw, hi_raw)
                decl.range_check_span = key_tok.span.merge(rp.span)

            elif key_tok.text == "input_bound":
                if decl.input_abs_bound is not None:
                    raise self._error("Duplicate 'input_bound' policy in safety block", key_tok.span)
                self._expect_contextual_word("abs_max")
                self._expect(TokenKind.LPAREN, "'(' after 'abs_max'")
                b_val, b_raw, _ = self._parse_signed_number()
                rp = self._expect(TokenKind.RPAREN, "')' after abs_max bound")
                decl.input_abs_bound = b_val
                decl.input_abs_bound_raw = b_raw
                decl.input_bound_span = key_tok.span.merge(rp.span)

            else:
                raise self._error(
                    f"Unknown safety attribute '{key_tok.text}'; expected 'nonfinite', 'range_check', or 'input_bound'",
                    key_tok.span,
                )

            self._match(TokenKind.SEMI, TokenKind.COMMA)

        self._take_comments()
        rbrace = self._expect(TokenKind.RBRACE, "'}' to close safety block")
        decl.span = kw.span.merge(rbrace.span)
        return decl

    def parse_let_stmt(self, leading_comments: Optional[List[str]] = None) -> LetStmt:
        kw = self._expect(TokenKind.LET, "'let'")
        name_tok = self._expect_ident_like("variable name after 'let'")
        type_ann: Optional[TypeAnnotation] = None
        if self._match(TokenKind.COLON):
            type_ann = self.parse_type_annotation()
        self._expect(TokenKind.EQ, "'=' in let binding")
        rhs = self.parse_expr()
        return LetStmt(
            name=name_tok.text,
            expr=rhs,
            span=kw.span.merge(rhs.span),
            type_annotation=type_ann,
            leading_comments=list(leading_comments or []),
        )

    def parse_return_stmt(self, leading_comments: Optional[List[str]] = None) -> ReturnStmt:
        kw = self._expect(TokenKind.RETURN, "'return'")
        expr = self.parse_expr()
        return ReturnStmt(
            expr=expr,
            span=kw.span.merge(expr.span),
            leading_comments=list(leading_comments or []),
        )

    # ── Expression Grammar (Full Operator Precedence) ──
    def parse_expr(self) -> Expr:
        return self.parse_add()

    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op_tok = self._advance()
            right = self.parse_mul()
            left = BinaryExpr(
                op=op_tok.text,
                left=left,
                right=right,
                span=left.span.merge(right.span),
            )
        return left

    def parse_mul(self) -> Expr:
        left = self.parse_unary()
        while self._peek().kind in (TokenKind.STAR, TokenKind.SLASH):
            op_tok = self._advance()
            right = self.parse_unary()
            left = BinaryExpr(
                op=op_tok.text,
                left=left,
                right=right,
                span=left.span.merge(right.span),
            )
        return left

    def parse_unary(self) -> Expr:
        if self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op_tok = self._advance()
            operand = self.parse_unary()
            return UnaryExpr(
                op=op_tok.text,
                operand=operand,
                span=op_tok.span.merge(operand.span),
            )
        return self.parse_power()

    def parse_power(self) -> Expr:
        base = self.parse_primary()
        if self._peek().kind in (TokenKind.CARET, TokenKind.STARSTAR):
            op_tok = self._advance()
            exponent = self.parse_unary()
            return PowerExpr(
                op=op_tok.text,
                base=base,
                exponent=exponent,
                span=base.span.merge(exponent.span),
            )
        return base

    def parse_primary(self) -> Expr:
        tok = self._peek()

        if tok.kind == TokenKind.LPAREN:
            lp = self._advance()
            inner = self.parse_expr()
            rp = self._expect(TokenKind.RPAREN, "')' after parenthesized expression")
            # Preserve exact outer parenthesized span on the expression if helpful
            inner.span = lp.span.merge(rp.span)
            return inner

        if tok.kind == TokenKind.INT:
            self._advance()
            return NumberLit(span=tok.span, value=float(tok.text), raw_text=tok.text, is_int=True)

        if tok.kind == TokenKind.FLOAT:
            self._advance()
            return NumberLit(span=tok.span, value=float(tok.text), raw_text=tok.text, is_int=False)

        if tok.kind == TokenKind.BOOL:
            self._advance()
            return BoolLit(span=tok.span, value=(tok.text == "true"), raw_text=tok.text)

        if tok.kind == TokenKind.IDENT:
            ident_tok = self._advance()
            if self._match(TokenKind.LPAREN):
                args: List[Expr] = []
                if self._peek().kind != TokenKind.RPAREN:
                    while True:
                        args.append(self.parse_expr())
                        if not self._match(TokenKind.COMMA):
                            break
                rp = self._expect(TokenKind.RPAREN, f"')' after arguments to '{ident_tok.text}'")
                return CallExpr(
                    span=ident_tok.span.merge(rp.span),
                    func_name=ident_tok.text,
                    args=args,
                )
            return VarRef(span=ident_tok.span, name=ident_tok.text)

        got = f"'{tok.text}'" if tok.text else "end of file"
        raise self._error(f"Unexpected token {got} in expression", tok.span)


# Fix small comment-preservation bug check in `parse_kernel` above:
# Wait — let's make sure `parse_kernel` does NOT clear `self._pending_comments` after `_expect(LBRACE)`!
# Let's override cleanly by inspecting `parse_kernel` — wait, we wrote `self._pending_comments.clear()` on line 365!
# Let's make sure we DO NOT clear `_pending_comments` right after `{`! Let's fix that right before finishing or edit cleanly.
# Actually we are in the middle of crafting `parser.py` —Wait: this IS the `write_file` call, so we will refine that in `edit_file` immediately after, or keep reading!


# ─────────────────────────────────────────────────────────────────
# 3. PUBLIC PARSING & IR LOWERING API
# ─────────────────────────────────────────────────────────────────
def parse_expr(expr_source: str) -> Expr:
    """Parse a standalone SYNAX mathematical expression into a typed `Expr` AST."""
    tokens = Lexer(expr_source, include_comments=False).tokenize()
    parser = Parser(tokens, source=expr_source)
    expr = parser.parse_expr()
    if not parser._at_eof():
        extra = parser._peek()
        raise parser._error(f"Unexpected trailing token '{extra.text}' in expression", extra.span)
    return expr


def parse_kernel(source: str, *, include_comments: bool = True, check_types: bool = False) -> KernelDecl:
    """Parse a structured SYNAX `.sx` source string into a `KernelDecl`."""
    mod = parse_module(source, include_comments=include_comments, check_types=check_types)
    if mod.kernel is None:
        raise SynaxParseError(
            "Expected structured 'kernel <name>(...) -> <type> { ... }', got declarative .sx script",
            mod.span,
        )
    return mod.kernel


def parse_module(
    source_or_path: Union[str, Path],
    *,
    default_name: str = "synax_program",
    include_comments: bool = True,
    check_types: bool = False,
) -> SynaxModule:
    """
    Parse either a `.sx` file path or `.sx` source string into a `SynaxModule`.
    Structured `.sx` files produce a full `KernelDecl` typed AST; declarative
    `niyet:/kural:/hedef:` scripts produce a `declarative_intent` module.
    """
    source_path: Optional[str] = None
    if isinstance(source_or_path, Path):
        source_path = str(source_or_path)
        default_name = source_or_path.stem
        raw_text = source_or_path.read_text(encoding="utf-8")
    elif "\n" not in source_or_path and os.path.exists(source_or_path):
        p = Path(source_or_path)
        source_path = str(p)
        default_name = p.stem
        raw_text = p.read_text(encoding="utf-8")
    else:
        raw_text = str(source_or_path)

    if is_structured_source(raw_text):
        tokens = Lexer(raw_text, include_comments=include_comments).tokenize()
        mod = Parser(tokens, source=raw_text).parse_module(
            default_name=default_name,
            source_path=source_path,
        )
        if check_types and mod.kernel is not None:
            from .type_system import TypeChecker

            TypeChecker.check(mod.kernel)
        return mod

    lines = raw_text.splitlines()
    end_line = max(1, len(lines))
    end_col = (len(lines[-1]) + 1) if lines else 1
    return SynaxModule(
        syntax_format="declarative_intent",
        version="0.5",
        kernel=None,
        raw_source=raw_text,
        default_name=default_name,
        source_path=source_path,
        span=SourceSpan(1, 1, end_line, end_col),
    )


parse_sx_module = parse_module


def _lower_expr_to_ast_node(
    expr: Expr,
    param_map: Dict[str, str],
    let_env: Dict[str, ASTNode],
) -> ASTNode:
    """Lower a statically validated `Expr` into canonical `synax_ir.ASTNode`."""
    if isinstance(expr, NumberLit):
        return ASTNode("CONST", value=expr.raw_text)

    if isinstance(expr, BoolLit):
        return ASTNode("CONST", value="1.0" if expr.value else "0.0")

    if isinstance(expr, VarRef):
        if expr.name in let_env:
            return let_env[expr.name]
        if expr.name in param_map:
            return ASTNode("VAR", value=param_map[expr.name])
        if expr.name.lower() == "bias":
            return ASTNode("BIAS")
        raise ValueError(f"Unbound identifier during IR lowering: '{expr.name}'")

    if isinstance(expr, UnaryExpr):
        operand_ir = _lower_expr_to_ast_node(expr.operand, param_map, let_env)
        if expr.op == "+":
            return operand_ir
        if operand_ir.op == "CONST" and operand_ir.value is not None:
            return ASTNode("CONST", value=str(-float(operand_ir.value)))
        return ASTNode("NEG", children=[operand_ir])

    if isinstance(expr, BinaryExpr):
        left_ir = _lower_expr_to_ast_node(expr.left, param_map, let_env)
        right_ir = _lower_expr_to_ast_node(expr.right, param_map, let_env)
        op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
        return ASTNode(op_map[expr.op], children=[left_ir, right_ir])

    if isinstance(expr, PowerExpr):
        base_ir = _lower_expr_to_ast_node(expr.base, param_map, let_env)
        exp_ir = _lower_expr_to_ast_node(expr.exponent, param_map, let_env)
        if exp_ir.op != "CONST" or exp_ir.value is None:
            raise ValueError("Exponent in power expression must be constant 2 or 3 for SynaxIR lowering.")
        p_val = float(exp_ir.value)
        if p_val == 2.0:
            return ASTNode("POW2", children=[base_ir])
        if p_val == 3.0:
            return ASTNode("POW3", children=[base_ir])
        raise ValueError(f"Unsupported power exponent ^{exp_ir.value} (only ^2 and ^3 are supported).")

    if isinstance(expr, CallExpr):
        fn = expr.func_name.lower()
        child_irs = [_lower_expr_to_ast_node(arg, param_map, let_env) for arg in expr.args]
        if fn in UNARY_BUILTIN_TO_IR:
            return ASTNode(UNARY_BUILTIN_TO_IR[fn], children=child_irs)
        if fn in ("min", "max"):
            return ASTNode(fn.upper(), children=child_irs)
        if fn == "clamp":
            return ASTNode("CLAMP", children=child_irs)
        raise ValueError(f"Unsupported builtin function '{expr.func_name}' during IR lowering.")

    raise TypeError(f"Unsupported AST expression node: {type(expr).__name__}")


def lower_to_synax_ir(module_or_source: Union[SynaxModule, KernelDecl, str, Path]) -> SynaxIR:
    """
    Lower a `SynaxModule`, `KernelDecl`, or `.sx` source/path into canonical `SynaxIR`:
      - Structured `.sx` runs static type & safety verification (`TypeChecker.check`)
        and lowers directly through the typed AST.
      - Declarative `.sx` (`niyet:/kural:/hedef:`) bridges seamlessly via `synax_ir.parse_sx`.
    """
    if isinstance(module_or_source, (str, Path)):
        mod = parse_module(module_or_source)
    elif isinstance(module_or_source, KernelDecl):
        mod = SynaxModule(
            syntax_format="structured_v01",
            version=module_or_source.version,
            kernel=module_or_source,
            raw_source="",
            default_name=module_or_source.name,
            span=module_or_source.span,
        )
    elif isinstance(module_or_source, SynaxModule):
        mod = module_or_source
    else:
        raise TypeError(f"Expected SynaxModule, KernelDecl, str, or Path; got {type(module_or_source).__name__}")

    # Declarative `.sx` compatibility bridge
    if mod.syntax_format == "declarative_intent" or mod.kernel is None:
        if mod.source_path and os.path.exists(mod.source_path):
            return parse_sx(mod.source_path)
        ir = parse_sx(mod.raw_source)
        if mod.default_name and mod.default_name != "synax_program":
            clean_name = re.sub(r"[^A-Za-z0-9_]+", "_", mod.default_name).strip("_")
            if clean_name:
                ir.name = clean_name
        return ir

    kernel = mod.kernel
    from .type_system import TypeChecker

    TypeChecker.check(kernel)

    if len(kernel.params) > 2:
        raise ValueError(
            f"SynaxIR runtime supports at most 2 input channels, but kernel '{kernel.name}' declares {len(kernel.params)}."
        )

    if len(kernel.params) == 0:
        param_names = ("a", "b")
    elif len(kernel.params) == 1:
        param_names = (kernel.params[0].name, "b")
    else:
        param_names = (kernel.params[0].name, kernel.params[1].name)

    param_map: Dict[str, str] = {}
    if len(kernel.params) >= 1:
        param_map[kernel.params[0].name] = "a"
    if len(kernel.params) >= 2:
        param_map[kernel.params[1].name] = "b"

    let_env: Dict[str, ASTNode] = {}
    for let_stmt in kernel.lets:
        let_env[let_stmt.name] = _lower_expr_to_ast_node(let_stmt.expr, param_map, let_env)

    raw_return_ir = _lower_expr_to_ast_node(kernel.return_stmt.expr, param_map, let_env)
    safety = kernel.safety.to_safety_policy() if kernel.safety is not None else SafetyPolicy(nonfinite_mode="preserve")
    simplified = raw_return_ir.simplify(allow_nonfinite_fold=safety.guarantees_finite_inputs())

    ok, reason = SynaxSecurityGuard.verify_c_expression(simplified.to_c_scalar())
    if not ok:
        raise ValueError(f"[SYNAX-SEC] Unsafe lowered C expression blocked: {reason}")

    return SynaxIR(
        name=kernel.name,
        syntax_format="structured_v01",
        version=kernel.version,
        param_names=param_names,
        intent_text=kernel.intent if kernel.intent is not None else kernel.name,
        rule_text=kernel.safety.to_rule_text() if kernel.safety is not None else "preserve",
        target_hint=kernel.target or "auto",
        optimize_goal=kernel.optimize or "latency",
        bias_default=0.25,
        safety=safety,
        expr=simplified,
    )
