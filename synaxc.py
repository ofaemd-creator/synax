#!/usr/bin/env python3
"""
SYNAXC (v0.5) — Unified Neuro-Symbolic & Myelin Compiler Pipeline
=============================================================================
Unifies the SYNAX v0.4 Differential Verification & Dual-Reference Core with
the Antigravity ARM64 NEON / Ranvier Saltatory Myelin Engine:

  SYNAPSE -> IMMUNE -> AXON -> TYCON -> MYELIN

Pipeline Stages:
  1. SYNAPSE (`synax_ir.py`):
     Parses structured (`synax 0.1 kernel ...`) and declarative (`niyet:/kural:`)
     `.sx` programs into canonical `SynaxIR` + Zero-Trust `SynaxSecurityGuard`.
  2. IMMUNE Dual-Reference Gate (`synax_verifier.py`):
     Verifies Python IEEE-754 binary32 AST Reference against C11 `-O0` Scalar
     Reference (or two independent LLM C11 references when `--llm` is used).
  3. AXON & TYCON Multi-Variant Synthesis:
     Generates candidate C11/SIMD/Multicore implementations without `-ffast-math`:
       - `v0_clang_o3_scalar`   : Branchless C11 scalar (`clang -O3 -mcpu=native`)
       - `v1_unroll4_scalar`    : 4x superscalar unrolled C11 loop
       - `v2_neon_simd`         : Explicit ARM64 NEON (`float32x4_t`) + bitwise shield
       - `v3_neon_4acc_prefetch`: 4x unrolled ARM64 NEON (16 floats/iter) + prefetch
       - `v4_gcd_multicore_neon`: Apple GCD `dispatch_apply_f` + NEON chunks
     (Plus optional LLM evolutionary mutations when `--llm claude|gemini` is enabled.)
  4. 19-Suite Differential Elimination:
     Every candidate is tested on all 19 adversarial suites (`n=0..100,003`,
     `NaN`, `±Inf`, `±0.0`, `1e-40`, `±3.4e38`, Cartesian pairs, `1234.5f` sentinel,
     and exact anomaly-heal counts). Any semantic deviation is rejected.
  5. Warm-Cache Median Benchmark & MYELIN Cache (`~/.cache/synax/hafiza/<hash>/`):
     Measures true warm-cache median latency, persists signed `rapor.json` +
     `referans.dylib` + `kazanan.dylib`, and binds directly to `SynaxAxonChannel`.
=============================================================================
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from synax_ir import ASTNode, SafetyPolicy, SynaxIR, _f32, _format_c_float, parse_sx
from synax_security import SynaxSecurityGuard
from synax_verifier import (
    DualReferenceMismatchError,
    LoadedKernel,
    VerificationReport,
    benchmark_kernel,
    build_adversarial_suites,
    verify_against_reference,
    verify_dual_reference_offline,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, "build")

SHARED_CFLAGS_O3 = ["-O3", "-mcpu=native", "-shared", "-fPIC", "-std=c11", "-Wall", "-Wno-unused-function"]
SHARED_CFLAGS_O1_SCALAR = [
    "-O1", "-fno-vectorize", "-fno-slp-vectorize",
    "-shared", "-fPIC", "-std=c11", "-Wall", "-Wno-unused-function",
]
SHARED_CFLAGS_O0_REF = ["-O0", "-shared", "-fPIC", "-std=c11", "-Wall", "-Wno-unused-function"]


def get_hafiza_root() -> Path:
    """Return secure user-owned Myelin cache root (`~/.cache/synax/hafiza`, mode 0700)."""
    env_dir = os.environ.get("SYNAX_CACHE_DIR")
    candidates = [Path(env_dir)] if env_dir else [
        Path.home() / ".cache" / "synax" / "hafiza",
        Path(BASE_DIR) / ".synax_cache" / "hafiza",
    ]
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            test_file = root / ".write_probe"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            try:
                os.chmod(root.parent, 0o700)
                os.chmod(root, 0o700)
            except OSError:
                pass
            return root
        except OSError:
            continue
    raise RuntimeError("Yazılabilir güvenli bir SYNAX önbellek dizini oluşturulamadı.")


# ─────────────────────────────────────────────────────────────────
# 1. DETERMINISTIC IEEE-754 C11 + ARM64 NEON + GCD CODE GENERATOR
# ─────────────────────────────────────────────────────────────────
C_MATH_PREAMBLE = """#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#if defined(__aarch64__) || defined(_M_ARM64)
#include <arm_neon.h>
#endif
#if defined(__APPLE__)
#include <dispatch/dispatch.h>
#include <unistd.h>
#endif

static inline bool synax_is_valid_f32(float v, uint32_t bound_u32) {
    uint32_t bits;
    memcpy(&bits, &v, sizeof(uint32_t));
    return (bits & 0x7FFFFFFFu) <= bound_u32;
}

static inline float synax_sqf(float x) {
    return x * x;
}

static inline float synax_cbef(float x) {
    return (x * x) * x;
}

static inline float synax_reluf(float x) {
    return isnan(x) ? NAN : (x > 0.0f ? x : 0.0f);
}

static inline float synax_minf(float x, float y) {
    if (isnan(x) || isnan(y)) return NAN;
    if (x == 0.0f && y == 0.0f) return (signbit(x) || signbit(y)) ? -0.0f : 0.0f;
    return x < y ? x : y;
}

static inline float synax_maxf(float x, float y) {
    if (isnan(x) || isnan(y)) return NAN;
    if (x == 0.0f && y == 0.0f) return (!signbit(x) || !signbit(y)) ? 0.0f : -0.0f;
    return x > y ? x : y;
}

static inline float synax_clampf(float x, float lo, float hi) {
    return synax_minf(synax_maxf(x, lo), hi);
}

#if defined(__aarch64__) || defined(_M_ARM64)
static inline float32x4_t synax_vsqq_f32(float32x4_t x) {
    return vmulq_f32(x, x);
}

static inline float32x4_t synax_vcbeq_f32(float32x4_t x) {
    return vmulq_f32(vmulq_f32(x, x), x);
}

/* IEEE-754 faithful ARM64 NEON expf (Cody-Waite range reduction + 2-step subnormal-safe scaling) */
static inline float32x4_t synax_vexpq_f32(float32x4_t x) {
    const float32x4_t inv_ln2 = vdupq_n_f32(1.4426950408889634f);
    const float32x4_t ln2_hi  = vdupq_n_f32(0.693145751953125f);
    const float32x4_t ln2_lo  = vdupq_n_f32(1.428606765330187e-06f);

    float32x4_t xc = vminq_f32(vmaxq_f32(x, vdupq_n_f32(-104.0f)), vdupq_n_f32(89.0f));
    float32x4_t fn = vrndnq_f32(vmulq_f32(xc, inv_ln2));
    float32x4_t r  = vfmsq_f32(xc, fn, ln2_hi);
    r = vfmsq_f32(r, fn, ln2_lo);

    float32x4_t p = vdupq_n_f32(1.3888889e-03f);
    p = vfmaq_f32(vdupq_n_f32(8.3333338e-03f), p, r);
    p = vfmaq_f32(vdupq_n_f32(4.1666668e-02f), p, r);
    p = vfmaq_f32(vdupq_n_f32(1.6666667e-01f), p, r);
    p = vfmaq_f32(vdupq_n_f32(5.0000000e-01f), p, r);
    p = vfmaq_f32(vdupq_n_f32(1.0000000e+00f), p, r);
    p = vfmaq_f32(vdupq_n_f32(1.0000000e+00f), p, r);

    int32x4_t ni = vcvtq_s32_f32(fn);
    int32x4_t n1 = vshrq_n_s32(ni, 1);
    int32x4_t n2 = vsubq_s32(ni, n1);
    float32x4_t s1 = vreinterpretq_f32_s32(vshlq_n_s32(vaddq_s32(n1, vdupq_n_s32(127)), 23));
    float32x4_t s2 = vreinterpretq_f32_s32(vshlq_n_s32(vaddq_s32(n2, vdupq_n_s32(127)), 23));
    float32x4_t res = vmulq_f32(vmulq_f32(p, s1), s2);

    uint32x4_t over_m  = vcgtq_f32(x, vdupq_n_f32(88.722839f));
    uint32x4_t under_m = vcltq_f32(x, vdupq_n_f32(-103.97208f));
    uint32x4_t nan_m   = vmvnq_u32(vceqq_f32(x, x));

    res = vbslq_f32(over_m, vdupq_n_f32(INFINITY), res);
    res = vbslq_f32(under_m, vdupq_n_f32(0.0f), res);
    res = vbslq_f32(nan_m, x, res);
    return res;
}

static inline float32x4_t synax_vsigmoidq_f32(float32x4_t x) {
    float32x4_t ex = synax_vexpq_f32(vnegq_f32(x));
    return vdivq_f32(vdupq_n_f32(1.0f), vaddq_f32(vdupq_n_f32(1.0f), ex));
}
#endif
"""


class SynaxCodeGenerator:
    """Deterministic lowering from `SynaxIR` to C11 Scalar, ARM64 NEON, and Apple GCD variants."""

    @staticmethod
    def _bound_u32_hex(safety: SafetyPolicy) -> str:
        if safety.input_abs_bound is None:
            return "0x7F7FFFFFu"  # FLT_MAX bits: finite iff (bits & 0x7FFFFFFF) <= 0x7F7FFFFF
        b = _f32(abs(safety.input_abs_bound))
        bits = struct.unpack("<I", struct.pack("<f", b))[0]
        return f"0x{bits:08X}u"

    @classmethod
    def _scalar_loop_body(cls, ir: SynaxIR, idx_var: str = "i") -> str:
        c_expr = ir.expr.to_c_scalar(var_a="ai", var_b="bi", var_bias="bias")
        heal_lit = _format_c_float(ir.safety.heal_value)
        mode = ir.safety.nonfinite_mode

        lines = [
            f"        float ai = a[{idx_var}];",
            f"        float bi = b ? b[{idx_var}] : 0.0f;",
        ]

        if mode == "preserve":
            lines.append(f"        float res = {c_expr};")
            if ir.safety.output_clamp is not None:
                lo_s = _format_c_float(ir.safety.output_clamp[0])
                hi_s = _format_c_float(ir.safety.output_clamp[1])
                lines.append(f"        res = synax_clampf(res, {lo_s}, {hi_s});")
        elif mode == "heal_inputs":
            lines.extend([
                "        if (!synax_is_valid_f32(ai, bound_u32)) { ai = " + heal_lit + "; healed++; }",
                "        if (b && !synax_is_valid_f32(bi, bound_u32)) { bi = " + heal_lit + "; healed++; }",
                f"        float res = {c_expr};",
            ])
            if ir.safety.output_clamp is not None:
                lo_s = _format_c_float(ir.safety.output_clamp[0])
                hi_s = _format_c_float(ir.safety.output_clamp[1])
                lines.append(f"        res = synax_clampf(res, {lo_s}, {hi_s});")
        elif mode == "zero_output":
            lines.extend([
                "        bool ok_a = synax_is_valid_f32(ai, bound_u32);",
                "        bool ok_b = b ? synax_is_valid_f32(bi, bound_u32) : true;",
                "        if (!ok_a) healed++;",
                "        if (!ok_b) healed++;",
                f"        float res = (ok_a && ok_b) ? ({c_expr}) : {heal_lit};",
            ])
            if ir.safety.output_clamp is not None:
                lo_s = _format_c_float(ir.safety.output_clamp[0])
                hi_s = _format_c_float(ir.safety.output_clamp[1])
                lines.append(f"        res = synax_clampf(res, {lo_s}, {hi_s});")
        elif mode == "reject":
            lines.extend([
                "        bool ok_a = synax_is_valid_f32(ai, bound_u32);",
                "        bool ok_b = b ? synax_is_valid_f32(bi, bound_u32) : true;",
                "        if (!ok_a) healed++;",
                "        if (!ok_b) healed++;",
                f"        float res = (ok_a && ok_b) ? ({c_expr}) : NAN;",
            ])
            if ir.safety.output_clamp is not None:
                lo_s = _format_c_float(ir.safety.output_clamp[0])
                hi_s = _format_c_float(ir.safety.output_clamp[1])
                lines.append(f"        if (ok_a && ok_b) res = synax_clampf(res, {lo_s}, {hi_s});")
        else:
            raise ValueError(f"Unsupported safety mode: {mode}")

        lines.append(f"        out[{idx_var}] = res;")
        return "\n".join(lines)

    @classmethod
    def emit_scalar_variant(cls, ir: SynaxIR, pragma_line: str = "") -> str:
        bias_lit = _format_c_float(ir.bias_default)
        bound_hex = cls._bound_u32_hex(ir.safety)
        body = cls._scalar_loop_body(ir, idx_var="i")
        pragma = f"    {pragma_line}\n" if pragma_line else ""

        return f"""{C_MATH_PREAMBLE}
void synax_kernel_tracked(const float* __restrict a,
                          const float* __restrict b,
                          float* __restrict out,
                          size_t n,
                          size_t* out_healed) {{
    const float bias = {bias_lit};
    const uint32_t bound_u32 = {bound_hex};
    (void)bias;
    (void)bound_u32;
    size_t healed = 0;
{pragma}    for (size_t i = 0; i < n; ++i) {{
{body}
    }}
    if (out_healed) *out_healed = healed;
}}

void synax_kernel(const float* a, const float* b, float* out, size_t n) {{
    synax_kernel_tracked(a, b, out, n, NULL);
}}
"""

    @classmethod
    def _neon_lane_block(cls, ir: SynaxIR, sfx: str) -> str:
        """Emit 1 SIMD vector lane group `sfx` (e.g. '0', '1', '2', '3') of 4 floats."""
        mode = ir.safety.nonfinite_mode
        pure_neon = ir.expr.can_use_pure_neon_intrinsics()
        lines: List[str] = []

        if mode != "preserve":
            lines.extend([
                f"            uint32x4_t ma{sfx} = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(va{sfx}), v_abs_mask), v_bound_u32);",
                f"            uint32x4_t mb{sfx} = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(vb{sfx}), v_abs_mask), v_bound_u32);",
                f"            healed_acc = vaddq_u32(healed_acc, vaddq_u32(vshrq_n_u32(vmvnq_u32(ma{sfx}), 31), vshrq_n_u32(vmvnq_u32(mb{sfx}), 31)));",
            ])

        if mode == "heal_inputs":
            lines.extend([
                f"            va{sfx} = vbslq_f32(ma{sfx}, va{sfx}, v_heal);",
                f"            vb{sfx} = vbslq_f32(mb{sfx}, vb{sfx}, v_heal);",
            ])
        elif mode in ("zero_output", "reject"):
            lines.extend([
                f"            va{sfx} = vbslq_f32(ma{sfx}, va{sfx}, v_zero);",
                f"            vb{sfx} = vbslq_f32(mb{sfx}, vb{sfx}, v_zero);",
            ])

        if pure_neon:
            neon_expr = ir.expr.to_neon_f32x4(var_a=f"va{sfx}", var_b=f"vb{sfx}", var_bias="vbias")
            lines.append(f"            float32x4_t vr{sfx} = {neon_expr};")
        else:
            c_scalar_lane = ir.expr.to_c_scalar(var_a=f"ta{sfx}[k]", var_b=f"tb{sfx}[k]", var_bias="bias")
            lines.extend([
                f"            float ta{sfx}[4], tb{sfx}[4], tr{sfx}[4];",
                f"            vst1q_f32(ta{sfx}, va{sfx}); vst1q_f32(tb{sfx}, vb{sfx});",
                f"            for (int k = 0; k < 4; ++k) {{ tr{sfx}[k] = {c_scalar_lane}; }}",
                f"            float32x4_t vr{sfx} = vld1q_f32(tr{sfx});",
            ])

        if mode == "zero_output":
            lines.append(f"            vr{sfx} = vbslq_f32(vandq_u32(ma{sfx}, mb{sfx}), vr{sfx}, v_heal);")

        if ir.safety.output_clamp is not None:
            lines.append(f"            vr{sfx} = vminq_f32(vmaxq_f32(vr{sfx}, v_clamp_lo), v_clamp_hi);")

        if mode == "reject":
            lines.append(f"            vr{sfx} = vbslq_f32(vandq_u32(ma{sfx}, mb{sfx}), vr{sfx}, v_nan);")

        return "\n".join(lines)

    @classmethod
    def _emit_neon_chunk_helper(cls, ir: SynaxIR, unroll_4x: bool) -> str:
        bias_lit = _format_c_float(ir.bias_default)
        heal_lit = _format_c_float(ir.safety.heal_value)
        bound_hex = cls._bound_u32_hex(ir.safety)
        tail_body = cls._scalar_loop_body(ir, idx_var="i")

        clamp_decls = ""
        if ir.safety.output_clamp is not None:
            lo_s = _format_c_float(ir.safety.output_clamp[0])
            hi_s = _format_c_float(ir.safety.output_clamp[1])
            clamp_decls = (
                f"        const float32x4_t v_clamp_lo = vdupq_n_f32({lo_s});\n"
                f"        const float32x4_t v_clamp_hi = vdupq_n_f32({hi_s});\n"
            )

        if not unroll_4x:
            b0 = cls._neon_lane_block(ir, "0")
            simd_loop = f"""        for (; i + 4 <= n; i += 4) {{
            float32x4_t va0 = vld1q_f32(a + i);
            float32x4_t vb0 = vld1q_f32(b + i);
{b0}
            vst1q_f32(out + i, vr0);
        }}"""
        else:
            blocks = "\n".join(cls._neon_lane_block(ir, str(k)) for k in range(4))
            simd_loop = f"""        for (; i + 16 <= n; i += 16) {{
            __builtin_prefetch(a + i + 128, 0, 1);
            __builtin_prefetch(b + i + 128, 0, 1);
            float32x4_t va0 = vld1q_f32(a + i + 0);
            float32x4_t va1 = vld1q_f32(a + i + 4);
            float32x4_t va2 = vld1q_f32(a + i + 8);
            float32x4_t va3 = vld1q_f32(a + i + 12);
            float32x4_t vb0 = vld1q_f32(b + i + 0);
            float32x4_t vb1 = vld1q_f32(b + i + 4);
            float32x4_t vb2 = vld1q_f32(b + i + 8);
            float32x4_t vb3 = vld1q_f32(b + i + 12);
{blocks}
            vst1q_f32(out + i + 0, vr0);
            vst1q_f32(out + i + 4, vr1);
            vst1q_f32(out + i + 8, vr2);
            vst1q_f32(out + i + 12, vr3);
        }}"""

        return f"""static inline void synax_neon_chunk(const float* __restrict a,
                                    const float* __restrict b,
                                    float* __restrict out,
                                    size_t n,
                                    size_t* out_healed) {{
    const float bias = {bias_lit};
    const uint32_t bound_u32 = {bound_hex};
    (void)bias;
    (void)bound_u32;
    size_t healed = 0;
    size_t i = 0;

#if defined(__aarch64__) || defined(_M_ARM64)
    if (b != NULL) {{
        const float32x4_t v_zero      = vdupq_n_f32(0.0f);
        const float32x4_t v_heal      = vdupq_n_f32({heal_lit});
        const float32x4_t v_nan       = vdupq_n_f32(NAN);
        const float32x4_t vbias       = vdupq_n_f32({bias_lit});
        const uint32x4_t  v_abs_mask  = vdupq_n_u32(0x7FFFFFFFu);
        const uint32x4_t  v_bound_u32 = vdupq_n_u32({bound_hex});
        uint32x4_t healed_acc = vdupq_n_u32(0);
        (void)v_zero; (void)v_heal; (void)v_nan; (void)vbias; (void)v_abs_mask; (void)v_bound_u32;
{clamp_decls}{simd_loop}
        healed += (size_t)vaddvq_u32(healed_acc);
    }}
#endif

    for (; i < n; ++i) {{
{tail_body}
    }}
    if (out_healed) *out_healed = healed;
}}
"""

    @classmethod
    def emit_neon_variant(cls, ir: SynaxIR, unroll_4x: bool = False) -> str:
        chunk_fn = cls._emit_neon_chunk_helper(ir, unroll_4x=unroll_4x)
        return f"""{C_MATH_PREAMBLE}
{chunk_fn}
void synax_kernel_tracked(const float* __restrict a,
                          const float* __restrict b,
                          float* __restrict out,
                          size_t n,
                          size_t* out_healed) {{
    synax_neon_chunk(a, b, out, n, out_healed);
}}

void synax_kernel(const float* a, const float* b, float* out, size_t n) {{
    synax_neon_chunk(a, b, out, n, NULL);
}}
"""

    @classmethod
    def emit_gcd_multicore_variant(cls, ir: SynaxIR) -> str:
        chunk_fn = cls._emit_neon_chunk_helper(ir, unroll_4x=True)
        return f"""{C_MATH_PREAMBLE}
{chunk_fn}
#if defined(__APPLE__)
typedef struct {{
    const float* a;
    const float* b;
    float* out;
    size_t base_len;
    size_t remainder;
    size_t chunk_healed[16];
    bool track_healed;
}} synax_gcd_ctx_t;

static void synax_gcd_worker(void* raw_ctx, size_t idx) {{
    synax_gcd_ctx_t* ctx = (synax_gcd_ctx_t*)raw_ctx;
    size_t start = idx * ctx->base_len + (idx < ctx->remainder ? idx : ctx->remainder);
    size_t len   = ctx->base_len + (idx < ctx->remainder ? 1 : 0);
    size_t local_h = 0;
    synax_neon_chunk(
        ctx->a + start,
        ctx->b ? (ctx->b + start) : NULL,
        ctx->out + start,
        len,
        ctx->track_healed ? &local_h : NULL
    );
    ctx->chunk_healed[idx] = local_h;
}}
#endif

void synax_kernel_tracked(const float* __restrict a,
                          const float* __restrict b,
                          float* __restrict out,
                          size_t n,
                          size_t* out_healed) {{
    if (n == 0) {{
        if (out_healed) *out_healed = 0;
        return;
    }}
#if defined(__APPLE__)
    const size_t parallel_threshold = (size_t)1 << 16; /* 65,536 floats */
    if (n >= parallel_threshold) {{
        long ncpu = sysconf(_SC_NPROCESSORS_ONLN);
        size_t chunks = (ncpu > 0) ? (size_t)ncpu : 4;
        if (chunks > 8) chunks = 8;
        if (chunks > n) chunks = n;

        synax_gcd_ctx_t ctx;
        memset(&ctx, 0, sizeof(ctx));
        ctx.a = a;
        ctx.b = b;
        ctx.out = out;
        ctx.base_len = n / chunks;
        ctx.remainder = n % chunks;
        ctx.track_healed = (out_healed != NULL);

        dispatch_queue_t q = dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0);
        dispatch_apply_f(chunks, q, &ctx, synax_gcd_worker);

        if (out_healed) {{
            size_t total_h = 0;
            for (size_t c = 0; c < chunks; ++c) total_h += ctx.chunk_healed[c];
            *out_healed = total_h;
        }}
        return;
    }}
#endif
    synax_neon_chunk(a, b, out, n, out_healed);
}}

void synax_kernel(const float* a, const float* b, float* out, size_t n) {{
    synax_kernel_tracked(a, b, out, n, NULL);
}}
"""


# ─────────────────────────────────────────────────────────────────
# 2. OPTIONAL LLM EVOLUTIONARY ADAPTER (v0.4 Claude CLI & Gemini)
# ─────────────────────────────────────────────────────────────────
def _query_claude_cli(prompt: str, model: str = "sonnet") -> str:
    claude_bin = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
    if not os.path.exists(claude_bin):
        raise RuntimeError("`claude` CLI bulunamadı.")
    with tempfile.TemporaryDirectory() as empty_dir:
        r = subprocess.run(
            [claude_bin, "-p", prompt, "--model", model],
            cwd=empty_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
    if r.returncode != 0:
        raise RuntimeError(f"Claude CLI hatası: {r.stderr.strip()[:300]}")
    return r.stdout


def _extract_llm_blocks(response: str) -> List[Dict[str, str]]:
    blocks = []
    for m in re.finditer(r"=== SURUM:\s*([^|\n]+)\|?([^\n]*)\n(.*?)=== SON", response, re.S):
        code = re.sub(r"^```\w*\n|```\s*$", "", m.group(3).strip(), flags=re.M)
        blocks.append({"name": m.group(1).strip(), "description": m.group(2).strip(), "code": code})
    return blocks


# ─────────────────────────────────────────────────────────────────
# 3. COMPILATION RESULT & UNIFIED COMPILER DRIVER
# ─────────────────────────────────────────────────────────────────
@dataclass
class CandidateResult:
    name: str
    description: str
    compiled: bool
    verified: bool
    median_ms: float = float("inf")
    max_abs_diff: float = 0.0
    note: str = ""
    dylib_path: str = ""
    c_path: str = ""


@dataclass
class CompilationResult:
    ir: SynaxIR
    cache_hit: bool
    cache_dir: Path
    ref_dylib_path: Path
    baseline_o1_dylib_path: Path
    winner_dylib_path: Path
    winner_c_path: Path
    winner_name: str
    ref_o1_median_ms: float
    clang_o3_median_ms: float
    winner_median_ms: float
    speedup_vs_scalar: float
    speedup_vs_clang_o3: float
    dual_ref_verified: bool
    suites_count: int
    candidates: List[CandidateResult] = field(default_factory=list)

    def create_axon_channel(self, myelin_threshold: int = 8, fixed_length: int = 32768):
        """
        Bind the verified unmyelinated scalar kernel (`baseline_o1.dylib`) and
        verified myelinated winning kernel (`kazanan.dylib`) to a live `SynaxAxonChannel`.
        """
        from synax_myelin import BiologicalMyelinEngine
        engine = BiologicalMyelinEngine()
        ch = engine.create_channel(self.ir.name, fixed_length, myelin_threshold=myelin_threshold)
        ch.bind_compiled_kernels(
            str(self.baseline_o1_dylib_path),
            str(self.winner_dylib_path),
            kernel_label=self.winner_name,
        )
        return ch


class SynaxCompiler:
    """Unified SYNAX v0.5 Compiler (`SYNAPSE -> IMMUNE -> AXON -> TYCON -> MYELIN`)."""

    def __init__(self, cache_root: Optional[Path] = None):
        self.cache_root = cache_root or get_hafiza_root()

    @staticmethod
    def _compile_dylib(c_source: str, c_path: Path, dylib_path: Path, cflags: List[str]) -> Tuple[bool, str]:
        ok_sec, sec_msg = SynaxSecurityGuard.verify_c_module_source(c_source)
        if not ok_sec:
            return False, f"Güvenlik duvarı engeli: {sec_msg}"

        c_path.write_text(c_source, encoding="utf-8")
        res = subprocess.run(
            ["clang", *cflags, str(c_path), "-lm", "-o", str(dylib_path)],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            err_line = res.stderr.strip().splitlines()[0] if res.stderr.strip() else "clang derleme hatası"
            return False, err_line
        return True, ""

    def compile(
        self,
        source_or_path: str,
        force_rebuild: bool = False,
        bench_n: int = 4_000_000,
        bench_repeats: int = 15,
        evolve_generations: int = 0,
        llm_provider: str = "off",
        verbose: bool = True,
    ) -> CompilationResult:
        t_start = time.perf_counter()
        ir = parse_sx(source_or_path)
        cache_dir = self.cache_root / ir.ir_hash
        rapor_path = cache_dir / "rapor.json"
        ref_dylib = cache_dir / "referans.dylib"
        base_o1_dylib = cache_dir / "baseline_o1.dylib"
        win_dylib = cache_dir / "kazanan.dylib"
        win_c = cache_dir / "kazanan.c"

        if verbose:
            p0, p1 = ir.param_names
            print(f"⚡ SYNAXC v0.5 — Modül: {ir.name} [IR #{ir.ir_hash}]")
            print(f"   • Biçim / Niyet : {ir.syntax_format} | {ir.intent_text}")
            print(f"   • Kanonik AST   : out = {ir.expr.to_human_formula(p0, p1)}")
            print(f"   • IMMUNE Kuralı : nonfinite={ir.safety.nonfinite_mode}"
                  + (f", bound=±{ir.safety.input_abs_bound:g}" if ir.safety.input_abs_bound else "")
                  + (f", clamp={ir.safety.output_clamp}" if ir.safety.output_clamp else ""))

        # 1. MYELIN PERSISTENT CACHE CHECK
        if (
            not force_rebuild
            and rapor_path.exists()
            and ref_dylib.exists()
            and base_o1_dylib.exists()
            and win_dylib.exists()
        ):
            ok_sig, _ = SynaxSecurityGuard.verify_json_file(str(rapor_path))
            if ok_sig:
                rapor = json.loads(rapor_path.read_text(encoding="utf-8"))
                dt_ms = (time.perf_counter() - t_start) * 1000.0
                if verbose:
                    print(
                        f"\n🧠 [MYELIN HAFIZA İSABETİ] {dt_ms:.2f} ms içinde doğrulandı:\n"
                        f"   • Kazanan Çekirdek : {rapor['kazanan']} ({rapor['kazanan_ms']:.3f} ms)\n"
                        f"   • Hızlanma         : Skaler C'ye göre {rapor['hizlanma_skaler']:.2f}x | "
                        f"clang -O3'e göre {rapor['hizlanma_clang_o3']:.2f}x"
                    )
                return CompilationResult(
                    ir=ir,
                    cache_hit=True,
                    cache_dir=cache_dir,
                    ref_dylib_path=ref_dylib,
                    baseline_o1_dylib_path=base_o1_dylib,
                    winner_dylib_path=win_dylib,
                    winner_c_path=win_c,
                    winner_name=rapor["kazanan"],
                    ref_o1_median_ms=rapor["referans_o1_ms"],
                    clang_o3_median_ms=rapor["clang_o3_ms"],
                    winner_median_ms=rapor["kazanan_ms"],
                    speedup_vs_scalar=rapor["hizlanma_skaler"],
                    speedup_vs_clang_o3=rapor["hizlanma_clang_o3"],
                    dual_ref_verified=True,
                    suites_count=rapor.get("test_kumesi_sayisi", 19),
                )

        cache_dir.mkdir(parents=True, exist_ok=True)
        suites = build_adversarial_suites(input_abs_bound=ir.safety.input_abs_bound)

        # 2. DUAL-REFERENCE SEMANTIC VERIFICATION GATE
        if verbose:
            print("\n① [SYNAPSE + IMMUNE] Çift-Referans Semantik Doğrulama…")

        ref_c_code = SynaxCodeGenerator.emit_scalar_variant(
            ir, pragma_line="#pragma clang loop vectorize(disable) unroll(disable)"
        )
        ok_ref, err_ref = self._compile_dylib(ref_c_code, cache_dir / "referans.c", ref_dylib, SHARED_CFLAGS_O0_REF)
        if not ok_ref:
            raise RuntimeError(f"Referans C11 derlemesi başarısız: {err_ref}")
        ok_o1, err_o1 = self._compile_dylib(
            ref_c_code, cache_dir / "baseline_o1.c", base_o1_dylib, SHARED_CFLAGS_O1_SCALAR
        )
        if not ok_o1:
            raise RuntimeError(f"Skaler O1 temel derlemesi başarısız: {err_o1}")

        ref_kernel = LoadedKernel(str(ref_dylib), name="referans_c11_o0")
        base_o1_kernel = LoadedKernel(str(base_o1_dylib), name="baseline_scalar_o1")

        dual_rep = verify_dual_reference_offline(ir, ref_kernel, suites)
        if llm_provider == "claude":
            # Optional Dual-LLM Reference Ambiguity Check (from SYNAX v0.4)
            prompt = (
                "You write C11 for Apple Silicon (arm64, clang). Exact signature, exported, no main():\n"
                "void synax_kernel(const float* a, const float* b, float* out, size_t n)\n"
                "Output ONLY:\n=== SURUM: llm_ref | skaler referans\n<complete C source>\n=== SON\n"
                f"INTENT: {ir.intent_text}\nRULES: {ir.rule_text}\n"
            )
            blocks = _extract_llm_blocks(_query_claude_cli(prompt))
            if blocks:
                ok_l, _ = self._compile_dylib(
                    blocks[0]["code"], cache_dir / "llm_ref.c", cache_dir / "llm_ref.dylib", SHARED_CFLAGS_O0_REF
                )
                if ok_l:
                    llm_k = LoadedKernel(str(cache_dir / "llm_ref.dylib"), name="llm_ref")
                    v_llm = verify_against_reference(llm_k, ref_kernel, suites)
                    if not v_llm.passed:
                        raise DualReferenceMismatchError(
                            f"LLM referansı ile deterministik IR uyuşmadı: {v_llm.failure_reason}"
                        )

        ref_o1_ms = benchmark_kernel(base_o1_kernel, n=bench_n, repeats=bench_repeats)
        if verbose:
            print(
                f"   ✓ Python IEEE-754 AST Referansı == C11 (-O0) Referansı "
                f"(maks fark: {dual_rep.max_abs_diff:.2e}, {dual_rep.suites_tested} semantik küme)"
            )
            print(f"   • Miyelinsiz Skaler C11 Temeli (-O1, vektörsüz): {ref_o1_ms:.3f} ms (N={bench_n:,})")

        # 3. AXON & TYCON CANDIDATE SYNTHESIS + 19-SUITE DIFFERENTIAL VERIFICATION
        if verbose:
            print(f"\n② [AXON + TYCON] Aday Çekirdek Sentezi & {len(suites)} Kümeli Diferansiyel Eleme…")

        specs: List[Tuple[str, str, str, List[str]]] = [
            (
                "v0_clang_o3_scalar",
                "Düz C11 + clang -O3 otomatik vektörleme (adil derleyici temeli)",
                SynaxCodeGenerator.emit_scalar_variant(ir),
                SHARED_CFLAGS_O3,
            ),
            (
                "v1_unroll4_scalar",
                "4x döngü açmalı süperskaler C11 boru hattı",
                SynaxCodeGenerator.emit_scalar_variant(
                    ir, pragma_line="#pragma clang loop vectorize(disable) unroll_count(4)"
                ),
                SHARED_CFLAGS_O3,
            ),
            (
                "v2_neon_simd",
                "Açık ARM64 NEON (float32x4_t) + bit-seviyesi IMMUNE maskesi",
                SynaxCodeGenerator.emit_neon_variant(ir, unroll_4x=False),
                SHARED_CFLAGS_O3,
            ),
            (
                "v3_neon_4acc_prefetch",
                "4x ARM64 NEON (16 float/adım) + Ranvier __builtin_prefetch",
                SynaxCodeGenerator.emit_neon_variant(ir, unroll_4x=True),
                SHARED_CFLAGS_O3,
            ),
            (
                "v4_gcd_multicore_neon",
                "Apple GCD çok çekirdek (dispatch_apply_f) + 4x NEON Sıçramalı",
                SynaxCodeGenerator.emit_gcd_multicore_variant(ir),
                SHARED_CFLAGS_O3,
            ),
        ]

        # Respect explicit scalar-only target hint if requested
        if ir.target_hint == "scalar":
            specs = specs[:2]
        elif ir.target_hint == "neon":
            specs = specs[:4]

        candidate_results: List[CandidateResult] = []
        verified_pool: List[Tuple[CandidateResult, str]] = []
        clang_o3_ms: Optional[float] = None

        for v_name, v_desc, v_code, v_flags in specs:
            c_file = cache_dir / f"{v_name}.c"
            so_file = cache_dir / f"{v_name}.dylib"
            ok_c, err_c = self._compile_dylib(v_code, c_file, so_file, v_flags)
            if not ok_c:
                if verbose:
                    print(f"   ✗ {v_name:<24} DERLENMEDİ — {err_c[:80]}")
                candidate_results.append(
                    CandidateResult(name=v_name, description=v_desc, compiled=False, verified=False, note=err_c)
                )
                continue

            cand_k = LoadedKernel(str(so_file), name=v_name)
            v_rep: VerificationReport = verify_against_reference(cand_k, ref_kernel, suites)
            if not v_rep.passed:
                if verbose:
                    print(f"   ✗ {v_name:<24} ELENDİ (Semantik Sapma) — {v_rep.failure_reason}")
                candidate_results.append(
                    CandidateResult(
                        name=v_name,
                        description=v_desc,
                        compiled=True,
                        verified=False,
                        max_abs_diff=v_rep.max_abs_diff,
                        note=v_rep.failure_reason,
                    )
                )
                continue

            ms = benchmark_kernel(cand_k, n=bench_n, repeats=bench_repeats)
            if v_name == "v0_clang_o3_scalar":
                clang_o3_ms = ms

            cr = CandidateResult(
                name=v_name,
                description=v_desc,
                compiled=True,
                verified=True,
                median_ms=ms,
                max_abs_diff=v_rep.max_abs_diff,
                note=f"{v_rep.suites_tested}/{len(suites)} küme geçti",
                dylib_path=str(so_file),
                c_path=str(c_file),
            )
            candidate_results.append(cr)
            verified_pool.append((cr, v_code))
            if verbose:
                print(
                    f"   ✓ {v_name:<24} {ms:8.3f} ms | maks fark: {v_rep.max_abs_diff:.2e} | {v_desc}"
                )

        # Optional LLM evolutionary mutation rounds (v0.4 `--nesil N --llm claude`)
        if evolve_generations > 0 and llm_provider == "claude" and verified_pool:
            for gen in range(1, evolve_generations + 1):
                verified_pool.sort(key=lambda pair: pair[0].median_ms)
                best_cr, best_code = verified_pool[0]
                if verbose:
                    print(f"\n③ [TYCON EVRİM — Nesil {gen}] En iyi ({best_cr.name}: {best_cr.median_ms:.3f} ms) mutasyona uğratılıyor…")
                mut_prompt = (
                    "You write C11 for Apple Silicon (arm64, clang). Exact signature, exported, no main():\n"
                    "void synax_kernel(const float* a, const float* b, float* out, size_t n)\n"
                    "Do NOT use -ffast-math tricks that alter NaN/Inf. Output 2 blocks:\n"
                    "=== SURUM: <name> | <Turkish description>\n<complete C source>\n=== SON\n"
                    f"Current best ({best_cr.name}, {best_cr.median_ms:.3f} ms):\n{best_code}\n"
                    f"REFERENCE:\n{ref_c_code}\n"
                )
                for idx_m, blk in enumerate(_extract_llm_blocks(_query_claude_cli(mut_prompt))):
                    m_name = re.sub(r"\W+", "_", f"mut_g{gen}_{idx_m}_{blk['name']}")[:40]
                    c_file = cache_dir / f"{m_name}.c"
                    so_file = cache_dir / f"{m_name}.dylib"
                    ok_c, err_c = self._compile_dylib(blk["code"], c_file, so_file, SHARED_CFLAGS_O3)
                    if not ok_c:
                        continue
                    cand_k = LoadedKernel(str(so_file), name=m_name)
                    v_rep = verify_against_reference(cand_k, ref_kernel, suites)
                    if not v_rep.passed:
                        if verbose:
                            print(f"   ✗ {m_name:<24} ELENDİ — {v_rep.failure_reason}")
                        continue
                    ms = benchmark_kernel(cand_k, n=bench_n, repeats=bench_repeats)
                    cr = CandidateResult(
                        name=m_name,
                        description=blk["description"],
                        compiled=True,
                        verified=True,
                        median_ms=ms,
                        max_abs_diff=v_rep.max_abs_diff,
                        dylib_path=str(so_file),
                        c_path=str(c_file),
                    )
                    candidate_results.append(cr)
                    verified_pool.append((cr, blk["code"]))
                    if verbose:
                        print(f"   ✓ {m_name:<24} {ms:8.3f} ms | {blk['description']}")

        if not verified_pool:
            raise RuntimeError("Hiçbir optimize aday 19-kümeli diferansiyel doğrulamayı geçemedi!")

        verified_pool.sort(key=lambda pair: pair[0].median_ms)
        winner_cr, winner_code = verified_pool[0]
        if clang_o3_ms is None:
            clang_o3_ms = ref_o1_ms

        # Persist winning C & dylib into canonical Myelin cache slots
        win_c.write_text(winner_code, encoding="utf-8")
        shutil.copy2(winner_cr.dylib_path, win_dylib)

        speedup_scalar = ref_o1_ms / max(winner_cr.median_ms, 1e-9)
        speedup_o3 = clang_o3_ms / max(winner_cr.median_ms, 1e-9)

        rapor_payload: Dict[str, Any] = {
            "modul": ir.name,
            "ir_hash": ir.ir_hash,
            "bicim": ir.syntax_format,
            "niyet": ir.intent_text,
            "kural": ir.rule_text,
            "formul": ir.expr.to_human_formula(*ir.param_names),
            "safety": ir.safety.to_dict(),
            "bench_n": bench_n,
            "referans_o1_ms": round(ref_o1_ms, 4),
            "clang_o3_ms": round(clang_o3_ms, 4),
            "kazanan": winner_cr.name,
            "kazanan_ms": round(winner_cr.median_ms, 4),
            "hizlanma_skaler": round(speedup_scalar, 3),
            "hizlanma_clang_o3": round(speedup_o3, 3),
            "test_kumesi_sayisi": len(suites),
            "tablo": [
                {
                    "ad": c.name,
                    "dogrulandi": c.verified,
                    "ms": round(c.median_ms, 4) if c.verified else None,
                    "maks_fark": c.max_abs_diff,
                    "aciklama": c.description,
                }
                for c in candidate_results
            ],
            "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        rapor_payload["_integrity_sha256"] = SynaxSecurityGuard.compute_canonical_sha256(rapor_payload)
        rapor_path.write_text(json.dumps(rapor_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if verbose:
            print(
                f"\n🏆 [MYELIN ŞAMPİYONU] {winner_cr.name} — {winner_cr.median_ms:.3f} ms (Medyan)\n"
                f"   • Skaler C (-O1) Karşısında : {speedup_scalar:.2f}x hızlı ({ref_o1_ms:.3f} ms -> {winner_cr.median_ms:.3f} ms)\n"
                f"   • clang -O3 Karşısında      : {speedup_o3:.2f}x hızlı ({clang_o3_ms:.3f} ms -> {winner_cr.median_ms:.3f} ms)\n"
                f"   • Kriptografik Hafıza Kaydı : {cache_dir}"
            )

        return CompilationResult(
            ir=ir,
            cache_hit=False,
            cache_dir=cache_dir,
            ref_dylib_path=ref_dylib,
            baseline_o1_dylib_path=base_o1_dylib,
            winner_dylib_path=win_dylib,
            winner_c_path=win_c,
            winner_name=winner_cr.name,
            ref_o1_median_ms=ref_o1_ms,
            clang_o3_median_ms=clang_o3_ms,
            winner_median_ms=winner_cr.median_ms,
            speedup_vs_scalar=speedup_scalar,
            speedup_vs_clang_o3=speedup_o3,
            dual_ref_verified=True,
            suites_count=len(suites),
            candidates=candidate_results,
        )


# ─────────────────────────────────────────────────────────────────
# 4. BACKWARD-COMPATIBLE STANDALONE BINARY WRAPPER
# ─────────────────────────────────────────────────────────────────
class SynaxNativeCompiler(SynaxCompiler):
    """Legacy-compatible wrapper around `SynaxCompiler` supporting standalone C binary output."""

    def compile_to_binary(self, sx_text: str, output_bin_path: Optional[str] = None) -> str:
        res = self.compile(sx_text, verbose=True)
        os.makedirs(BUILD_DIR, exist_ok=True)
        bin_path = output_bin_path or os.path.join(BUILD_DIR, f"synax_{res.ir.name}_{res.ir.ir_hash}_bin")
        driver_c = os.path.join(BUILD_DIR, f"synax_{res.ir.name}_{res.ir.ir_hash}_main.c")

        winner_src = res.winner_c_path.read_text(encoding="utf-8")
        standalone_src = (
            winner_src
            + f"""
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {{
    size_t N = (argc > 1) ? (size_t)atol(argv[1]) : 1000000;
    float* a = (float*)malloc(N * sizeof(float));
    float* b = (float*)malloc(N * sizeof(float));
    float* out = (float*)malloc(N * sizeof(float));
    for (size_t i = 0; i < N; ++i) {{
        a[i] = 1.5f + (float)(i % 10) * 0.1f;
        b[i] = 0.8f + (float)(i % 7) * 0.05f;
    }}
    size_t healed = 0;
    synax_kernel_tracked(a, b, out, N, &healed);
    printf("[SYNAX Native Binary] %s (%s) | N=%zu | out[0..3]=[%.4f, %.4f, %.4f, %.4f] | healed=%zu\\n",
           "{res.ir.name}", "{res.winner_name}", N,
           N > 0 ? out[0] : 0.0f, N > 1 ? out[1] : 0.0f,
           N > 2 ? out[2] : 0.0f, N > 3 ? out[3] : 0.0f, healed);
    free(a); free(b); free(out);
    return 0;
}}
"""
        )
        Path(driver_c).write_text(standalone_src, encoding="utf-8")
        subprocess.run(
            ["clang", "-O3", "-mcpu=native", "-std=c11", driver_c, "-lm", "-o", bin_path],
            check=True,
        )
        return bin_path


def main():
    ap = argparse.ArgumentParser(description="SYNAXC v0.5 — Birleştirilmiş Doğrulamalı C11/NEON/Myelin Derleyicisi")
    ap.add_argument("sx", help=".sx kaynak dosyası veya doğal dil niyeti")
    ap.add_argument("--yeniden", action="store_true", help="Miyelin önbelleğini yok sayıp baştan derle ve doğrula")
    ap.add_argument("--n", type=int, default=4_000_000, help="Benchmark vektör boyutu (varsayılan: 4,000,000)")
    ap.add_argument("--tekrar", type=int, default=15, help="Isınmış önbellek medyan tekrar sayısı (varsayılan: 15)")
    ap.add_argument("--nesil", type=int, default=0, help="İsteğe bağlı LLM evrim nesli sayısı")
    ap.add_argument("--llm", choices=["off", "claude"], default="off", help="İsteğe bağlı LLM mutasyon sağlayıcısı")
    args = ap.parse_args()

    compiler = SynaxCompiler()
    try:
        compiler.compile(
            args.sx,
            force_rebuild=args.yeniden,
            bench_n=args.n,
            bench_repeats=args.tekrar,
            evolve_generations=args.nesil,
            llm_provider=args.llm,
            verbose=True,
        )
    except DualReferenceMismatchError as exc:
        print(f"\n✗ [SEMANTİK BELİRSİZLİK HATASI] {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"\n✗ [SYNAXC HATA] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
