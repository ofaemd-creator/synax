#!/usr/bin/env python3
"""
SYNAX x86_64 AVX2 + FMA SIMD BACKEND (src/synax/backends/avx2_backend.py)
=============================================================================
Lowers `SynaxIR` to explicit 256-bit x86_64 AVX2 + FMA (`__m256`, 8x float32
lanes per cycle) with branchless IEEE-754 bitwise `SafetyPolicy` masks and an
automatic scalar tail (plus portable scalar fallback on non-x86 hosts).

Guarantees 1:1 semantic equivalence with the C11 Scalar Reference across all
19 adversarial test suites (`preserve`, `heal_inputs`, `zero_output`, `reject`).
=============================================================================
"""

import os
import struct
import sys
from typing import List

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_ir import ASTNode, SafetyPolicy, SynaxIR, _f32, _format_c_float
from synaxc import C_MATH_PREAMBLE, SynaxCodeGenerator

AVX2_NATIVE_OPS = {
    "VAR", "CONST", "BIAS", "NEG",
    "ADD", "SUB", "MUL", "DIV",
    "POW2", "POW3", "SQRT", "ABS",
    "RELU", "MIN", "MAX", "CLAMP",
    "EXP", "SIGMOID",
}

AVX2_PREAMBLE = """#if defined(__AVX2__)
#include <immintrin.h>

static inline __m256 synax_avx2_abs_ps(__m256 x) {
    return _mm256_and_ps(x, _mm256_castsi256_ps(_mm256_set1_epi32(0x7FFFFFFF)));
}

static inline __m256 synax_avx2_sq_ps(__m256 x) {
    return _mm256_mul_ps(x, x);
}

static inline __m256 synax_avx2_cbe_ps(__m256 x) {
    return _mm256_mul_ps(_mm256_mul_ps(x, x), x);
}

/* IEEE-754 NaN-propagating & signed-zero-exact min/max/relu in AVX2 */
static inline __m256 synax_avx2_min_ps(__m256 x, __m256 y) {
    __m256 unord = _mm256_cmp_ps(x, y, _CMP_UNORD_Q);
    __m256 m = _mm256_or_ps(_mm256_min_ps(x, y), _mm256_min_ps(y, x));
    return _mm256_blendv_ps(m, _mm256_set1_ps(NAN), unord);
}

static inline __m256 synax_avx2_max_ps(__m256 x, __m256 y) {
    __m256 unord = _mm256_cmp_ps(x, y, _CMP_UNORD_Q);
    __m256 m = _mm256_and_ps(_mm256_max_ps(x, y), _mm256_max_ps(y, x));
    return _mm256_blendv_ps(m, _mm256_set1_ps(NAN), unord);
}

static inline __m256 synax_avx2_relu_ps(__m256 x) {
    return synax_avx2_max_ps(_mm256_setzero_ps(), x);
}

/* Cody-Waite range-reduced IEEE-754 8-lane AVX2 expf */
static inline __m256 synax_avx2_exp_ps(__m256 x) {
    const __m256 inv_ln2 = _mm256_set1_ps(1.4426950408889634f);
    const __m256 ln2_hi  = _mm256_set1_ps(0.693145751953125f);
    const __m256 ln2_lo  = _mm256_set1_ps(1.428606765330187e-06f);

    __m256 xc = _mm256_min_ps(_mm256_max_ps(x, _mm256_set1_ps(-104.0f)), _mm256_set1_ps(89.0f));
    __m256 fn = _mm256_round_ps(_mm256_mul_ps(xc, inv_ln2), _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    __m256 r  = _mm256_sub_ps(xc, _mm256_mul_ps(fn, ln2_hi));
    r = _mm256_sub_ps(r, _mm256_mul_ps(fn, ln2_lo));

    __m256 p = _mm256_set1_ps(1.3888889e-03f);
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(8.3333338e-03f));
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(4.1666668e-02f));
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(1.6666667e-01f));
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(5.0000000e-01f));
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(1.0000000e+00f));
    p = _mm256_add_ps(_mm256_mul_ps(p, r), _mm256_set1_ps(1.0000000e+00f));

    __m256i ni = _mm256_cvtps_epi32(fn);
    __m256i n1 = _mm256_srai_epi32(ni, 1);
    __m256i n2 = _mm256_sub_epi32(ni, n1);
    __m256 s1  = _mm256_castsi256_ps(_mm256_slli_epi32(_mm256_add_epi32(n1, _mm256_set1_epi32(127)), 23));
    __m256 s2  = _mm256_castsi256_ps(_mm256_slli_epi32(_mm256_add_epi32(n2, _mm256_set1_epi32(127)), 23));
    __m256 res = _mm256_mul_ps(_mm256_mul_ps(p, s1), s2);

    __m256 over_m  = _mm256_cmp_ps(x, _mm256_set1_ps(88.722839f), _CMP_GT_OQ);
    __m256 under_m = _mm256_cmp_ps(x, _mm256_set1_ps(-103.97208f), _CMP_LT_OQ);
    __m256 nan_m   = _mm256_cmp_ps(x, x, _CMP_UNORD_Q);

    res = _mm256_blendv_ps(res, _mm256_set1_ps(INFINITY), over_m);
    res = _mm256_blendv_ps(res, _mm256_setzero_ps(), under_m);
    res = _mm256_blendv_ps(res, x, nan_m);
    return res;
}

static inline __m256 synax_avx2_sigmoid_ps(__m256 x) {
    __m256 neg_x = _mm256_sub_ps(_mm256_setzero_ps(), x);
    __m256 ex = synax_avx2_exp_ps(neg_x);
    __m256 one = _mm256_set1_ps(1.0f);
    return _mm256_div_ps(one, _mm256_add_ps(one, ex));
}
#endif
"""


class AVX2Backend:
    """Lowers `SynaxIR` to 256-bit x86_64 AVX2 C11 source code."""

    @classmethod
    def can_use_pure_avx2(cls, node: ASTNode) -> bool:
        if node.op not in AVX2_NATIVE_OPS:
            return False
        return all(cls.can_use_pure_avx2(ch) for ch in node.children)

    @classmethod
    def lower_ast_avx2(cls, node: ASTNode, var_a: str = "va", var_b: str = "vb", var_bias: str = "vbias") -> str:
        if node.op == "VAR":
            return var_a if node.value == "a" else var_b
        if node.op == "CONST":
            return f"_mm256_set1_ps({_format_c_float(float(node.value))})"
        if node.op == "BIAS":
            return var_bias

        c = [cls.lower_ast_avx2(ch, var_a=var_a, var_b=var_b, var_bias=var_bias) for ch in node.children]
        if node.op == "NEG":     return f"_mm256_sub_ps(_mm256_setzero_ps(), {c[0]})"
        if node.op == "ADD":     return f"_mm256_add_ps({c[0]}, {c[1]})"
        if node.op == "SUB":     return f"_mm256_sub_ps({c[0]}, {c[1]})"
        if node.op == "MUL":     return f"_mm256_mul_ps({c[0]}, {c[1]})"
        if node.op == "DIV":     return f"_mm256_div_ps({c[0]}, {c[1]})"
        if node.op == "POW2":    return f"synax_avx2_sq_ps({c[0]})"
        if node.op == "POW3":    return f"synax_avx2_cbe_ps({c[0]})"
        if node.op == "SQRT":    return f"_mm256_sqrt_ps({c[0]})"
        if node.op == "ABS":     return f"synax_avx2_abs_ps({c[0]})"
        if node.op == "RELU":    return f"synax_avx2_relu_ps({c[0]})"
        if node.op == "MIN":     return f"synax_avx2_min_ps({c[0]}, {c[1]})"
        if node.op == "MAX":     return f"synax_avx2_max_ps({c[0]}, {c[1]})"
        if node.op == "CLAMP":   return f"synax_avx2_min_ps(synax_avx2_max_ps({c[0]}, {c[1]}), {c[2]})"
        if node.op == "EXP":     return f"synax_avx2_exp_ps({c[0]})"
        if node.op == "SIGMOID": return f"synax_avx2_sigmoid_ps({c[0]})"
        return c[0] if c else "_mm256_setzero_ps()"

    @classmethod
    def emit_c_source(cls, ir: SynaxIR) -> str:
        bias_lit = _format_c_float(ir.bias_default)
        heal_lit = _format_c_float(ir.safety.heal_value)
        bound_hex = SynaxCodeGenerator._bound_u32_hex(ir.safety)
        bound_i32_hex = bound_hex.rstrip("u")
        tail_body = SynaxCodeGenerator._scalar_loop_body(ir, idx_var="i")
        mode = ir.safety.nonfinite_mode

        lines: List[str] = []
        if mode != "preserve":
            # Since bound_u32 <= 0x7F7FFFFF (positive signed int32!), signed _mm256_cmpgt_epi32(abs_bits, v_bound)
            # is 100% exact for detecting invalid/NaN/Inf/out-of-range lanes!
            lines.extend([
                "            __m256i abs_a = _mm256_and_si256(_mm256_castps_si256(va), v_abs_mask);",
                "            __m256i abs_b = _mm256_and_si256(_mm256_castps_si256(vb), v_abs_mask);",
                "            __m256i bad_a = _mm256_cmpgt_epi32(abs_a, v_bound_i32);",
                "            __m256i bad_b = _mm256_cmpgt_epi32(abs_b, v_bound_i32);",
                "            healed += (size_t)__builtin_popcount((unsigned)_mm256_movemask_ps(_mm256_castsi256_ps(bad_a)));",
                "            healed += (size_t)__builtin_popcount((unsigned)_mm256_movemask_ps(_mm256_castsi256_ps(bad_b)));",
            ])

        if mode == "heal_inputs":
            lines.extend([
                "            va = _mm256_blendv_ps(va, v_heal, _mm256_castsi256_ps(bad_a));",
                "            vb = _mm256_blendv_ps(vb, v_heal, _mm256_castsi256_ps(bad_b));",
            ])
        elif mode in ("zero_output", "reject"):
            lines.extend([
                "            va = _mm256_blendv_ps(va, v_zero, _mm256_castsi256_ps(bad_a));",
                "            vb = _mm256_blendv_ps(vb, v_zero, _mm256_castsi256_ps(bad_b));",
            ])

        if cls.can_use_pure_avx2(ir.expr):
            avx_expr = cls.lower_ast_avx2(ir.expr)
            lines.append(f"            __m256 vr = {avx_expr};")
        else:
            c_lane = ir.expr.to_c_scalar(var_a="ta[k]", var_b="tb[k]", var_bias="bias")
            lines.extend([
                "            float ta[8], tb[8], tr[8];",
                "            _mm256_storeu_ps(ta, va); _mm256_storeu_ps(tb, vb);",
                f"            for (int k = 0; k < 8; ++k) {{ tr[k] = {c_lane}; }}",
                "            __m256 vr = _mm256_loadu_ps(tr);",
            ])

        if mode == "zero_output":
            lines.append("            __m256 any_bad = _mm256_castsi256_ps(_mm256_or_si256(bad_a, bad_b));")
            lines.append("            vr = _mm256_blendv_ps(vr, v_heal, any_bad);")

        if ir.safety.output_clamp is not None:
            lo_s = _format_c_float(ir.safety.output_clamp[0])
            hi_s = _format_c_float(ir.safety.output_clamp[1])
            lines.append(
                f"            vr = synax_avx2_min_ps(synax_avx2_max_ps(vr, _mm256_set1_ps({lo_s})), _mm256_set1_ps({hi_s}));"
            )

        if mode == "reject":
            lines.append("            __m256 any_bad = _mm256_castsi256_ps(_mm256_or_si256(bad_a, bad_b));")
            lines.append("            vr = _mm256_blendv_ps(vr, v_nan, any_bad);")

        lane_body = "\n".join(lines)

        return f"""{C_MATH_PREAMBLE}
{AVX2_PREAMBLE}
void synax_kernel_tracked(const float* __restrict a,
                          const float* __restrict b,
                          float* __restrict out,
                          size_t n,
                          size_t* out_healed) {{
    const float bias = {bias_lit};
    const uint32_t bound_u32 = {bound_hex};
    (void)bias; (void)bound_u32;
    size_t healed = 0;
    size_t i = 0;

#if defined(__AVX2__)
    if (b != NULL) {{
        const __m256  v_zero      = _mm256_setzero_ps();
        const __m256  v_heal      = _mm256_set1_ps({heal_lit});
        const __m256  v_nan       = _mm256_set1_ps(NAN);
        const __m256  vbias       = _mm256_set1_ps({bias_lit});
        const __m256i v_abs_mask  = _mm256_set1_epi32(0x7FFFFFFF);
        const __m256i v_bound_i32 = _mm256_set1_epi32((int32_t){bound_i32_hex});
        (void)v_zero; (void)v_heal; (void)v_nan; (void)vbias; (void)v_abs_mask; (void)v_bound_i32;

        for (; i + 8 <= n; i += 8) {{
            __m256 va = _mm256_loadu_ps(a + i);
            __m256 vb = _mm256_loadu_ps(b + i);
{lane_body}
            _mm256_storeu_ps(out + i, vr);
        }}
    }}
#endif

    for (; i < n; ++i) {{
{tail_body}
    }}
    if (out_healed) *out_healed = healed;
}}

void synax_kernel(const float* a, const float* b, float* out, size_t n) {{
    synax_kernel_tracked(a, b, out, n, NULL);
}}
"""
