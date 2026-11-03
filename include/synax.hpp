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
 * @file synax.hpp
 * @brief Modern C++17 Header-Only RAII Wrapper for the SYNAX (.sx) Myelin Runtime.
 */

#ifndef SYNAX_PUBLIC_SDK_HPP
#define SYNAX_PUBLIC_SDK_HPP

#include "synax.h"

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace synax {

/**
 * @brief Exception thrown on SYNAX channel creation, kernel binding, or transmission errors.
 */
class Error : public std::runtime_error {
public:
    explicit Error(const std::string& message, int code = -1)
        : std::runtime_error(message), code_(code) {}

    [[nodiscard]] int code() const noexcept { return code_; }

private:
    int code_;
};

/**
 * @brief Move-only RAII C++17 handle managing a native `SynaxAxonChannel`.
 *
 * Enforces deterministic resource cleanup (`synax_axon_destroy` on scope exit),
 * input vector shape parity (`a.size() == b.size()`), and checked error handling.
 */
class AxonChannel {
public:
    /**
     * @brief Construct a new adaptive Axon channel.
     *
     * @param name              Channel name (truncated to 63 bytes in C ABI).
     * @param fixed_length      Nominal vector size per transmission burst.
     * @param myelin_threshold  Number of bursts before automatic SIMD myelination (default 25).
     * @throws synax::Error     If native channel allocation fails.
     */
    explicit AxonChannel(const std::string& name,
                         std::size_t fixed_length,
                         std::uint64_t myelin_threshold = 25)
        : handle_(::synax_axon_create(name.c_str(), fixed_length, myelin_threshold)) {
        if (!handle_) {
            throw Error("synax_axon_create failed to allocate SynaxAxonChannel", -1);
        }
    }

    ~AxonChannel() noexcept {
        if (handle_) {
            ::synax_axon_destroy(handle_);
            handle_ = nullptr;
        }
    }

    /* Non-copyable */
    AxonChannel(const AxonChannel&) = delete;
    AxonChannel& operator=(const AxonChannel&) = delete;

    /* Move-constructible & move-assignable */
    AxonChannel(AxonChannel&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)) {}

    AxonChannel& operator=(AxonChannel&& other) noexcept {
        if (this != &other) {
            if (handle_) {
                ::synax_axon_destroy(handle_);
            }
            handle_ = std::exchange(other.handle_, nullptr);
        }
        return *this;
    }

    /**
     * @brief Bind `synaxc`-verified reference and SIMD winner shared libraries.
     */
    void bind_compiled_kernels(const std::string& ref_dylib_path,
                               const std::string& myelinated_dylib_path,
                               const std::string& kernel_label = "") {
        ensure_valid();
        const int rc = ::synax_axon_bind_compiled_kernels(
            handle_,
            ref_dylib_path.c_str(),
            myelinated_dylib_path.c_str(),
            kernel_label.empty() ? nullptr : kernel_label.c_str()
        );
        if (rc != 0) {
            throw Error(
                "synax_axon_bind_compiled_kernels failed with error code " + std::to_string(rc),
                rc
            );
        }
    }

    /**
     * @brief Transmit dual-channel `float` vectors (`a` and `b`) through the Axon channel.
     *
     * @throws std::invalid_argument If `a.size() != b.size()`.
     * @throws synax::Error          If native transmission fails.
     */
    [[nodiscard]] std::vector<float> transmit(const std::vector<float>& a,
                                              const std::vector<float>& b) {
        ensure_valid();
        if (a.size() != b.size()) {
            throw std::invalid_argument(
                "synax::AxonChannel::transmit length mismatch: a.size() (" +
                std::to_string(a.size()) + ") != b.size() (" +
                std::to_string(b.size()) + ")"
            );
        }
        std::vector<float> out(a.size(), 0.0f);
        if (a.empty()) {
            return out;
        }
        const int rc = ::synax_axon_transmit(handle_, a.data(), b.data(), out.data(), a.size());
        if (rc != 0) {
            throw Error("synax_axon_transmit failed with error code " + std::to_string(rc), rc);
        }
        return out;
    }

    /**
     * @brief Zero-allocation buffer transmission overload for pre-allocated buffers.
     */
    void transmit_into(const float* src_a,
                       const float* src_b,
                       float* dst,
                       std::size_t count) {
        ensure_valid();
        if (count == 0) {
            return;
        }
        const int rc = ::synax_axon_transmit(handle_, src_a, src_b, dst, count);
        if (rc != 0) {
            throw Error("synax_axon_transmit failed with error code " + std::to_string(rc), rc);
        }
    }

    /**
     * @brief Explicitly trigger myelination (function-pointer hot-swap / SIMD JIT).
     */
    void myelinate() {
        ensure_valid();
        const int rc = ::synax_axon_myelinate(handle_);
        if (rc != 0) {
            throw Error("synax_axon_myelinate failed with error code " + std::to_string(rc), rc);
        }
    }

    /**
     * @brief Return current telemetry and IEEE-754 anomaly-healing statistics.
     */
    [[nodiscard]] ::AxonStats stats() const {
        ensure_valid();
        return ::synax_axon_get_stats(handle_);
    }

    /**
     * @brief Return current myelination state (`AXON_STATE_UNMYELINATED`, etc.).
     */
    [[nodiscard]] ::AxonMyelinState state() const {
        ensure_valid();
        return ::synax_axon_get_state(handle_);
    }

    /**
     * @brief Return active or bound specialized kernel name.
     */
    [[nodiscard]] std::string kernel_name() const {
        ensure_valid();
        const char* raw_name = ::synax_axon_get_kernel_name(handle_);
        return raw_name ? std::string(raw_name) : std::string();
    }

    /**
     * @brief Access underlying C pointer (null if moved-from).
     */
    [[nodiscard]] ::SynaxAxonChannel* raw() noexcept { return handle_; }
    [[nodiscard]] const ::SynaxAxonChannel* raw() const noexcept { return handle_; }

private:
    void ensure_valid() const {
        if (!handle_) {
            throw Error("Attempted to use a moved-from synax::AxonChannel", -1);
        }
    }

    ::SynaxAxonChannel* handle_{nullptr};
};

} // namespace synax

#endif /* SYNAX_PUBLIC_SDK_HPP */
