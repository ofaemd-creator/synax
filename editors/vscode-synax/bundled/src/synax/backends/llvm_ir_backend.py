#!/usr/bin/env python3
"""
SYNAX LLVM SSA IR BACKEND (src/synax/backends/llvm_ir_backend.py)
=============================================================================
Lowers canonical `SynaxIR` (`ASTNode` + `SafetyPolicy`) directly to valid,
modern opaque-pointer SSA LLVM IR (`.ll`) without passing through C!

Features:
  - Exact IEEE-754 binary32 hex-literal emission (`0x...`)
  - Bitwise `bitcast float %v to i32` + `icmp ule i32` Immune Shield lowering
  - IEEE-754 NaN-propagating `min`, `max`, `clamp`, `relu` via `fcmp uno`
  - Direct native `.dylib` / `.so` compilation via `clang -O3 -mcpu=native -x ir`
    verified 1:1 against the C11 Scalar Reference across all 19 edge suites.
=============================================================================
"""

import math
import os
import struct
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_ir import ASTNode, SynaxIR, _f32


def _llvm_f32_hex(val: float) -> str:
    """
    Encode a single-precision float32 as LLVM IR's exact 64-bit IEEE-754 hex literal.
     LLVM IR requires float constants in hex to be represented as the bit-pattern
    of the value widened to IEEE-754 binary64.
    """
    if math.isnan(val):
        return "0x7FF8000000000000"  # Quiet NaN
    if math.isinf(val):
        return "0x7FF0000000000000" if val > 0 else "0xFFF0000000000000"
    f32_val = _f32(val)
    q_bits = struct.unpack("<Q", struct.pack("<d", float(f32_val)))[0]
    return f"0x{q_bits:016X}"


class _SSABuilder:
    def __init__(self):
        self.counter = 0
        self.lines: List[str] = []

    def reg(self) -> str:
        self.counter += 1
        return f"%r{self.counter}"

    def emit(self, inst: str):
        self.lines.append(f"  {inst}")

    def emit_label(self, name: str):
        self.lines.append(f"{name}:")

    def emit_min_f32(self, x: str, y: str) -> str:
        # Match synax_minf: NaN if either NaN; signed-zero (-0.0 < +0.0) handled via bitcast on 0==0
        unord = self.reg()
        self.emit(f"{unord} = fcmp uno float {x}, {y}")
        eq_zero_x = self.reg()
        eq_zero_y = self.reg()
        both_zero = self.reg()
        self.emit(f"{eq_zero_x} = fcmp oeq float {x}, 0.000000e+00")
        self.emit(f"{eq_zero_y} = fcmp oeq float {y}, 0.000000e+00")
        self.emit(f"{both_zero} = and i1 {eq_zero_x}, {eq_zero_y}")
        bx = self.reg()
        by = self.reg()
        bor = self.reg()
        zres = self.reg()
        self.emit(f"{bx} = bitcast float {x} to i32")
        self.emit(f"{by} = bitcast float {y} to i32")
        self.emit(f"{bor} = or i32 {bx}, {by}")
        self.emit(f"{zres} = bitcast i32 {bor} to float")
        lt = self.reg()
        sel_lt = self.reg()
        sel_z = self.reg()
        out = self.reg()
        self.emit(f"{lt} = fcmp olt float {x}, {y}")
        self.emit(f"{sel_lt} = select i1 {lt}, float {x}, float {y}")
        self.emit(f"{sel_z} = select i1 {both_zero}, float {zres}, float {sel_lt}")
        self.emit(f"{out} = select i1 {unord}, float {_llvm_f32_hex(float('nan'))}, float {sel_z}")
        return out

    def emit_max_f32(self, x: str, y: str) -> str:
        unord = self.reg()
        self.emit(f"{unord} = fcmp uno float {x}, {y}")
        eq_zero_x = self.reg()
        eq_zero_y = self.reg()
        both_zero = self.reg()
        self.emit(f"{eq_zero_x} = fcmp oeq float {x}, 0.000000e+00")
        self.emit(f"{eq_zero_y} = fcmp oeq float {y}, 0.000000e+00")
        self.emit(f"{both_zero} = and i1 {eq_zero_x}, {eq_zero_y}")
        bx = self.reg()
        by = self.reg()
        band = self.reg()
        zres = self.reg()
        self.emit(f"{bx} = bitcast float {x} to i32")
        self.emit(f"{by} = bitcast float {y} to i32")
        self.emit(f"{band} = and i32 {bx}, {by}")
        self.emit(f"{zres} = bitcast i32 {band} to float")
        gt = self.reg()
        sel_gt = self.reg()
        sel_z = self.reg()
        out = self.reg()
        self.emit(f"{gt} = fcmp ogt float {x}, {y}")
        self.emit(f"{sel_gt} = select i1 {gt}, float {x}, float {y}")
        self.emit(f"{sel_z} = select i1 {both_zero}, float {zres}, float {sel_gt}")
        self.emit(f"{out} = select i1 {unord}, float {_llvm_f32_hex(float('nan'))}, float {sel_z}")
        return out

    def lower_expr(self, node: ASTNode, va: str, vb: str, vbias: str) -> str:
        if node.op == "VAR":
            return va if node.value == "a" else vb
        if node.op == "CONST":
            return _llvm_f32_hex(float(node.value))
        if node.op == "BIAS":
            return vbias

        c = [self.lower_expr(ch, va, vb, vbias) for ch in node.children]
        r = self.reg()
        op = node.op
        if op == "NEG":
            self.emit(f"{r} = fneg float {c[0]}")
            return r
        if op == "ADD":
            self.emit(f"{r} = fadd float {c[0]}, {c[1]}")
            return r
        if op == "SUB":
            self.emit(f"{r} = fsub float {c[0]}, {c[1]}")
            return r
        if op == "MUL":
            self.emit(f"{r} = fmul float {c[0]}, {c[1]}")
            return r
        if op == "DIV":
            self.emit(f"{r} = fdiv float {c[0]}, {c[1]}")
            return r
        if op == "POW2":
            self.emit(f"{r} = fmul float {c[0]}, {c[0]}")
            return r
        if op == "POW3":
            sq = self.reg()
            self.emit(f"{sq} = fmul float {c[0]}, {c[0]}")
            self.emit(f"{r} = fmul float {sq}, {c[0]}")
            return r
        if op == "SQRT":
            self.emit(f"{r} = call float @llvm.sqrt.f32(float {c[0]})")
            return r
        if op == "ABS":
            self.emit(f"{r} = call float @llvm.fabs.f32(float {c[0]})")
            return r
        if op == "SIN":
            self.emit(f"{r} = call float @llvm.sin.f32(float {c[0]})")
            return r
        if op == "COS":
            self.emit(f"{r} = call float @llvm.cos.f32(float {c[0]})")
            return r
        if op == "EXP":
            self.emit(f"{r} = call float @llvm.exp.f32(float {c[0]})")
            return r
        if op == "LOG":
            self.emit(f"{r} = call float @llvm.log.f32(float {c[0]})")
            return r
        if op == "TANH":
            self.emit(f"{r} = call float @tanhf(float {c[0]})")
            return r
        if op == "SIGMOID":
            nx = self.reg()
            ex = self.reg()
            dn = self.reg()
            one = _llvm_f32_hex(1.0)
            self.emit(f"{nx} = fneg float {c[0]}")
            self.emit(f"{ex} = call float @llvm.exp.f32(float {nx})")
            self.emit(f"{dn} = fadd float {one}, {ex}")
            self.emit(f"{r} = fdiv float {one}, {dn}")
            return r
        if op == "RELU":
            un = self.reg()
            gt = self.reg()
            pos = self.reg()
            self.emit(f"{un} = fcmp uno float {c[0]}, 0.000000e+00")
            self.emit(f"{gt} = fcmp ogt float {c[0]}, 0.000000e+00")
            self.emit(f"{pos} = select i1 {gt}, float {c[0]}, float 0.000000e+00")
            self.emit(f"{r} = select i1 {un}, float {_llvm_f32_hex(float('nan'))}, float {pos}")
            return r
        if op == "MIN":
            return self.emit_min_f32(c[0], c[1])
        if op == "MAX":
            return self.emit_max_f32(c[0], c[1])
        if op == "CLAMP":
            lo_clamped = self.emit_max_f32(c[0], c[1])
            return self.emit_min_f32(lo_clamped, c[2])
        if op == "SELECT":
            gt = self.reg()
            self.emit(f"{gt} = fcmp ogt float {c[0]}, 0.000000e+00")
            self.emit(f"{r} = select i1 {gt}, float {c[1]}, float {c[2]}")
            return r
        if op == "FMA":
            prod = self.reg()
            self.emit(f"{prod} = fmul float {c[0]}, {c[1]}")
            self.emit(f"{r} = fadd float {prod}, {c[2]}")
            return r
        raise ValueError(f"Unsupported AST op in LLVM IR backend: {op}")


class LLVMIRBackend:
    """Generates standalone SSA LLVM IR (`.ll`) and compiles via Clang's LLVM backend."""

    @classmethod
    def emit_llvm_ir(cls, ir: SynaxIR) -> str:
        b = _SSABuilder()
        bound_u32 = (
            0x7F7FFFFF
            if ir.safety.input_abs_bound is None
            else struct.unpack("<I", struct.pack("<f", _f32(abs(ir.safety.input_abs_bound))))[0]
        )
        heal_hex = _llvm_f32_hex(ir.safety.heal_value)
        bias_hex = _llvm_f32_hex(ir.bias_default)
        nan_hex = _llvm_f32_hex(float("nan"))
        mode = ir.safety.nonfinite_mode

        b.emit_label("entry")
        b.emit("%b_nonnull = icmp ne ptr %b, null")
        b.emit("%zero_len = icmp eq i64 %n, 0")
        b.emit("br i1 %zero_len, label %exit_empty, label %loop.header")

        b.emit_label("exit_empty")
        b.emit("%h_nonnull0 = icmp ne ptr %out_healed, null")
        b.emit("br i1 %h_nonnull0, label %store_h0, label %ret0")
        b.emit_label("store_h0")
        b.emit("store i64 0, ptr %out_healed, align 8")
        b.emit("br label %ret0")
        b.emit_label("ret0")
        b.emit("ret void")

        b.emit_label("loop.header")
        b.emit("%i = phi i64 [ 0, %entry ], [ %i.next, %loop.latch ]")
        b.emit("%healed = phi i64 [ 0, %entry ], [ %healed.next, %loop.latch ]")
        b.emit("%pa = getelementptr inbounds float, ptr %a, i64 %i")
        b.emit("%ai_raw = load float, ptr %pa, align 4")
        b.emit("br i1 %b_nonnull, label %load_b, label %no_b")

        b.emit_label("load_b")
        b.emit("%pb = getelementptr inbounds float, ptr %b, i64 %i")
        b.emit("%bi_loaded = load float, ptr %pb, align 4")
        b.emit("br label %body")

        b.emit_label("no_b")
        b.emit("br label %body")

        b.emit_label("body")
        b.emit("%bi_raw = phi float [ %bi_loaded, %load_b ], [ 0.000000e+00, %no_b ]")

        # Bitwise IEEE-754 validation on ai_raw and bi_raw
        b.emit("%bits_a = bitcast float %ai_raw to i32")
        b.emit("%abs_a = and i32 %bits_a, 2147483647")
        b.emit(f"%ok_a = icmp ule i32 %abs_a, {bound_u32}")
        b.emit("%bits_b = bitcast float %bi_raw to i32")
        b.emit("%abs_b = and i32 %bits_b, 2147483647")
        b.emit(f"%ok_b_val = icmp ule i32 %abs_b, {bound_u32}")
        b.emit("%ok_b = select i1 %b_nonnull, i1 %ok_b_val, i1 true")

        if mode == "preserve":
            va_use = "%ai_raw"
            vb_use = "%bi_raw"
            b.emit("%healed.step = add i64 %healed, 0")
        else:
            b.emit("%bad_a_i64 = select i1 %ok_a, i64 0, i64 1")
            b.emit("%bad_b_i64 = select i1 %ok_b, i64 0, i64 1")
            b.emit("%h_tmp = add i64 %healed, %bad_a_i64")
            b.emit("%healed.step = add i64 %h_tmp, %bad_b_i64")
            if mode == "heal_inputs":
                b.emit(f"%ai_san = select i1 %ok_a, float %ai_raw, float {heal_hex}")
                b.emit(f"%bi_san = select i1 %ok_b, float %bi_raw, float {heal_hex}")
            else:
                b.emit("%ai_san = select i1 %ok_a, float %ai_raw, float 0.000000e+00")
                b.emit("%bi_san = select i1 %ok_b, float %bi_raw, float 0.000000e+00")
            va_use = "%ai_san"
            vb_use = "%bi_san"

        res_reg = b.lower_expr(ir.expr, va_use, vb_use, bias_hex)

        if mode == "zero_output":
            both_ok = b.reg()
            sel_zero = b.reg()
            b.emit(f"{both_ok} = and i1 %ok_a, %ok_b")
            b.emit(f"{sel_zero} = select i1 {both_ok}, float {res_reg}, float {heal_hex}")
            res_reg = sel_zero

        if ir.safety.output_clamp is not None:
            lo_h = _llvm_f32_hex(ir.safety.output_clamp[0])
            hi_h = _llvm_f32_hex(ir.safety.output_clamp[1])
            lo_c = b.emit_max_f32(res_reg, lo_h)
            res_reg = b.emit_min_f32(lo_c, hi_h)

        if mode == "reject":
            both_ok = b.reg()
            sel_rej = b.reg()
            b.emit(f"{both_ok} = and i1 %ok_a, %ok_b")
            b.emit(f"{sel_rej} = select i1 {both_ok}, float {res_reg}, float {nan_hex}")
            res_reg = sel_rej

        b.emit("br label %loop.latch")
        b.emit_label("loop.latch")
        b.emit("%pout = getelementptr inbounds float, ptr %out, i64 %i")
        b.emit(f"store float {res_reg}, ptr %pout, align 4")
        b.emit("%healed.next = add i64 %healed.step, 0")
        b.emit("%i.next = add nuw i64 %i, 1")
        b.emit("%cond = icmp ult i64 %i.next, %n")
        b.emit("br i1 %cond, label %loop.header, label %exit")

        b.emit_label("exit")
        b.emit("%h_nonnull = icmp ne ptr %out_healed, null")
        b.emit("br i1 %h_nonnull, label %store_h, label %ret_done")
        b.emit_label("store_h")
        b.emit("store i64 %healed.next, ptr %out_healed, align 8")
        b.emit("br label %ret_done")
        b.emit_label("ret_done")
        b.emit("ret void")

        # Note on macOS Mach-O vs Linux ELF symbol mangling in textual LLVM IR:
        # When compiling `.ll` without a target triple header via `clang -x ir`, Clang
        # automatically injects the host target datalayout & Mach-O `_` prefix ONLY if
        # symbols use standard LLVM identifiers (`@synax_kernel` -> Mach-O `_synax_kernel`!).
        fn_body = "\n".join(b.lines)

        return f"""; SYNAX SSA LLVM IR Module — {ir.name} [IR #{ir.ir_hash}]
declare float @llvm.sqrt.f32(float)
declare float @llvm.fabs.f32(float)
declare float @llvm.sin.f32(float)
declare float @llvm.cos.f32(float)
declare float @llvm.exp.f32(float)
declare float @llvm.log.f32(float)
declare float @tanhf(float)

define void @synax_kernel_tracked(ptr noalias readonly %a, ptr noalias readonly %b, ptr noalias writeonly %out, i64 %n, ptr noalias %out_healed) {{
{fn_body}
}}

define void @synax_kernel(ptr noalias readonly %a, ptr noalias readonly %b, ptr noalias writeonly %out, i64 %n) {{
entry:
  call void @synax_kernel_tracked(ptr %a, ptr %b, ptr %out, i64 %n, ptr null)
  ret void
}}
"""

    @classmethod
    def compile_ll_to_dylib(cls, ir: SynaxIR, ll_path: Path, dylib_path: Path) -> Tuple[bool, str]:
        import platform

        cpu_flag = "-mcpu=native" if platform.machine().lower() in ("arm64", "aarch64") else "-march=native"
        ll_text = cls.emit_llvm_ir(ir)
        ll_path.write_text(ll_text, encoding="utf-8")
        res = subprocess.run(
            ["clang", "-O3", cpu_flag, "-shared", "-fPIC", "-Wno-override-module", "-x", "ir", str(ll_path), "-lm", "-o", str(dylib_path)],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            err = res.stderr.strip().splitlines()[0] if res.stderr.strip() else "LLVM IR derleme hatası"
            return False, err
        return True, ""
