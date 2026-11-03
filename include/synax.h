/*
 * Copyright 2026 Dr. Ömer Faruk Aydın and SYNAX Project Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * MEDICAL RESEARCH DISCLAIMER:
 * SYNAX (.sx) and its runtime libraries are experimental academic and
 * computational research software. They are NOT certified clinical medical
 * devices (EU MDR 2017/745, U.S. FDA 21 CFR, IEC 60601-2-4) and must NEVER
 * be used for patient diagnosis, monitoring, defibrillation, or clinical care.
 */

/**
 * @file synax.h
 * @brief Official Public C99/C11 SDK Header for the SYNAX (.sx) Myelin Runtime.
 *
 * Provides stable ABI v1 bindings to `libsynax_myelin` (.dylib / .so),
 * enabling C, C++, Rust, and FFI consumers to create adaptive Axon channels,
 * bind differentially verified `synaxc` SIMD kernels, stream biomedical or
 * scientific `float32` signals with IEEE-754 Immune Shield protection, and
 * perform O(1) function-pointer hot-swaps (myelination).
 */

#ifndef SYNAX_PUBLIC_SDK_H
#define SYNAX_PUBLIC_SDK_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ──────────────────────────────────────────────────────────────────────────
 * Version & ABI Metadata
 * ────────────────────────────────────────────────────────────────────────── */
#define SYNAX_VERSION_MAJOR 0
#define SYNAX_VERSION_MINOR 5
#define SYNAX_VERSION_PATCH 0
#define SYNAX_VERSION_STRING "0.5.0"
#define SYNAX_ABI_VERSION 1

/* Portable restrict qualifier across C99, C11, and C++17 */
#if defined(__cplusplus)
#  if defined(__GNUC__) || defined(__clang__) || defined(_MSC_VER)
#    define SYNAX_RESTRICT __restrict
#  else
#    define SYNAX_RESTRICT
#  endif
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 199901L)
#  define SYNAX_RESTRICT restrict
#else
#  define SYNAX_RESTRICT
#endif

/* Shared library symbol visibility */
#if defined(_WIN32) || defined(__CYGWIN__)
#  if defined(SYNAX_BUILD_SHARED)
#    define SYNAX_API __declspec(dllexport)
#  else
#    define SYNAX_API
#  endif
#elif defined(__GNUC__) || defined(__clang__)
#  define SYNAX_API __attribute__((visibility("default")))
#else
#  define SYNAX_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ──────────────────────────────────────────────────────────────────────────
 * Compiled Kernel Function Pointer Signatures (`synaxc` ABI v1)
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * @brief Basic stateless kernel signature exported as `synax_kernel` by
 *        `synaxc`-compiled shared libraries.
 */
typedef void (*SynaxKernelFn)(const float* a,
                              const float* b,
                              float* out,
                              size_t count);

/**
 * @brief Anomaly-tracking kernel signature exported as `synax_kernel_tracked`
 *        by `synaxc`-compiled shared libraries and the Myelin runtime.
 *
 * Writes the exact count of non-finite or out-of-range inputs sanitized or
 * flagged by the IEEE-754 Immune Shield into `*out_healed` (when non-NULL).
 */
typedef void (*SynaxTrackedKernelFn)(const float* SYNAX_RESTRICT src_a,
                                     const float* SYNAX_RESTRICT src_b,
                                     float* SYNAX_RESTRICT dst,
                                     size_t count,
                                     size_t* out_healed);

/* Guard shared runtime types for drop-in coexistence with synax_myelin_engine.h */
#ifndef SYNAX_MYELIN_ENGINE_H
#define SYNAX_MYELIN_ENGINE_H

/**
 * @brief Conduction state of a `SynaxAxonChannel`.
 */
typedef enum {
    AXON_STATE_UNMYELINATED = 0, /**< Scalar continuous conduction (profiling / reference) */
    AXON_STATE_MYELINATING   = 1, /**< Active JIT compilation or kernel binding transition */
    AXON_STATE_MYELINATED    = 2  /**< Verified SIMD saltatory conduction (hot-swapped) */
} AxonMyelinState;

/**
 * @brief Telemetry and IEEE-754 Immune Shield statistics for an Axon channel.
 */
typedef struct {
    uint64_t total_transmissions;     /**< Total signal bursts transmitted */
    uint64_t myelination_threshold;   /**< Burst threshold triggering automatic myelination */
    double unmyelinated_avg_ns;       /**< Exponential moving average latency (ns) pre-myelination */
    double myelinated_avg_ns;         /**< Exponential moving average latency (ns) post-myelination */
    double conduction_velocity_ratio; /**< Observed saltatory speedup ratio (unmyelinated / myelinated) */
    size_t healed_anomalies_count;    /**< Cumulative NaN/Inf/range anomalies intercepted */
    size_t internode_block_size;      /**< Ranvier internode SIMD block width (in floats) */
} AxonStats;

typedef SynaxTrackedKernelFn AxonKernelFunc;
typedef SynaxKernelFn AxonBasicKernelFunc;

/**
 * @brief Adaptive Axon conduction channel state (`ABI v1` layout).
 *
 * Applications should treat fields as read-only and interact via the
 * `synax_axon_*` functions to preserve ABI invariants across versions.
 */
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

/* ──────────────────────────────────────────────────────────────────────────
 * Public Runtime API (`libsynax_myelin`)
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * @brief Allocate and initialize a new adaptive `SynaxAxonChannel`.
 *
 * @param name              Human-readable channel identifier (max 63 ASCII chars; NULL uses default).
 * @param fixed_length      Nominal float32 vector length per burst.
 * @param myelin_threshold  Number of bursts before automatic transition to myelinated execution
 *                          (0 defaults to 25).
 * @return Pointer to allocated channel, or `NULL` on allocation failure.
 */
SYNAX_API SynaxAxonChannel* synax_axon_create(const char* name,
                                              size_t fixed_length,
                                              uint64_t myelin_threshold);

/**
 * @brief Destroy a `SynaxAxonChannel`, closing bound dynamic libraries and freeing memory.
 *        Safe to pass `NULL`.
 */
SYNAX_API void synax_axon_destroy(SynaxAxonChannel* channel);

/**
 * @brief Bind `synaxc`-verified reference and optimized shared libraries to an Axon channel.
 *
 * Before myelination, `channel` executes `ref_dylib_path`. Upon reaching
 * `myelination_threshold` (or an explicit `synax_axon_myelinate` call), it performs
 * an O(1) function-pointer hot-swap to `myelinated_dylib_path`.
 *
 * @param channel                Target Axon channel.
 * @param ref_dylib_path         Path to reference C11 shared library (`.dylib` / `.so`).
 * @param myelinated_dylib_path  Path to 19-suite verified SIMD winner shared library.
 * @param kernel_label           Optional diagnostic label (e.g., `"v3_neon_4acc_prefetch"`).
 * @return `0` on success; negative error code (`-1` invalid args, `-2` ref `dlopen` failed,
 *         `-3` winner `dlopen` failed, `-4` missing `synax_kernel_tracked`/`synax_kernel` symbols).
 */
SYNAX_API int synax_axon_bind_compiled_kernels(SynaxAxonChannel* channel,
                                               const char* ref_dylib_path,
                                               const char* myelinated_dylib_path,
                                               const char* kernel_label);

/**
 * @brief Transmit a `float32` signal burst through the Axon channel.
 *
 * Automatically increments transmission telemetry, accumulates IEEE-754 anomaly counts,
 * and triggers `synax_axon_myelinate()` once `myelination_threshold` is reached.
 *
 * @param channel  Active Axon channel.
 * @param src_a    Primary input buffer (`count` floats, non-NULL when `count > 0`).
 * @param src_b    Secondary input buffer (`count` floats, or `NULL` to treat channel B as `0.0f`).
 * @param dst      Output buffer (`count` floats, non-NULL when `count > 0`).
 * @param count    Number of `float` elements to process.
 * @return `0` on success, `-1` on invalid arguments.
 */
SYNAX_API int synax_axon_transmit(SynaxAxonChannel* channel,
                                  const float* src_a,
                                  const float* src_b,
                                  float* dst,
                                  size_t count);

/**
 * @brief Manually trigger myelination (SIMD hot-swap or JIT specialization) on `channel`.
 *
 * @return `0` on success (or if already myelinated), `-1` if `channel` is `NULL`.
 */
SYNAX_API int synax_axon_myelinate(SynaxAxonChannel* channel);

/**
 * @brief Retrieve a snapshot of conduction timing and anomaly-healing telemetry.
 */
SYNAX_API AxonStats synax_axon_get_stats(const SynaxAxonChannel* channel);

/**
 * @brief Query the current myelination state of `channel`.
 */
SYNAX_API AxonMyelinState synax_axon_get_state(const SynaxAxonChannel* channel);

/**
 * @brief Return the active or bound specialized kernel identifier string.
 */
SYNAX_API const char* synax_axon_get_kernel_name(const SynaxAxonChannel* channel);

#endif /* SYNAX_MYELIN_ENGINE_H */

#ifdef __cplusplus
}
#endif

#endif /* SYNAX_PUBLIC_SDK_H */
