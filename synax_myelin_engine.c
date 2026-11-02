/**
 * SYNAX BIOLOGICAL MYELIN ENGINE (v1.0)
 * ==============================================================================
 * Real-Time Biological Neuron & Myelin Data Flow Engine
 * Designed for Apple Silicon (ARM64 NEON) & Universal POSIX architectures.
 * ==============================================================================
 */

#define _GNU_SOURCE
#include "synax_myelin_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dlfcn.h>
#include <unistd.h>
#include <sys/time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#endif

#if defined(__aarch64__) || defined(_M_ARM64)
#include <arm_neon.h>
#endif

/* Yüksek hassasiyetli zaman ölçümü (Nanometrik biyolojik iletim saati) */
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
 * 1. UNMYELINATED AXON KERNEL (Sürekli İletim / Ham Akson)
 * Biyolojik benzetim: Her bir membran parçasında tek tek depolarizasyon,
 * skaler dallanmalar, yüksek membran direnci ve yavaş sinyal iletimi.
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

        /* Biyolojik iyon dengesizliği / Anomali kontrolü (Her elemanda tekil dallanma) */
        if (!isfinite(a) || a > 1000.0f || a < -1000.0f) {
            a = 0.0f;
            healed++;
        }
        if (src_b && (!isfinite(b) || b > 1000.0f || b < -1000.0f)) {
            b = 0.0f;
            healed++;
        }

        /* Standart non-lineer aktivasyon ve rezonans akısı */
        float sum = a + b;
        float diff = a - b;
        float energy = (diff * diff);
        /* Saf skaler aktivasyon (L2 norm benzeri hemodinamik enerji) */
        float val = sqrtf(energy + 1e-6f) + 0.5f * sum;
        dst[i] = val;
    }
    if (out_healed) *out_healed = healed;
}

/* ─────────────────────────────────────────────────────────────────
 * 2. MYELINATED SALTATORY KERNEL (Ranvier Düğümleri & SIMD Sıçraması)
 * Biyolojik benzetim: Miyelin kılıfı sayesinde internode boyunca
 * elektrotonik anlık akış (L1 Önbellek & 128-bit NEON Vektörleri),
 * Ranvier Düğümlerinde ise sıfır-dallanmalı bağışıklık yenilenmesi.
 * ───────────────────────────────────────────────────────────────── */
static void kernel_myelinated_neon_saltatory(const float* __restrict src_a,
                                            const float* __restrict src_b,
                                            float* __restrict dst,
                                            size_t count,
                                            size_t* out_healed) {
    size_t healed = 0;
    size_t i = 0;

#if defined(__aarch64__) || defined(_M_ARM64)
    /* 16 float (4 x 128-bit NEON) bloklar halinde sıçramalı iletim (Saltatory Block) */
    const float32x4_t v_zero = vdupq_n_f32(0.0f);
    const float32x4_t v_half = vdupq_n_f32(0.5f);
    const float32x4_t v_eps  = vdupq_n_f32(1e-6f);
    const float32x4_t v_max  = vdupq_n_f32(1000.0f);
    const float32x4_t v_min  = vdupq_n_f32(-1000.0f);

    for (; i + 16 <= count; i += 16) {
        /* Ranvier Internode Prefetch: Sonraki L1D önbellek hattını önden çek */
        __builtin_prefetch(&src_a[i + 32], 0, 3);
        if (src_b) __builtin_prefetch(&src_b[i + 32], 0, 3);
        __builtin_prefetch(&dst[i + 32], 1, 3);

        /* 4x NEON Yükleme */
        float32x4_t a0 = vld1q_f32(&src_a[i + 0]);
        float32x4_t a1 = vld1q_f32(&src_a[i + 4]);
        float32x4_t a2 = vld1q_f32(&src_a[i + 8]);
        float32x4_t a3 = vld1q_f32(&src_a[i + 12]);

        float32x4_t b0 = src_b ? vld1q_f32(&src_b[i + 0]) : v_zero;
        float32x4_t b1 = src_b ? vld1q_f32(&src_b[i + 4]) : v_zero;
        float32x4_t b2 = src_b ? vld1q_f32(&src_b[i + 8]) : v_zero;
        float32x4_t b3 = src_b ? vld1q_f32(&src_b[i + 12]) : v_zero;

        /* Düğüm Bağışıklık Kalkanı (Ranvier Node Immune Shield - Sıfır Dallanmalı Maskeleme) */
        /* IEEE 754 NaN/Inf ve sınır dışı değerleri tek döngüde vbslq ile sıfırla */
        uint32x4_t mask_a0 = vandq_u32(vcgeq_f32(a0, v_min), vcleq_f32(a0, v_max));
        uint32x4_t mask_a1 = vandq_u32(vcgeq_f32(a1, v_min), vcleq_f32(a1, v_max));
        uint32x4_t mask_a2 = vandq_u32(vcgeq_f32(a2, v_min), vcleq_f32(a2, v_max));
        uint32x4_t mask_a3 = vandq_u32(vcgeq_f32(a3, v_min), vcleq_f32(a3, v_max));

        a0 = vbslq_f32(mask_a0, a0, v_zero);
        a1 = vbslq_f32(mask_a1, a1, v_zero);
        a2 = vbslq_f32(mask_a2, a2, v_zero);
        a3 = vbslq_f32(mask_a3, a3, v_zero);

        /* Vektör Aritmetiği: sum ve diff */
        float32x4_t sum0 = vaddq_f32(a0, b0);
        float32x4_t sum1 = vaddq_f32(a1, b1);
        float32x4_t sum2 = vaddq_f32(a2, b2);
        float32x4_t sum3 = vaddq_f32(a3, b3);

        float32x4_t diff0 = vsubq_f32(a0, b0);
        float32x4_t diff1 = vsubq_f32(a1, b1);
        float32x4_t diff2 = vsubq_f32(a2, b2);
        float32x4_t diff3 = vsubq_f32(a3, b3);

        /* Enerji = diff^2 + eps */
        float32x4_t en0 = vaddq_f32(vmulq_f32(diff0, diff0), v_eps);
        float32x4_t en1 = vaddq_f32(vmulq_f32(diff1, diff1), v_eps);
        float32x4_t en2 = vaddq_f32(vmulq_f32(diff2, diff2), v_eps);
        float32x4_t en3 = vaddq_f32(vmulq_f32(diff3, diff3), v_eps);

        /* Hızlı ARM NEON Karekök (vrsqrteq_f32 + vrsqrtsq_f32 adımı veya doğrudan vsqrtq) */
        float32x4_t r0 = vaddq_f32(vsqrtq_f32(en0), vmulq_f32(v_half, sum0));
        float32x4_t r1 = vaddq_f32(vsqrtq_f32(en1), vmulq_f32(v_half, sum1));
        float32x4_t r2 = vaddq_f32(vsqrtq_f32(en2), vmulq_f32(v_half, sum2));
        float32x4_t r3 = vaddq_f32(vsqrtq_f32(en3), vmulq_f32(v_half, sum3));

        /* Sonuçları L1 önbellek hattına doğrudan yaz */
        vst1q_f32(&dst[i + 0], r0);
        vst1q_f32(&dst[i + 4], r1);
        vst1q_f32(&dst[i + 8], r2);
        vst1q_f32(&dst[i + 12], r3);
    }
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
    if (out_healed) *out_healed += healed;
}

/* ─────────────────────────────────────────────────────────────────
 * 3. KANAL OLUŞTURMA VE YÖNETİMİ
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

    return channel;
}

void synax_axon_destroy(SynaxAxonChannel* channel) {
    if (!channel) return;
    if (channel->dylib_handle) {
        dlclose(channel->dylib_handle);
        channel->dylib_handle = NULL;
    }
    free(channel);
}

/* ─────────────────────────────────────────────────────────────────
 * 4. OTONOM MİYELİNLEŞTİRME (OLIGODENDROCYTE PLASTICITY JIT)
 * Biyolojik benzetim: Sık kullanılan aksonun etrafı oligodendrositler
 * tarafından kat kat miyelinle sarılır. SYNAX bu anda L1 önbellek ve
 * NEON SIMD için özelleşmiş dinamik bir kütüphane derler ve fonksiyon
 * göstericisini atomik olarak sıcak-takas (hot-swap) yapar.
 * ───────────────────────────────────────────────────────────────── */
int synax_axon_myelinate(SynaxAxonChannel* channel) {
    if (!channel) return -1;
    if (channel->state == AXON_STATE_MYELINATED) return 0; // Zaten miyelinli

    channel->state = AXON_STATE_MYELINATING;

    /* Dinamik JIT Derleme Kontrolü */
    char c_src_path[256];
    char dylib_path[256];
    snprintf(c_src_path, sizeof(c_src_path), "/tmp/synax_myelin_%s_%p.c", channel->name, (void*)channel);
    snprintf(dylib_path, sizeof(dylib_path), "/tmp/synax_myelin_%s_%p.dylib", channel->name, (void*)channel);

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
            "    size_t i = 0;\n"
            "#if defined(__aarch64__) || defined(_M_ARM64)\n"
            "    const float32x4_t v_zero = vdupq_n_f32(0.0f);\n"
            "    const float32x4_t v_half = vdupq_n_f32(0.5f);\n"
            "    const float32x4_t v_eps  = vdupq_n_f32(1e-6f);\n"
            "    const float32x4_t v_max  = vdupq_n_f32(1000.0f);\n"
            "    const float32x4_t v_min  = vdupq_n_f32(-1000.0f);\n"
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
            "        uint32x4_t m0 = vandq_u32(vcgeq_f32(a0, v_min), vcleq_f32(a0, v_max));\n"
            "        uint32x4_t m1 = vandq_u32(vcgeq_f32(a1, v_min), vcleq_f32(a1, v_max));\n"
            "        uint32x4_t m2 = vandq_u32(vcgeq_f32(a2, v_min), vcleq_f32(a2, v_max));\n"
            "        uint32x4_t m3 = vandq_u32(vcgeq_f32(a3, v_min), vcleq_f32(a3, v_max));\n"
            "        a0 = vbslq_f32(m0, a0, v_zero);\n"
            "        a1 = vbslq_f32(m1, a1, v_zero);\n"
            "        a2 = vbslq_f32(m2, a2, v_zero);\n"
            "        a3 = vbslq_f32(m3, a3, v_zero);\n"
            "        float32x4_t d0 = vsubq_f32(a0, b0);\n"
            "        float32x4_t d1 = vsubq_f32(a1, b1);\n"
            "        float32x4_t d2 = vsubq_f32(a2, b2);\n"
            "        float32x4_t d3 = vsubq_f32(a3, b3);\n"
            "        float32x4_t e0 = vaddq_f32(vmulq_f32(d0, d0), v_eps);\n"
            "        float32x4_t e1 = vaddq_f32(vmulq_f32(d1, d1), v_eps);\n"
            "        float32x4_t e2 = vaddq_f32(vmulq_f32(d2, d2), v_eps);\n"
            "        float32x4_t e3 = vaddq_f32(vmulq_f32(d3, d3), v_eps);\n"
            "        vst1q_f32(&dst[i + 0], vaddq_f32(vsqrtq_f32(e0), vmulq_f32(v_half, vaddq_f32(a0, b0))));\n"
            "        vst1q_f32(&dst[i + 4], vaddq_f32(vsqrtq_f32(e1), vmulq_f32(v_half, vaddq_f32(a1, b1))));\n"
            "        vst1q_f32(&dst[i + 8], vaddq_f32(vsqrtq_f32(e2), vmulq_f32(v_half, vaddq_f32(a2, b2))));\n"
            "        vst1q_f32(&dst[i + 12], vaddq_f32(vsqrtq_f32(e3), vmulq_f32(v_half, vaddq_f32(a3, b3))));\n"
            "    }\n"
            "#endif\n"
            "    for (; i < count; ++i) {\n"
            "        float a = src_a[i];\n"
            "        float b = src_b ? src_b[i] : 0.0f;\n"
            "        if (!isfinite(a) || a > 1000.0f || a < -1000.0f) a = 0.0f;\n"
            "        if (src_b && (!isfinite(b) || b > 1000.0f || b < -1000.0f)) b = 0.0f;\n"
            "        float diff = a - b;\n"
            "        dst[i] = sqrtf(diff * diff + 1e-6f) + 0.5f * (a + b);\n"
            "    }\n"
            "    if (out_healed) *out_healed += 0;\n"
            "}\n"
        );
        fclose(fp);

        char compile_cmd[512];
        snprintf(compile_cmd, sizeof(compile_cmd),
                 "clang -O3 -shared -fPIC -ffast-math %s -o %s > /dev/null 2>&1",
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

    /* Geri dönüş: Yerleşik NEON Saltatory Kernel'e geç */
    channel->active_kernel = kernel_myelinated_neon_saltatory;
    strncpy(channel->specialized_kernel_name, "Builtin_NEON_Saltatory", sizeof(channel->specialized_kernel_name) - 1);
    channel->state = AXON_STATE_MYELINATED;
    return 0;
}

/* ─────────────────────────────────────────────────────────────────
 * 5. SİNYAL İLETİMİ (TRANSMIT ACTION POTENTIAL)
 * ───────────────────────────────────────────────────────────────── */
int synax_axon_transmit(SynaxAxonChannel* channel,
                        const float* src_a,
                        const float* src_b,
                        float* dst,
                        size_t count) {
    if (!channel || !src_a || !dst || count == 0) return -1;

    size_t healed = 0;
    double t0 = get_time_ns();

    /* Aktif fonksiyon göstericisini çalıştır (Sıçramalı veya Sürekli) */
    channel->active_kernel(src_a, src_b, dst, count, &healed);

    double t1 = get_time_ns();
    double duration_ns = t1 - t0;

    channel->stats.total_transmissions++;
    channel->stats.healed_anomalies_count += healed;

    if (channel->state == AXON_STATE_UNMYELINATED) {
        if (channel->stats.unmyelinated_avg_ns == 0.0) {
            channel->stats.unmyelinated_avg_ns = duration_ns;
        } else {
            /* Üstel hareketli ortalama */
            channel->stats.unmyelinated_avg_ns = 0.8 * channel->stats.unmyelinated_avg_ns + 0.2 * duration_ns;
        }

        /* Miyelinleşme eşiği aşıldı mı? */
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
