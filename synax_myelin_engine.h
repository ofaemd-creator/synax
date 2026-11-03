/**
 * SYNAX BIOLOGICAL MYELIN ENGINE (v1.0)
 * ==============================================================================
 * Genuine Biological Neuron & Myelin Architecture:
 *   1. Unmyelinated Axon (Continuous Conduction):
 *      - Cold-path, element-by-element execution, invariant discovery,
 *        frequency/variance profiling.
 *   2. Oligodendrocyte Plasticity Trigger:
 *      - Activity-dependent threshold (firing frequency & shape consistency).
 *      - Dynamic JIT compilation of specialized NEON SIMD Internode Kernels.
 *   3. Saltatory Conduction (Ranvier Nodes):
 *      - Rapid internode jump (L1 cache-aligned, zero branch overhead).
 *      - Ranvier Node boundary: Immune Shield regeneration (NaN/Inf healing).
 *      - Atomic function pointer hot-swap.
 * ==============================================================================
 */

#ifndef SYNAX_MYELIN_ENGINE_H
#define SYNAX_MYELIN_ENGINE_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    AXON_STATE_UNMYELINATED = 0, // Ham akson, yavaş iletim (sürekli iletim)
    AXON_STATE_MYELINATING   = 1, // Miyelinleşme tetiklendi (JIT derleme evresi)
    AXON_STATE_MYELINATED    = 2  // Miyelinli akson, sıçramalı iletim (Saltatory conduction)
} AxonMyelinState;

typedef struct {
    uint64_t total_transmissions;     // Toplam sinyal iletim sayısı
    uint64_t myelination_threshold;   // Miyelinleşme eşiği (örn. 25 tetikleme)
    double unmyelinated_avg_ns;       // Miyelinsiz ortalama iletim süresi (ns)
    double myelinated_avg_ns;         // Miyelinli ortalama iletim süresi (ns)
    double conduction_velocity_ratio; // İletim hızı artış katsayısı (saltatory speedup)
    size_t healed_anomalies_count;    // İyileştirilen biyomedikal anomali/gürültü sayısı
    size_t internode_block_size;      // Ranvier düğümleri arası blok büyüklüğü (float sayısı)
} AxonStats;

typedef void (*AxonKernelFunc)(const float* __restrict src_a,
                              const float* __restrict src_b,
                              float* __restrict dst,
                              size_t count,
                              size_t* out_healed);

typedef void (*AxonBasicKernelFunc)(const float* a,
                                    const float* b,
                                    float* out,
                                    size_t count);

typedef struct SynaxAxonChannel {
    char name[64];
    AxonMyelinState state;
    size_t fixed_length;
    AxonKernelFunc active_kernel;
    AxonStats stats;
    void* dylib_handle;
    void* ref_dylib_handle;
    AxonKernelFunc custom_unmyelinated_kernel;
    AxonKernelFunc custom_myelinated_kernel;
    AxonBasicKernelFunc custom_unmyelinated_basic;
    AxonBasicKernelFunc custom_myelinated_basic;
    char specialized_kernel_name[64];
} SynaxAxonChannel;

/* API */
SynaxAxonChannel* synax_axon_create(const char* name, size_t fixed_length, uint64_t myelin_threshold);
void synax_axon_destroy(SynaxAxonChannel* channel);

/* Bind synaxc-verified reference & optimized dylibs for function-pointer hot-swapping */
int synax_axon_bind_compiled_kernels(SynaxAxonChannel* channel,
                                     const char* ref_dylib_path,
                                     const char* myelinated_dylib_path,
                                     const char* kernel_label);

/* Ana sinyal iletim fonksiyonu (Action Potential Transmission) */
int synax_axon_transmit(SynaxAxonChannel* channel,
                        const float* src_a,
                        const float* src_b,
                        float* dst,
                        size_t count);

/* Manuel veya otonom miyelinleştirme tetikleyicisi */
int synax_axon_myelinate(SynaxAxonChannel* channel);

/* Durum ve istatistik sorgulama */
AxonStats synax_axon_get_stats(const SynaxAxonChannel* channel);
AxonMyelinState synax_axon_get_state(const SynaxAxonChannel* channel);
const char* synax_axon_get_kernel_name(const SynaxAxonChannel* channel);

#ifdef __cplusplus
}
#endif

#endif /* SYNAX_MYELIN_ENGINE_H */
