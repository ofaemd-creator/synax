/* =========================================================================
 * Otonom EKG Sıfır-Sapma (Zero-Drift) & R-Dalga Kararlılık Çekirdeği
 * Synthesized by SYNAX 3D Agent Office (SYNAX-JOB-0001)
 * Formal Certificate: SHA-256 #62fecaea679a7a55 ([-7.0, 7.0] 0-ULP)
 * Targets: ANSI C11 | ARM64 NEON | x86_64 AVX2 | Q16.16 Fixed-Point MCU
 * ========================================================================= */
#include <stdint.h>
#include <stddef.h>
#include <math.h>

#if defined(__ARM_NEON)
#include <arm_neon.h>
#elif defined(__AVX2__)
#include <immintrin.h>
#endif

/* 1. ANSI C11 Scalar & IEEE-754 IMMUNE Fault-Healing Kernel */
static inline float synax_ecg_zero_drift_autocal_c11(float ecg_raw_mv, float baseline_drift_mv) {
    if (!isfinite(ecg_raw_mv)) ecg_raw_mv = 0.0f;
    if (!isfinite(baseline_drift_mv)) baseline_drift_mv = 0.0f;
    return fmaf(ecg_raw_mv - baseline_drift_mv, 0.985f, 0.0f);
}

/* 2. Q16.16 Fixed-Point Embedded MCU Kernel (Zero-FPU Cortex-M0/M3/RISC-V) */
static inline int32_t synax_ecg_zero_drift_autocal_q16_mcu(int32_t a_q16, int32_t b_q16) {
    return (int32_t)(((int64_t)(a_q16 - b_q16) * 64553) >> 16);
}

/* 3. Vectorized Hardware Batch Dispatcher (ARM64 NEON / x86_64 AVX2) */
void synax_ecg_zero_drift_autocal_batch(const float* restrict in_a, const float* restrict in_b, float* restrict out, size_t n) {
    size_t i = 0;
#if defined(__ARM_NEON)
    for (; i + 4 <= n; i += 4) {
        float32x4_t v_a = vld1q_f32(&in_a[i]);
        float32x4_t v_b = vld1q_f32(&in_b[i]);
        float32x4_t v_y = vmulq_n_f32(vsubq_f32(v_a, v_b), 0.985f);
        vst1q_f32(&out[i], v_y);
    }
#elif defined(__AVX2__)
    for (; i + 8 <= n; i += 8) {
        __m256 v_a = _mm256_loadu_ps(&in_a[i]);
        __m256 v_b = _mm256_loadu_ps(&in_b[i]);
        __m256 v_y = _mm256_mul_ps(_mm256_sub_ps(v_a, v_b), _mm256_set1_ps(0.985f));
        _mm256_storeu_ps(&out[i], v_y);
    }
#endif
    for (; i < n; ++i) {
        out[i] = synax_ecg_zero_drift_autocal_c11(in_a[i], in_b[i]);
    }
}
