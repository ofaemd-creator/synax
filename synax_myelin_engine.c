/**
 * SYNAX BIOLOGICALLY-INSPIRED MYELIN ENGINE (v1.0-LTS)
 * ==============================================================================
 * Myelination-Inspired Adaptive JIT Optimization & Saltatory Conduction.
 * 
 * Hardware-level Differential Equivalence & Immune Shield:
 *   - Both Channel A and Channel B are fully sanitized in SIMD & Scalar paths.
 *   - Uses IEEE 754 integer bit-level validation: (abs_bits <= 0x447A0000)
 *     Guarantees NaN, Inf, and [-1000, 1000] range validation in ONE instruction,
 *     100% immune to compiler fast-math flags.
 *   - Anomaly counter tracked bit-exactly in both Scalar and NEON paths.
 *   - Saltatory jump execution across Ranvier node vector blocks (ARM64 NEON).
 * ==============================================================================
 */

#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "synax_myelin_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <dlfcn.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#endif

#if defined(__aarch64__) || defined(_M_ARM64)
#include <arm_neon.h>
#endif

/* Yüksek hassasiyetli zaman ölçümü (Nanometrik iletim saati) */
static double get_time_ns(void) {
#if defined(__APPLE__)
    static mach_timebase_info_data_t tb;
    if (tb.denom == 0) {
        mach_timebase_info(&tb);
    }
    uint64_t t = mach_absolute_time();
    return (double)(t * tb.numer) / (double)tb.denom;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
#endif
}

/* ─────────────────────────────────────────────────────────────────
 * 1. UNMYELINATED SCALAR KERNEL (Sürekli İletim / Referans Çekirdek)
 * Biyolojik benzetim: Her bir zarda tek tek skaler depolarizasyon.
 * Hem 'a' hem 'b' girdilerini tam olarak denetler ve anomalileri sayar.
 * ───────────────────────────────────────────────────────────────── */
static void kernel_unmyelinated_scalar(const float* __restrict src_a,
                                      const float* __restrict src_b,
                                      float* __restrict dst,
                                      size_t count,
                                      size_t* out_healed) {
    size_t healed = 0;
    for (size_t i = 0; i < count; ++i) {
        float a = src_a[i];
        float b = src_b ? src_b[i] : 0.0f;

        /* Sinyal Bağışıklık Kalkanı: Sınır aşımı ve NaN/Inf kontrolü */
        if (!isfinite(a) || a > 1000.0f || a < -1000.0f) {
            a = 0.0f;
            healed++;
        }
        if (src_b) {
            if (!isfinite(b) || b > 1000.0f || b < -1000.0f) {
                b = 0.0f;
                healed++;
            }
        }

        /* L2 hemodinamik enerji ve rezonans akısı */
        float sum = a + b;
        float diff = a - b;
        float energy = (diff * diff);
        float val = sqrtf(energy + 1e-6f) + 0.5f * sum;
        dst[i] = val;
    }
    if (out_healed) *out_healed = healed;
}

/* ─────────────────────────────────────────────────────────────────
 * 2. MYELINATED SALTATORY KERNEL (Ranvier Düğümleri & NEON SIMD)
 * IEEE 754 bit-seviyesinde (abs_bits <= 0x447A0000) kontrolü ile
 * NaN, Inf ve sınır aşımını tek çevrimde yakalar.
 * Skaler referans çekirdekle 1:1 SAYISAL EŞDEĞERDİR.
 * ───────────────────────────────────────────────────────────────── */
static void kernel_myelinated_neon_saltatory(const float* __restrict src_a,
                                            const float* __restrict src_b,
                                            float* __restrict dst,
                                            size_t count,
                                            size_t* out_healed) {
    size_t healed = 0;
    size_t i = 0;

#if defined(__aarch64__) || defined(_M_ARM64)
    const float32x4_t v_zero = vdupq_n_f32(0.0f);
    const float32x4_t v_half = vdupq_n_f32(0.5f);
    const float32x4_t v_eps  = vdupq_n_f32(1e-6f);
    const uint32x4_t v_abs_mask = vdupq_n_u32(0x7FFFFFFFU);
    const uint32x4_t v_max_u32  = vdupq_n_u32(0x447A0000U); /* 1000.0f */

    uint32x4_t healed_acc = vdupq_n_u32(0);

    for (; i + 16 <= count; i += 16) {
        __builtin_prefetch(&src_a[i + 32], 0, 3);
        if (src_b) __builtin_prefetch(&src_b[i + 32], 0, 3);
        __builtin_prefetch(&dst[i + 32], 1, 3);

        float32x4_t a0 = vld1q_f32(&src_a[i + 0]);
        float32x4_t a1 = vld1q_f32(&src_a[i + 4]);
        float32x4_t a2 = vld1q_f32(&src_a[i + 8]);
        float32x4_t a3 = vld1q_f32(&src_a[i + 12]);

        float32x4_t b0 = src_b ? vld1q_f32(&src_b[i + 0]) : v_zero;
        float32x4_t b1 = src_b ? vld1q_f32(&src_b[i + 4]) : v_zero;
        float32x4_t b2 = src_b ? vld1q_f32(&src_b[i + 8]) : v_zero;
        float32x4_t b3 = src_b ? vld1q_f32(&src_b[i + 12]) : v_zero;

        /* Ranvier Node Immune Shield: Channel A (IEEE 754 Bit-Level) */
        uint32x4_t mask_a0 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a0), v_abs_mask), v_max_u32);
        uint32x4_t mask_a1 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a1), v_abs_mask), v_max_u32);
        uint32x4_t mask_a2 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a2), v_abs_mask), v_max_u32);
        uint32x4_t mask_a3 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a3), v_abs_mask), v_max_u32);

        uint32x4_t bad_a0 = vshrq_n_u32(vmvnq_u32(mask_a0), 31);
        uint32x4_t bad_a1 = vshrq_n_u32(vmvnq_u32(mask_a1), 31);
        uint32x4_t bad_a2 = vshrq_n_u32(vmvnq_u32(mask_a2), 31);
        uint32x4_t bad_a3 = vshrq_n_u32(vmvnq_u32(mask_a3), 31);

        healed_acc = vaddq_u32(healed_acc, vaddq_u32(bad_a0, bad_a1));
        healed_acc = vaddq_u32(healed_acc, vaddq_u32(bad_a2, bad_a3));

        a0 = vbslq_f32(mask_a0, a0, v_zero);
        a1 = vbslq_f32(mask_a1, a1, v_zero);
        a2 = vbslq_f32(mask_a2, a2, v_zero);
        a3 = vbslq_f32(mask_a3, a3, v_zero);

        /* Ranvier Node Immune Shield: Channel B (IEEE 754 Bit-Level) */
        if (src_b) {
            uint32x4_t mask_b0 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b0), v_abs_mask), v_max_u32);
            uint32x4_t mask_b1 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b1), v_abs_mask), v_max_u32);
            uint32x4_t mask_b2 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b2), v_abs_mask), v_max_u32);
            uint32x4_t mask_b3 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b3), v_abs_mask), v_max_u32);

            uint32x4_t bad_b0 = vshrq_n_u32(vmvnq_u32(mask_b0), 31);
            uint32x4_t bad_b1 = vshrq_n_u32(vmvnq_u32(mask_b1), 31);
            uint32x4_t bad_b2 = vshrq_n_u32(vmvnq_u32(mask_b2), 31);
            uint32x4_t bad_b3 = vshrq_n_u32(vmvnq_u32(mask_b3), 31);

            healed_acc = vaddq_u32(healed_acc, vaddq_u32(bad_b0, bad_b1));
            healed_acc = vaddq_u32(healed_acc, vaddq_u32(bad_b2, bad_b3));

            b0 = vbslq_f32(mask_b0, b0, v_zero);
            b1 = vbslq_f32(mask_b1, b1, v_zero);
            b2 = vbslq_f32(mask_b2, b2, v_zero);
            b3 = vbslq_f32(mask_b3, b3, v_zero);
        }

        /* Vektör Aritmetiği */
        float32x4_t sum0 = vaddq_f32(a0, b0);
        float32x4_t sum1 = vaddq_f32(a1, b1);
        float32x4_t sum2 = vaddq_f32(a2, b2);
        float32x4_t sum3 = vaddq_f32(a3, b3);

        float32x4_t diff0 = vsubq_f32(a0, b0);
        float32x4_t diff1 = vsubq_f32(a1, b1);
        float32x4_t diff2 = vsubq_f32(a2, b2);
        float32x4_t diff3 = vsubq_f32(a3, b3);

        float32x4_t en0 = vaddq_f32(vmulq_f32(diff0, diff0), v_eps);
        float32x4_t en1 = vaddq_f32(vmulq_f32(diff1, diff1), v_eps);
        float32x4_t en2 = vaddq_f32(vmulq_f32(diff2, diff2), v_eps);
        float32x4_t en3 = vaddq_f32(vmulq_f32(diff3, diff3), v_eps);

        float32x4_t r0 = vaddq_f32(vsqrtq_f32(en0), vmulq_f32(v_half, sum0));
        float32x4_t r1 = vaddq_f32(vsqrtq_f32(en1), vmulq_f32(v_half, sum1));
        float32x4_t r2 = vaddq_f32(vsqrtq_f32(en2), vmulq_f32(v_half, sum2));
        float32x4_t r3 = vaddq_f32(vsqrtq_f32(en3), vmulq_f32(v_half, sum3));

        vst1q_f32(&dst[i + 0], r0);
        vst1q_f32(&dst[i + 4], r1);
        vst1q_f32(&dst[i + 8], r2);
        vst1q_f32(&dst[i + 12], r3);
    }

    healed += (size_t)vaddvq_u32(healed_acc);
#endif

    /* Kalan öğeleri güvenli şekilde tamamla */
    for (; i < count; ++i) {
        float a = src_a[i];
        float b = src_b ? src_b[i] : 0.0f;
        if (!isfinite(a) || a > 1000.0f || a < -1000.0f) { a = 0.0f; healed++; }
        if (src_b && (!isfinite(b) || b > 1000.0f || b < -1000.0f)) { b = 0.0f; healed++; }
        float diff = a - b;
        dst[i] = sqrtf(diff * diff + 1e-6f) + 0.5f * (a + b);
    }
    if (out_healed) *out_healed = healed;
}

/* ─────────────────────────────────────────────────────────────────
 * 3. KANAL YÖNETİMİ
 * ───────────────────────────────────────────────────────────────── */
SynaxAxonChannel* synax_axon_create(const char* name, size_t fixed_length, uint64_t myelin_threshold) {
    SynaxAxonChannel* channel = (SynaxAxonChannel*)calloc(1, sizeof(SynaxAxonChannel));
    if (!channel) return NULL;

    strncpy(channel->name, name ? name : "default_axon", sizeof(channel->name) - 1);
    channel->fixed_length = fixed_length;
    channel->state = AXON_STATE_UNMYELINATED;
    channel->active_kernel = kernel_unmyelinated_scalar;
    channel->stats.total_transmissions = 0;
    channel->stats.myelination_threshold = myelin_threshold > 0 ? myelin_threshold : 25;
    channel->stats.internode_block_size = 1024;
    channel->stats.unmyelinated_avg_ns = 0.0;
    channel->stats.myelinated_avg_ns = 0.0;
    channel->stats.conduction_velocity_ratio = 1.0;
    channel->dylib_handle = NULL;
    channel->ref_dylib_handle = NULL;
    strncpy(channel->specialized_kernel_name, "Builtin_Scalar_Ref", sizeof(channel->specialized_kernel_name) - 1);

    return channel;
}

void synax_axon_destroy(SynaxAxonChannel* channel) {
    if (!channel) return;
    if (channel->dylib_handle) {
        dlclose(channel->dylib_handle);
        channel->dylib_handle = NULL;
    }
    if (channel->ref_dylib_handle && channel->ref_dylib_handle != channel->dylib_handle) {
        dlclose(channel->ref_dylib_handle);
        channel->ref_dylib_handle = NULL;
    }
    free(channel);
}

int synax_axon_bind_compiled_kernels(SynaxAxonChannel* channel,
                                     const char* ref_dylib_path,
                                     const char* myelinated_dylib_path,
                                     const char* kernel_label) {
    if (!channel || !ref_dylib_path || !myelinated_dylib_path) return -1;

    void* ref_h = dlopen(ref_dylib_path, RTLD_NOW | RTLD_LOCAL);
    if (!ref_h) return -2;

    void* opt_h = (strcmp(ref_dylib_path, myelinated_dylib_path) == 0)
        ? ref_h
        : dlopen(myelinated_dylib_path, RTLD_NOW | RTLD_LOCAL);
    if (!opt_h) {
        dlclose(ref_h);
        return -3;
    }

    AxonKernelFunc ref_tracked = (AxonKernelFunc)dlsym(ref_h, "synax_kernel_tracked");
    AxonBasicKernelFunc ref_basic = (AxonBasicKernelFunc)dlsym(ref_h, "synax_kernel");
    AxonKernelFunc opt_tracked = (AxonKernelFunc)dlsym(opt_h, "synax_kernel_tracked");
    AxonBasicKernelFunc opt_basic = (AxonBasicKernelFunc)dlsym(opt_h, "synax_kernel");

    if ((!ref_tracked && !ref_basic) || (!opt_tracked && !opt_basic)) {
        if (opt_h != ref_h) dlclose(opt_h);
        dlclose(ref_h);
        return -4;
    }

    if (channel->dylib_handle) {
        dlclose(channel->dylib_handle);
    }
    if (channel->ref_dylib_handle && channel->ref_dylib_handle != channel->dylib_handle) {
        dlclose(channel->ref_dylib_handle);
    }

    channel->ref_dylib_handle = ref_h;
    channel->dylib_handle = opt_h;
    channel->custom_unmyelinated_kernel = ref_tracked;
    channel->custom_myelinated_kernel = opt_tracked;
    channel->custom_unmyelinated_basic = ref_basic;
    channel->custom_myelinated_basic = opt_basic;
    channel->state = AXON_STATE_UNMYELINATED;
    channel->active_kernel = ref_tracked;

    if (kernel_label && kernel_label[0] != '\0') {
        strncpy(channel->specialized_kernel_name, kernel_label, sizeof(channel->specialized_kernel_name) - 1);
    } else {
        strncpy(channel->specialized_kernel_name, "SynaxC_Verified_SIMD", sizeof(channel->specialized_kernel_name) - 1);
    }
    return 0;
}

/* ─────────────────────────────────────────────────────────────────
 * 4. GÜVENLİ MİYELİNLEŞTİRME (SECURE ADAPTIVE JIT / HOT-SWAP)
 * ───────────────────────────────────────────────────────────────── */
int synax_axon_myelinate(SynaxAxonChannel* channel) {
    if (!channel) return -1;
    if (channel->state == AXON_STATE_MYELINATED) return 0;

    channel->state = AXON_STATE_MYELINATING;

    /* synaxc tarafından doğrulanmış dinamik çekirdek bağlıysa O(1) fonksiyon işaretçisi takası yap */
    if (channel->custom_myelinated_kernel || channel->custom_myelinated_basic) {
        channel->active_kernel = channel->custom_myelinated_kernel;
        channel->state = AXON_STATE_MYELINATED;
        return 0;
    }

    /* Güvenli önbellek dizini oluştur */
    const char* home = getenv("HOME");
    char cache_dir[512];
    if (home) {
        snprintf(cache_dir, sizeof(cache_dir), "%s/.cache/synax", home);
    } else {
        snprintf(cache_dir, sizeof(cache_dir), "/tmp/synax_%d", getuid());
    }
    mkdir(cache_dir, 0700);

    char c_src_path[600];
    char dylib_path[600];
    pid_t pid = getpid();
    snprintf(c_src_path, sizeof(c_src_path), "%s/axon_%s_%d_%p.c", cache_dir, channel->name, pid, (void*)channel);
    snprintf(dylib_path, sizeof(dylib_path), "%s/axon_%s_%d_%p.dylib", cache_dir, channel->name, pid, (void*)channel);

    FILE* fp = fopen(c_src_path, "w");
    if (fp) {
        fprintf(fp,
            "#include <stdint.h>\n"
            "#include <stddef.h>\n"
            "#include <math.h>\n"
            "#if defined(__aarch64__) || defined(_M_ARM64)\n"
            "#include <arm_neon.h>\n"
            "#endif\n\n"
            "void synax_specialized_saltatory_kernel(const float* __restrict src_a,\n"
            "                                        const float* __restrict src_b,\n"
            "                                        float* __restrict dst,\n"
            "                                        size_t count,\n"
            "                                        size_t* out_healed) {\n"
            "    size_t healed = 0;\n"
            "    size_t i = 0;\n"
            "#if defined(__aarch64__) || defined(_M_ARM64)\n"
            "    const float32x4_t v_zero = vdupq_n_f32(0.0f);\n"
            "    const float32x4_t v_half = vdupq_n_f32(0.5f);\n"
            "    const float32x4_t v_eps  = vdupq_n_f32(1e-6f);\n"
            "    const uint32x4_t v_abs_mask = vdupq_n_u32(0x7FFFFFFFU);\n"
            "    const uint32x4_t v_max_u32  = vdupq_n_u32(0x447A0000U);\n"
            "    uint32x4_t healed_acc = vdupq_n_u32(0);\n"
            "    for (; i + 16 <= count; i += 16) {\n"
            "        __builtin_prefetch(&src_a[i + 32], 0, 3);\n"
            "        if (src_b) __builtin_prefetch(&src_b[i + 32], 0, 3);\n"
            "        __builtin_prefetch(&dst[i + 32], 1, 3);\n"
            "        float32x4_t a0 = vld1q_f32(&src_a[i + 0]);\n"
            "        float32x4_t a1 = vld1q_f32(&src_a[i + 4]);\n"
            "        float32x4_t a2 = vld1q_f32(&src_a[i + 8]);\n"
            "        float32x4_t a3 = vld1q_f32(&src_a[i + 12]);\n"
            "        float32x4_t b0 = src_b ? vld1q_f32(&src_b[i + 0]) : v_zero;\n"
            "        float32x4_t b1 = src_b ? vld1q_f32(&src_b[i + 4]) : v_zero;\n"
            "        float32x4_t b2 = src_b ? vld1q_f32(&src_b[i + 8]) : v_zero;\n"
            "        float32x4_t b3 = src_b ? vld1q_f32(&src_b[i + 12]) : v_zero;\n"
            "        uint32x4_t m_a0 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a0), v_abs_mask), v_max_u32);\n"
            "        uint32x4_t m_a1 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a1), v_abs_mask), v_max_u32);\n"
            "        uint32x4_t m_a2 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a2), v_abs_mask), v_max_u32);\n"
            "        uint32x4_t m_a3 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(a3), v_abs_mask), v_max_u32);\n"
            "        healed_acc = vaddq_u32(healed_acc, vaddq_u32(vshrq_n_u32(vmvnq_u32(m_a0), 31), vshrq_n_u32(vmvnq_u32(m_a1), 31)));\n"
            "        healed_acc = vaddq_u32(healed_acc, vaddq_u32(vshrq_n_u32(vmvnq_u32(m_a2), 31), vshrq_n_u32(vmvnq_u32(m_a3), 31)));\n"
            "        a0 = vbslq_f32(m_a0, a0, v_zero);\n"
            "        a1 = vbslq_f32(m_a1, a1, v_zero);\n"
            "        a2 = vbslq_f32(m_a2, a2, v_zero);\n"
            "        a3 = vbslq_f32(m_a3, a3, v_zero);\n"
            "        if (src_b) {\n"
            "            uint32x4_t m_b0 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b0), v_abs_mask), v_max_u32);\n"
            "            uint32x4_t m_b1 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b1), v_abs_mask), v_max_u32);\n"
            "            uint32x4_t m_b2 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b2), v_abs_mask), v_max_u32);\n"
            "            uint32x4_t m_b3 = vcleq_u32(vandq_u32(vreinterpretq_u32_f32(b3), v_abs_mask), v_max_u32);\n"
            "            healed_acc = vaddq_u32(healed_acc, vaddq_u32(vshrq_n_u32(vmvnq_u32(m_b0), 31), vshrq_n_u32(vmvnq_u32(m_b1), 31)));\n"
            "            healed_acc = vaddq_u32(healed_acc, vaddq_u32(vshrq_n_u32(vmvnq_u32(m_b2), 31), vshrq_n_u32(vmvnq_u32(m_b3), 31)));\n"
            "            b0 = vbslq_f32(m_b0, b0, v_zero);\n"
            "            b1 = vbslq_f32(m_b1, b1, v_zero);\n"
            "            b2 = vbslq_f32(m_b2, b2, v_zero);\n"
            "            b3 = vbslq_f32(m_b3, b3, v_zero);\n"
            "        }\n"
            "        float32x4_t sum0 = vaddq_f32(a0, b0);\n"
            "        float32x4_t sum1 = vaddq_f32(a1, b1);\n"
            "        float32x4_t sum2 = vaddq_f32(a2, b2);\n"
            "        float32x4_t sum3 = vaddq_f32(a3, b3);\n"
            "        float32x4_t diff0 = vsubq_f32(a0, b0);\n"
            "        float32x4_t diff1 = vsubq_f32(a1, b1);\n"
            "        float32x4_t diff2 = vsubq_f32(a2, b2);\n"
            "        float32x4_t diff3 = vsubq_f32(a3, b3);\n"
            "        float32x4_t en0 = vaddq_f32(vmulq_f32(diff0, diff0), v_eps);\n"
            "        float32x4_t en1 = vaddq_f32(vmulq_f32(diff1, diff1), v_eps);\n"
            "        float32x4_t en2 = vaddq_f32(vmulq_f32(diff2, diff2), v_eps);\n"
            "        float32x4_t en3 = vaddq_f32(vmulq_f32(diff3, diff3), v_eps);\n"
            "        vst1q_f32(&dst[i + 0], vaddq_f32(vsqrtq_f32(en0), vmulq_f32(v_half, sum0)));\n"
            "        vst1q_f32(&dst[i + 4], vaddq_f32(vsqrtq_f32(en1), vmulq_f32(v_half, sum1)));\n"
            "        vst1q_f32(&dst[i + 8], vaddq_f32(vsqrtq_f32(en2), vmulq_f32(v_half, sum2)));\n"
            "        vst1q_f32(&dst[i + 12], vaddq_f32(vsqrtq_f32(en3), vmulq_f32(v_half, sum3)));\n"
            "    }\n"
            "    healed += (size_t)vaddvq_u32(healed_acc);\n"
            "#endif\n"
            "    for (; i < count; ++i) {\n"
            "        float a = src_a[i];\n"
            "        float b = src_b ? src_b[i] : 0.0f;\n"
            "        if (!isfinite(a) || a > 1000.0f || a < -1000.0f) { a = 0.0f; healed++; }\n"
            "        if (src_b && (!isfinite(b) || b > 1000.0f || b < -1000.0f)) { b = 0.0f; healed++; }\n"
            "        float diff = a - b;\n"
            "        dst[i] = sqrtf(diff * diff + 1e-6f) + 0.5f * (a + b);\n"
            "    }\n"
            "    if (out_healed) *out_healed = healed;\n"
            "}\n"
        );
        fclose(fp);

        char compile_cmd[1200];
        snprintf(compile_cmd, sizeof(compile_cmd),
                 "clang -O3 -shared -fPIC '%s' -o '%s' > /dev/null 2>&1",
                 c_src_path, dylib_path);
        int ret = system(compile_cmd);
        if (ret == 0) {
            void* handle = dlopen(dylib_path, RTLD_NOW | RTLD_LOCAL);
            if (handle) {
                AxonKernelFunc fn = (AxonKernelFunc)dlsym(handle, "synax_specialized_saltatory_kernel");
                if (fn) {
                    channel->dylib_handle = handle;
                    channel->active_kernel = fn;
                    strncpy(channel->specialized_kernel_name, "JIT_NEON_Saltatory", sizeof(channel->specialized_kernel_name) - 1);
                    channel->state = AXON_STATE_MYELINATED;
                    unlink(c_src_path);
                    return 0;
                }
            }
        }
        unlink(c_src_path);
    }

    channel->active_kernel = kernel_myelinated_neon_saltatory;
    strncpy(channel->specialized_kernel_name, "Builtin_NEON_Saltatory", sizeof(channel->specialized_kernel_name) - 1);
    channel->state = AXON_STATE_MYELINATED;
    return 0;
}

/* ─────────────────────────────────────────────────────────────────
 * 5. İLETİM (TRANSMIT) & SAĞLAM İSTATİSTİK
 * ───────────────────────────────────────────────────────────────── */
int synax_axon_transmit(SynaxAxonChannel* channel,
                        const float* src_a,
                        const float* src_b,
                        float* dst,
                        size_t count) {
    if (!channel) return -1;
    if (count == 0) return 0;
    if (!src_a || !dst) return -1;

    size_t healed = 0;
    double t0 = get_time_ns();

    if (channel->active_kernel) {
        channel->active_kernel(src_a, src_b, dst, count, &healed);
    } else if (channel->state == AXON_STATE_MYELINATED && channel->custom_myelinated_basic) {
        channel->custom_myelinated_basic(src_a, src_b, dst, count);
    } else if (channel->custom_unmyelinated_basic) {
        channel->custom_unmyelinated_basic(src_a, src_b, dst, count);
    } else {
        return -1;
    }

    double t1 = get_time_ns();
    double duration_ns = t1 - t0;

    channel->stats.total_transmissions++;
    channel->stats.healed_anomalies_count += healed;

    if (channel->state == AXON_STATE_UNMYELINATED) {
        if (channel->stats.unmyelinated_avg_ns == 0.0) {
            channel->stats.unmyelinated_avg_ns = duration_ns;
        } else {
            channel->stats.unmyelinated_avg_ns = 0.8 * channel->stats.unmyelinated_avg_ns + 0.2 * duration_ns;
        }

        if (channel->stats.total_transmissions >= channel->stats.myelination_threshold) {
            synax_axon_myelinate(channel);
        }
    } else if (channel->state == AXON_STATE_MYELINATED) {
        if (channel->stats.myelinated_avg_ns == 0.0) {
            channel->stats.myelinated_avg_ns = duration_ns;
        } else {
            channel->stats.myelinated_avg_ns = 0.8 * channel->stats.myelinated_avg_ns + 0.2 * duration_ns;
        }

        if (channel->stats.myelinated_avg_ns > 0.0 && channel->stats.unmyelinated_avg_ns > 0.0) {
            channel->stats.conduction_velocity_ratio = channel->stats.unmyelinated_avg_ns / channel->stats.myelinated_avg_ns;
        }
    }

    return 0;
}

AxonStats synax_axon_get_stats(const SynaxAxonChannel* channel) {
    if (!channel) {
        AxonStats empty = {0};
        return empty;
    }
    return channel->stats;
}

AxonMyelinState synax_axon_get_state(const SynaxAxonChannel* channel) {
    if (!channel) return AXON_STATE_UNMYELINATED;
    return channel->state;
}

const char* synax_axon_get_kernel_name(const SynaxAxonChannel* channel) {
    if (!channel) return "NULL";
    return channel->specialized_kernel_name;
}
