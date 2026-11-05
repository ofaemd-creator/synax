"""
SYNAX Static Type & Constraint System (`src/synax/type_system.py`)
==================================================================
Enforces compile-time type safety, lexical scoping, builtin arity, constant
domain bounds, `safety` block invariants, and `require` tensor shape checks
across structured SYNAX `KernelDecl` ASTs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .lexer import SourceSpan, format_caret_diagnostic
from .parser import (
    BinaryExpr,
    BoolLit,
    CallExpr,
    Expr,
    KernelDecl,
    LetStmt,
    NumberLit,
    PowerExpr,
    RequireDecl,
    ReturnStmt,
    SafetyDecl,
    SynaxModule,
    TypeAnnotation,
    UnaryExpr,
    VarRef,
)

SCALAR_TYPES = {"f32", "f64", "i32", "bool"}
NUMERIC_SCALARS = {"f32", "f64", "i32"}
FLOAT_SCALARS = {"f32", "f64"}

UNARY_FLOAT_BUILTINS = {
    "sqrt",
    "sin",
    "cos",
    "exp",
    "log",
    "ln",
    "sigmoid",
    "tanh",
}
UNARY_NUMERIC_BUILTINS = {
    "square",
    "pow2",
    "cube",
    "pow3",
    "abs",
    "fabs",
    "relu",
}
ALL_UNARY_BUILTINS = UNARY_FLOAT_BUILTINS | UNARY_NUMERIC_BUILTINS
BINARY_BUILTINS = {"min", "max"}
TERNARY_BUILTINS = {"clamp"}
DENDRITIC_UNARY_REDUCTIONS = {"sum", "mean", "l2_norm", "norm"}
DENDRITIC_BINARY_REDUCTIONS = {"dot"}
DENDRITIC_WINDOW_BUILTINS = {"window_mean"}


@dataclass(frozen=True)
class SynaxType:
    """Resolved static type in SYNAX (`f32`, `f64`, `i32`, `bool`, `tensor<T>`, `tensor<T, N>`)."""

    base: str
    elem_type: Optional[str] = None
    dim: Optional[int] = None

    @property
    def is_tensor(self) -> bool:
        return self.base == "tensor"

    @property
    def is_scalar(self) -> bool:
        return self.base in SCALAR_TYPES

    @property
    def scalar_dtype(self) -> str:
        return self.elem_type if self.is_tensor and self.elem_type is not None else self.base

    @property
    def is_numeric(self) -> bool:
        return self.scalar_dtype in NUMERIC_SCALARS

    @property
    def is_float(self) -> bool:
        return self.scalar_dtype in FLOAT_SCALARS

    def __str__(self) -> str:
        if self.is_tensor:
            if self.dim is not None:
                return f"tensor<{self.elem_type}, {self.dim}>"
            return f"tensor<{self.elem_type}>"
        return self.base


F32_TYPE = SynaxType("f32")
F64_TYPE = SynaxType("f64")
I32_TYPE = SynaxType("i32")
BOOL_TYPE = SynaxType("bool")
TENSOR_F32_TYPE = SynaxType("tensor", elem_type="f32")


class SynaxTypeError(TypeError):
    """Static type, arity, scoping, shape, or safety constraint error in SYNAX."""

    def __init__(self, message: str, span: Optional[SourceSpan] = None, source_line: str = ""):
        self.message = message
        self.span = span
        self.source_line = source_line
        formatted = format_caret_diagnostic("SynaxTypeError", message, span, source_line)
        super().__init__(formatted)

    def format_diagnostic(self) -> str:
        return format_caret_diagnostic("SynaxTypeError", self.message, self.span, self.source_line)

    def __str__(self) -> str:
        return self.format_diagnostic()


def extract_const_number(expr: Expr) -> Optional[float]:
    """
    If `expr` is a compile-time numeric literal (including unary `+`/`-` prefixes),
    return its `float` value; otherwise return `None`.
    """
    if isinstance(expr, NumberLit):
        return expr.value
    if isinstance(expr, UnaryExpr) and expr.op in ("+", "-"):
        inner = extract_const_number(expr.operand)
        if inner is not None:
            return -inner if expr.op == "-" else inner
    return None


def _is_flexible_numeric_literal(expr: Expr) -> Tuple[bool, bool]:
    """
    Return `(is_num_lit, is_int_lit)` indicating whether `expr` is an untyped
    numeric literal (`NumberLit` or signed `UnaryExpr` wrapping `NumberLit`).
    """
    if isinstance(expr, NumberLit):
        return True, expr.is_int
    if isinstance(expr, UnaryExpr) and expr.op in ("+", "-"):
        return _is_flexible_numeric_literal(expr.operand)
    return False, False


class TypeChecker:
    """Static Type & Constraint Checker for SYNAX `KernelDecl` ASTs."""

    def __init__(self, kernel: KernelDecl):
        self.kernel = kernel
        self.param_env: Dict[str, SynaxType] = {}
        self.let_env: Dict[str, SynaxType] = {}

    @classmethod
    def check(cls, kernel_decl: KernelDecl | SynaxModule) -> KernelDecl:
        """
        Validate parameter types, `require` shape invariants, `safety` block bounds,
        `let` scoping, builtin arity/bounds, and return type compatibility.
        Populates `inferred_type` on all `ParamDecl`, `LetStmt`, `ReturnStmt`, and `Expr` nodes.
        """
        if isinstance(kernel_decl, SynaxModule):
            if kernel_decl.kernel is None:
                raise SynaxTypeError("Declarative .sx module has no structured KernelDecl to type-check.")
            kernel_decl = kernel_decl.kernel
        checker = cls(kernel_decl)
        checker._run()
        return kernel_decl

    def _source_line(self, span: Optional[SourceSpan]) -> str:
        if span is not None and 1 <= span.line <= len(self.kernel.source_lines):
            return self.kernel.source_lines[span.line - 1]
        return ""

    def _fail(self, message: str, span: Optional[SourceSpan] = None) -> SynaxTypeError:
        sp = span or self.kernel.span
        raise SynaxTypeError(message, sp, self._source_line(sp))

    def resolve_type_annotation(self, ann: TypeAnnotation) -> SynaxType:
        if ann.elem_type is None and ann.dim is None:
            if ann.base not in SCALAR_TYPES:
                self._fail(
                    f"Unknown type '{ann.base}'; supported scalar types are {sorted(SCALAR_TYPES)} and 'tensor<T>'",
                    ann.span,
                )
            return SynaxType(base=ann.base)

        if ann.base != "tensor":
            self._fail(
                f"Type '{ann.base}' is not generic; only 'tensor<T>' or 'tensor<T, N>' accepts type parameters",
                ann.span,
            )

        if ann.elem_type not in SCALAR_TYPES:
            self._fail(
                f"Invalid tensor element type '{ann.elem_type}'; expected one of {sorted(SCALAR_TYPES)}",
                ann.span,
            )

        if ann.dim is not None and ann.dim <= 0:
            self._fail(
                f"Tensor static dimension N must be > 0, got {ann.dim}",
                ann.span,
            )

        return SynaxType(base="tensor", elem_type=ann.elem_type, dim=ann.dim)

    def _run(self) -> None:
        # 1. Validate parameters
        for param in self.kernel.params:
            if param.name in self.param_env:
                self._fail(f"Duplicate parameter name '{param.name}' in kernel '{self.kernel.name}'", param.span)
            p_type = self.resolve_type_annotation(param.type_annotation)
            param.inferred_type = p_type
            self.param_env[param.name] = p_type

        # 2. Validate return type annotation
        expected_ret_type = self.resolve_type_annotation(self.kernel.return_type)

        # 3. Validate `require shape(p0) == shape(p1)` declarations
        for req in self.kernel.requires:
            self._check_require(req)

        # 4. Validate `safety { ... }` block invariants
        if self.kernel.safety is not None:
            self._check_safety(self.kernel.safety)

        # 5. Validate `let` bindings and `return` statement in lexical source order
        stmts = self.kernel.statements if self.kernel.statements else [*self.kernel.lets, self.kernel.return_stmt]
        seen_return = False
        for stmt in stmts:
            if isinstance(stmt, LetStmt):
                self._check_let(stmt)
            elif isinstance(stmt, ReturnStmt):
                seen_return = True
                self._check_return(stmt, expected_ret_type)

        if not seen_return:
            self._check_return(self.kernel.return_stmt, expected_ret_type)

    def _check_require(self, req: RequireDecl) -> None:
        lhs_dim = self._check_shape_operand(req.lhs)
        rhs_dim = self._check_shape_operand(req.rhs)
        if lhs_dim is not None and rhs_dim is not None and lhs_dim != rhs_dim:
            self._fail(
                f"Static shape mismatch in 'require': shape dimension {lhs_dim} != {rhs_dim}",
                req.span,
            )

    def _check_shape_operand(self, shape_expr) -> Optional[int]:
        if shape_expr.param_name is not None:
            pname = shape_expr.param_name
            if pname not in self.param_env:
                self._fail(
                    f"'require shape({pname})' references undeclared parameter '{pname}'",
                    shape_expr.span,
                )
            ptype = self.param_env[pname]
            if not ptype.is_tensor:
                self._fail(
                    f"'require shape({pname})' requires a tensor parameter, but '{pname}' has scalar type '{ptype}'",
                    shape_expr.span,
                )
            return ptype.dim

        if shape_expr.dim_literal is not None:
            if shape_expr.dim_literal <= 0:
                self._fail(
                    f"Shape dimension literal in 'require' must be > 0, got {shape_expr.dim_literal}",
                    shape_expr.span,
                )
            return shape_expr.dim_literal
        return None

    def _check_safety(self, safety: SafetyDecl) -> None:
        if safety.nonfinite_mode == "heal_inputs":
            if not math.isfinite(safety.heal_value):
                self._fail(
                    f"Safety 'heal(...)' value must be finite, got {safety.heal_value}",
                    safety.nonfinite_span or safety.span,
                )

        if safety.output_clamp is not None:
            lo, hi = safety.output_clamp
            if not (math.isfinite(lo) and math.isfinite(hi)) or lo > hi:
                self._fail(
                    f"Invalid safety range_check clamp({lo}, {hi}): lower bound must be <= upper bound",
                    safety.range_check_span or safety.span,
                )

        if safety.input_abs_bound is not None:
            bound = safety.input_abs_bound
            if not math.isfinite(bound) or bound <= 0.0:
                self._fail(
                    f"Invalid safety input_bound abs_max({bound}): bound must be strictly > 0",
                    safety.input_bound_span or safety.span,
                )

    def _check_let(self, stmt: LetStmt) -> None:
        # Evaluate RHS BEFORE adding `stmt.name` to `let_env` so self-referential
        # `let x = x + 1` or forward references fail with use-before-definition.
        rhs_type = self._infer_expr(stmt.expr)

        if stmt.name in self.let_env:
            self._fail(f"Duplicate 'let' binding '{stmt.name}' in same kernel block", stmt.span)
        if stmt.name in self.param_env:
            self._fail(f"'let {stmt.name}' shadows kernel parameter '{stmt.name}'", stmt.span)

        if stmt.type_annotation is not None:
            declared_type = self.resolve_type_annotation(stmt.type_annotation)
            final_type = self._check_assignable(
                target_type=declared_type,
                value_type=rhs_type,
                value_expr=stmt.expr,
                context=f"let '{stmt.name}'",
                span=stmt.span,
            )
        else:
            final_type = rhs_type

        stmt.inferred_type = final_type
        self.let_env[stmt.name] = final_type

    def _check_return(self, stmt: ReturnStmt, expected_ret_type: SynaxType) -> None:
        ret_expr_type = self._infer_expr(stmt.expr)
        final_type = self._check_assignable(
            target_type=expected_ret_type,
            value_type=ret_expr_type,
            value_expr=stmt.expr,
            context=f"return statement of kernel '{self.kernel.name}'",
            span=stmt.span,
        )
        stmt.inferred_type = final_type

    def _check_assignable(
        self,
        *,
        target_type: SynaxType,
        value_type: SynaxType,
        value_expr: Expr,
        context: str,
        span: SourceSpan,
    ) -> SynaxType:
        if target_type == value_type:
            return target_type

        # Allow scalar numeric literal adaptation (e.g. `let c: f64 = 0.5`, `let n: i32 = 2`, `let x: f32 = 1`)
        is_lit, is_int_lit = _is_flexible_numeric_literal(value_expr)
        if is_lit and target_type.is_scalar and target_type.is_numeric:
            if target_type.base == "i32" and not is_int_lit:
                self._fail(
                    f"Type mismatch in {context}: expected '{target_type}', got floating-point literal '{value_type}'",
                    span,
                )
            value_expr.inferred_type = target_type
            return target_type

        self._fail(
            f"Type mismatch in {context}: expected '{target_type}', got '{value_type}'",
            span,
        )

    def _broadcast_numeric(
        self,
        left_type: SynaxType,
        right_type: SynaxType,
        left_expr: Expr,
        right_expr: Expr,
        span: SourceSpan,
        op_desc: str,
    ) -> SynaxType:
        if not left_type.is_numeric:
            self._fail(f"Operator '{op_desc}' requires numeric operands, got '{left_type}'", left_expr.span)
        if not right_type.is_numeric:
            self._fail(f"Operator '{op_desc}' requires numeric operands, got '{right_type}'", right_expr.span)

        l_lit, _ = _is_flexible_numeric_literal(left_expr)
        r_lit, _ = _is_flexible_numeric_literal(right_expr)

        # Harmonize scalar dtypes when one side is an untyped numeric literal (e.g., `a * 2` or `x_f64 + 1.0`)
        l_dtype = left_type.scalar_dtype
        r_dtype = right_type.scalar_dtype
        if l_dtype != r_dtype:
            if l_lit and left_type.is_scalar and r_dtype in FLOAT_SCALARS:
                l_dtype = r_dtype
                left_type = SynaxType(l_dtype)
                left_expr.inferred_type = left_type
            elif r_lit and right_type.is_scalar and l_dtype in FLOAT_SCALARS:
                r_dtype = l_dtype
                right_type = SynaxType(r_dtype)
                right_expr.inferred_type = right_type
            elif l_lit and r_lit and left_type.is_scalar and right_type.is_scalar:
                # e.g., `1 + 2.0` -> `f32`
                common = "f64" if "f64" in (l_dtype, r_dtype) else "f32"
                l_dtype = r_dtype = common
                left_type = right_type = SynaxType(common)
                left_expr.inferred_type = right_expr.inferred_type = left_type
            else:
                self._fail(
                    f"Element type mismatch in '{op_desc}': cannot combine '{left_type}' and '{right_type}'",
                    span,
                )

        # Shape combination
        if left_type.is_scalar and right_type.is_scalar:
            return SynaxType(l_dtype)
        if left_type.is_tensor and right_type.is_scalar:
            return left_type
        if left_type.is_scalar and right_type.is_tensor:
            return right_type

        # Both tensors
        if left_type.dim != right_type.dim:
            self._fail(
                f"Tensor shape mismatch in '{op_desc}': '{left_type}' vs '{right_type}'",
                span,
            )
        return left_type

    def _infer_expr(self, expr: Expr) -> SynaxType:
        if isinstance(expr, NumberLit):
            # Default standalone integer literal to `i32` if pure int?
            # Note: in SYNAX arithmetic kernels, `f32` is standard for float literals and
            # integer literals (`0`, `1`, `2`) adapt to float via `_broadcast_numeric` / `_check_assignable`.
            ty = I32_TYPE if expr.is_int else F32_TYPE
            expr.inferred_type = ty
            return ty

        if isinstance(expr, BoolLit):
            expr.inferred_type = BOOL_TYPE
            return BOOL_TYPE

        if isinstance(expr, VarRef):
            if expr.name in self.let_env:
                ty = self.let_env[expr.name]
            elif expr.name in self.param_env:
                ty = self.param_env[expr.name]
            elif expr.name == "bias":
                ty = F32_TYPE
            else:
                self._fail(f"Undefined identifier '{expr.name}' (not declared or used before definition)", expr.span)
            expr.inferred_type = ty
            return ty

        if isinstance(expr, UnaryExpr):
            op_type = self._infer_expr(expr.operand)
            if not op_type.is_numeric:
                self._fail(f"Unary '{expr.op}' requires a numeric operand, got '{op_type}'", expr.span)
            expr.inferred_type = op_type
            return op_type

        if isinstance(expr, BinaryExpr):
            lt = self._infer_expr(expr.left)
            rt = self._infer_expr(expr.right)
            res = self._broadcast_numeric(lt, rt, expr.left, expr.right, expr.span, expr.op)
            expr.inferred_type = res
            return res

        if isinstance(expr, PowerExpr):
            bt = self._infer_expr(expr.base)
            self._infer_expr(expr.exponent)
            if not bt.is_numeric:
                self._fail(f"Exponentiation base must be numeric, got '{bt}'", expr.base.span)
            exp_const = extract_const_number(expr.exponent)
            if exp_const is None or exp_const not in (2.0, 3.0):
                self._fail(
                    "Exponentiation in SYNAX requires constant exponent 2 or 3 (e.g. x^2 or x^3)",
                    expr.exponent.span,
                )
            expr.inferred_type = bt
            return bt

        if isinstance(expr, CallExpr):
            return self._infer_call(expr)

        self._fail(f"Unsupported expression node '{type(expr).__name__}'", expr.span)

    def _infer_call(self, expr: CallExpr) -> SynaxType:
        fn = expr.func_name

        # 1. Unary builtins
        if fn in ALL_UNARY_BUILTINS:
            if len(expr.args) != 1:
                self._fail(
                    f"Builtin '{fn}()' expects 1 argument, got {len(expr.args)}",
                    expr.span,
                )
            arg_expr = expr.args[0]
            arg_type = self._infer_expr(arg_expr)
            if not arg_type.is_numeric:
                self._fail(f"Builtin '{fn}()' requires a numeric argument, got '{arg_type}'", arg_expr.span)

            if fn in UNARY_FLOAT_BUILTINS and not arg_type.is_float:
                is_lit, _ = _is_flexible_numeric_literal(arg_expr)
                if is_lit and arg_type.is_scalar:
                    arg_type = F32_TYPE
                    arg_expr.inferred_type = F32_TYPE
                else:
                    self._fail(
                        f"Transcendental builtin '{fn}()' requires floating-point operand ('f32'/'f64'), got '{arg_type}'",
                        arg_expr.span,
                    )
            expr.inferred_type = arg_type
            return arg_type

        # 2. Binary builtins (`min`, `max`)
        if fn in BINARY_BUILTINS:
            if len(expr.args) != 2:
                self._fail(
                    f"Builtin '{fn}()' expects 2 arguments, got {len(expr.args)}",
                    expr.span,
                )
            t0 = self._infer_expr(expr.args[0])
            t1 = self._infer_expr(expr.args[1])
            res = self._broadcast_numeric(t0, t1, expr.args[0], expr.args[1], expr.span, fn)
            expr.inferred_type = res
            return res

        # 3. Ternary builtin (`clamp(x, lo, hi)`)
        if fn in TERNARY_BUILTINS:
            if len(expr.args) != 3:
                self._fail(
                    f"Builtin 'clamp(x, lo, hi)' expects 3 arguments, got {len(expr.args)}",
                    expr.span,
                )
            x_expr, lo_expr, hi_expr = expr.args
            tx = self._infer_expr(x_expr)
            tlo = self._infer_expr(lo_expr)
            thi = self._infer_expr(hi_expr)

            # Static constant bound check: if `lo` and `hi` are constant literals and `lo > hi`, fail!
            lo_const = extract_const_number(lo_expr)
            hi_const = extract_const_number(hi_expr)
            if lo_const is not None and hi_const is not None and lo_const > hi_const:
                self._fail(
                    f"Invalid clamp(x, {lo_const}, {hi_const}): constant lower bound ({lo_const}) > upper bound ({hi_const})",
                    expr.span,
                )

            t_x_lo = self._broadcast_numeric(tx, tlo, x_expr, lo_expr, expr.span, "clamp")
            res = self._broadcast_numeric(t_x_lo, thi, x_expr, hi_expr, expr.span, "clamp")
            expr.inferred_type = res
            return res

        # 4. Dendritic unary reductions (`sum`, `mean`, `l2_norm`, `norm`)
        if fn in DENDRITIC_UNARY_REDUCTIONS:
            if len(expr.args) != 1:
                self._fail(
                    f"Dendritic reduction '{fn}()' expects 1 argument, got {len(expr.args)}",
                    expr.span,
                )
            arg_expr = expr.args[0]
            arg_type = self._infer_expr(arg_expr)
            if not arg_type.is_numeric:
                self._fail(
                    f"Dendritic reduction '{fn}()' requires a numeric tensor or scalar, got '{arg_type}'",
                    arg_expr.span,
                )
            ret_type = SynaxType(arg_type.scalar_dtype)
            expr.inferred_type = ret_type
            return ret_type

        # 5. Dendritic binary reductions (`dot(a, b)`)
        if fn in DENDRITIC_BINARY_REDUCTIONS:
            if len(expr.args) != 2:
                self._fail(
                    f"Dendritic reduction '{fn}()' expects 2 arguments, got {len(expr.args)}",
                    expr.span,
                )
            t0 = self._infer_expr(expr.args[0])
            t1 = self._infer_expr(expr.args[1])
            if not t0.is_numeric:
                self._fail(f"Dendritic dot requires numeric operands, got '{t0}'", expr.args[0].span)
            if not t1.is_numeric:
                self._fail(f"Dendritic dot requires numeric operands, got '{t1}'", expr.args[1].span)
            if t0.is_tensor and t1.is_tensor and t0.dim is not None and t1.dim is not None and t0.dim != t1.dim:
                self._fail(f"Dendritic dot shape mismatch: '{t0}' vs '{t1}'", expr.span)
            ret_type = SynaxType(t0.scalar_dtype)
            expr.inferred_type = ret_type
            return ret_type

        # 6. Dendritic window filtering (`window_mean(x, window_size)`)
        if fn in DENDRITIC_WINDOW_BUILTINS:
            if len(expr.args) != 2:
                self._fail(
                    f"Dendritic filtering '{fn}()' expects 2 arguments (tensor, window_size), got {len(expr.args)}",
                    expr.span,
                )
            t0 = self._infer_expr(expr.args[0])
            t1 = self._infer_expr(expr.args[1])
            if not (t0.is_tensor and t0.is_numeric):
                self._fail(f"First argument to '{fn}()' must be a numeric tensor, got '{t0}'", expr.args[0].span)
            if not t1.is_numeric:
                self._fail(f"Second argument (window size) to '{fn}()' must be numeric, got '{t1}'", expr.args[1].span)
            w_const = extract_const_number(expr.args[1])
            if w_const is not None and w_const <= 0:
                self._fail(f"Window size in '{fn}()' must be > 0, got {w_const}", expr.args[1].span)
            expr.inferred_type = t0
            return t0

        self._fail(f"Unknown builtin function '{fn}()'", expr.span)
