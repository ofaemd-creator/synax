// Copyright 2026 Dr. Ömer Faruk Aydın and SYNAX Project Contributors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// MEDICAL RESEARCH DISCLAIMER:
// SYNAX (.sx) and `synax-rs` are strictly experimental academic and
// computational research software. They are NOT certified clinical medical
// devices (EU MDR 2017/745, U.S. FDA 21 CFR, IEC 60601-2-4) and must NEVER
// be used to direct patient care, diagnosis, or defibrillation.

//! # `synax-rs` — Safe Rust Bindings for the SYNAX (`.sx`) Myelin Runtime
//!
//! Provides both raw C ABI declarations (`libsynax_myelin`) and an idiomatic,
//! memory-safe RAII wrapper [`AxonChannel`] enforcing slice length invariants
//! (`a.len() == b.len()`), deterministic `Drop` cleanup, and IEEE-754 Immune
//! Shield telemetry inspection.

use std::error::Error;
use std::ffi::{CStr, CString, NulError};
use std::fmt;
use std::marker::{PhantomData, PhantomPinned};
use std::os::raw::{c_char, c_int};
use std::path::Path;
use std::ptr::{self, NonNull};

/// Public SDK major version matching `SYNAX_VERSION_MAJOR` in `include/synax.h`.
pub const SYNAX_VERSION_MAJOR: u32 = 0;
/// Public SDK minor version matching `SYNAX_VERSION_MINOR` in `include/synax.h`.
pub const SYNAX_VERSION_MINOR: u32 = 5;
/// Native C ABI version matching `SYNAX_ABI_VERSION` in `include/synax.h`.
pub const SYNAX_ABI_VERSION: u32 = 1;

/// Conduction state of an [`AxonChannel`], matching C `AxonMyelinState`.
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AxonMyelinState {
    /// Continuous scalar reference execution (profiling / cold path).
    Unmyelinated = 0,
    /// Active JIT synthesis or kernel binding transition.
    Myelinating = 1,
    /// Verified SIMD saltatory execution (O(1) function-pointer hot-swapped).
    Myelinated = 2,
}

impl AxonMyelinState {
    #[inline]
    fn from_raw(raw: c_int) -> Self {
        match raw {
            1 => Self::Myelinating,
            2 => Self::Myelinated,
            _ => Self::Unmyelinated,
        }
    }
}

/// Telemetry and IEEE-754 Immune Shield metrics matching C `AxonStats`.
#[repr(C)]
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct AxonStats {
    /// Total signal bursts transmitted across this channel.
    pub total_transmissions: u64,
    /// Burst count threshold triggering automatic myelination.
    pub myelination_threshold: u64,
    /// Exponential moving average latency (ns) in unmyelinated scalar mode.
    pub unmyelinated_avg_ns: f64,
    /// Exponential moving average latency (ns) in myelinated SIMD mode.
    pub myelinated_avg_ns: f64,
    /// Observed saltatory speedup ratio (`unmyelinated_avg_ns / myelinated_avg_ns`).
    pub conduction_velocity_ratio: f64,
    /// Cumulative `NaN`, `±Inf`, or range-violating inputs sanitized by the Immune Shield.
    pub healed_anomalies_count: usize,
    /// Ranvier internode SIMD block width (in `f32` elements).
    pub internode_block_size: usize,
}

/// Opaque FFI handle representing C `struct SynaxAxonChannel`.
#[repr(C)]
pub struct SynaxAxonChannel {
    _private: [u8; 0],
    _marker: PhantomData<(*mut u8, PhantomPinned)>,
}

/// Raw `extern "C"` bindings to `libsynax_myelin`.
pub mod ffi {
    use super::{c_char, c_int, AxonStats, SynaxAxonChannel};

    extern "C" {
        pub fn synax_axon_create(
            name: *const c_char,
            fixed_length: usize,
            myelin_threshold: u64,
        ) -> *mut SynaxAxonChannel;

        pub fn synax_axon_destroy(channel: *mut SynaxAxonChannel);

        pub fn synax_axon_bind_compiled_kernels(
            channel: *mut SynaxAxonChannel,
            ref_dylib_path: *const c_char,
            myelinated_dylib_path: *const c_char,
            kernel_label: *const c_char,
        ) -> c_int;

        pub fn synax_axon_transmit(
            channel: *mut SynaxAxonChannel,
            src_a: *const f32,
            src_b: *const f32,
            dst: *mut f32,
            count: usize,
        ) -> c_int;

        pub fn synax_axon_myelinate(channel: *mut SynaxAxonChannel) -> c_int;

        pub fn synax_axon_get_stats(channel: *const SynaxAxonChannel) -> AxonStats;

        pub fn synax_axon_get_state(channel: *const SynaxAxonChannel) -> c_int;

        pub fn synax_axon_get_kernel_name(channel: *const SynaxAxonChannel) -> *const c_char;
    }
}

pub use ffi::{
    synax_axon_bind_compiled_kernels, synax_axon_create, synax_axon_destroy,
    synax_axon_get_kernel_name, synax_axon_get_state, synax_axon_get_stats, synax_axon_myelinate,
    synax_axon_transmit,
};

/// Errors returned by safe [`AxonChannel`] operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SynaxError {
    /// Provided string or filesystem path contained an interior NUL byte.
    InteriorNul(NulError),
    /// Path could not be represented as valid UTF-8 for C `dlopen`.
    InvalidPathEncoding,
    /// Native `synax_axon_create` returned a null pointer.
    AllocationFailed,
    /// Input slice lengths did not match (`a.len() != b.len()`), or destination length differed.
    LengthMismatch { expected: usize, actual: usize },
    /// `synax_axon_bind_compiled_kernels` returned a non-zero error code.
    BindKernelsFailed(i32),
    /// `synax_axon_transmit` returned a non-zero error code.
    TransmissionFailed(i32),
    /// `synax_axon_myelinate` returned a non-zero error code.
    MyelinationFailed(i32),
}

impl fmt::Display for SynaxError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InteriorNul(err) => write!(f, "interior NUL byte in C string parameter: {err}"),
            Self::InvalidPathEncoding => write!(f, "dylib path is not valid UTF-8"),
            Self::AllocationFailed => write!(f, "synax_axon_create failed to allocate channel"),
            Self::LengthMismatch { expected, actual } => write!(
                f,
                "slice length mismatch: expected {expected} elements, got {actual}"
            ),
            Self::BindKernelsFailed(code) => {
                write!(f, "synax_axon_bind_compiled_kernels failed (code {code})")
            }
            Self::TransmissionFailed(code) => {
                write!(f, "synax_axon_transmit failed (code {code})")
            }
            Self::MyelinationFailed(code) => {
                write!(f, "synax_axon_myelinate failed (code {code})")
            }
        }
    }
}

impl Error for SynaxError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::InteriorNul(err) => Some(err),
            _ => None,
        }
    }
}

impl From<NulError> for SynaxError {
    fn from(err: NulError) -> Self {
        Self::InteriorNul(err)
    }
}

/// Safe, move-only RAII wrapper around a native `SynaxAxonChannel`.
pub struct AxonChannel {
    ptr: NonNull<SynaxAxonChannel>,
}

// SAFETY: Each `SynaxAxonChannel` owns an isolated heap allocation and private dylib handles;
// moving ownership across threads is safe when synchronized via `&mut self` for mutation.
unsafe impl Send for AxonChannel {}

impl AxonChannel {
    /// Allocate and initialize a new adaptive `AxonChannel`.
    ///
    /// Passing `myelin_threshold == 0` uses the native default threshold (`25`).
    pub fn new(
        name: &str,
        fixed_length: usize,
        myelin_threshold: u64,
    ) -> Result<Self, SynaxError> {
        let c_name = CString::new(name)?;
        // SAFETY: `c_name` is a valid NUL-terminated string for the duration of the call.
        let raw = unsafe { synax_axon_create(c_name.as_ptr(), fixed_length, myelin_threshold) };
        let ptr = NonNull::new(raw).ok_or(SynaxError::AllocationFailed)?;
        Ok(Self { ptr })
    }

    /// Bind `synaxc`-verified reference and myelinated SIMD shared libraries for hot-swapping.
    pub fn bind_compiled_kernels(
        &mut self,
        ref_dylib_path: &Path,
        myelinated_dylib_path: &Path,
        kernel_label: Option<&str>,
    ) -> Result<(), SynaxError> {
        let ref_str = ref_dylib_path
            .to_str()
            .ok_or(SynaxError::InvalidPathEncoding)?;
        let opt_str = myelinated_dylib_path
            .to_str()
            .ok_or(SynaxError::InvalidPathEncoding)?;

        let c_ref = CString::new(ref_str)?;
        let c_opt = CString::new(opt_str)?;
        let c_label = match kernel_label {
            Some(lbl) if !lbl.is_empty() => Some(CString::new(lbl)?),
            _ => None,
        };

        let label_ptr = c_label.as_ref().map_or(ptr::null(), |s| s.as_ptr());

        // SAFETY: `self.ptr` is valid and uniquely borrowed via `&mut self`; all CStrings are alive.
        let rc = unsafe {
            synax_axon_bind_compiled_kernels(
                self.ptr.as_ptr(),
                c_ref.as_ptr(),
                c_opt.as_ptr(),
                label_ptr,
            )
        };
        if rc != 0 {
            return Err(SynaxError::BindKernelsFailed(rc));
        }
        Ok(())
    }

    /// Transmit dual-channel `f32` slices (`a` and `b`) and return the computed output `Vec<f32>`.
    ///
    /// Enforces `a.len() == b.len()` prior to invoking the C SIMD/scalar kernel.
    pub fn transmit(&mut self, a: &[f32], b: &[f32]) -> Result<Vec<f32>, SynaxError> {
        if a.len() != b.len() {
            return Err(SynaxError::LengthMismatch {
                expected: a.len(),
                actual: b.len(),
            });
        }
        let mut dst = vec![0.0_f32; a.len()];
        self.transmit_into(a, b, &mut dst)?;
        Ok(dst)
    }

    /// Zero-allocation dual-channel transmission into a caller-supplied output slice `dst`.
    ///
    /// Enforces `a.len() == b.len()` and `dst.len() == a.len()`.
    pub fn transmit_into(
        &mut self,
        a: &[f32],
        b: &[f32],
        dst: &mut [f32],
    ) -> Result<(), SynaxError> {
        if a.len() != b.len() {
            return Err(SynaxError::LengthMismatch {
                expected: a.len(),
                actual: b.len(),
            });
        }
        if dst.len() != a.len() {
            return Err(SynaxError::LengthMismatch {
                expected: a.len(),
                actual: dst.len(),
            });
        }
        if a.is_empty() {
            return Ok(());
        }

        // SAFETY: `a`, `b`, and `dst` all have length `a.len() > 0`, valid aligned pointers,
        // and `dst` does not alias `a` or `b` thanks to Rust's `&mut [f32]` borrow rules.
        let rc = unsafe {
            synax_axon_transmit(
                self.ptr.as_ptr(),
                a.as_ptr(),
                b.as_ptr(),
                dst.as_mut_ptr(),
                a.len(),
            )
        };
        if rc != 0 {
            return Err(SynaxError::TransmissionFailed(rc));
        }
        Ok(())
    }

    /// Manually trigger myelination (function-pointer hot-swap / SIMD specialization).
    pub fn myelinate(&mut self) -> Result<(), SynaxError> {
        // SAFETY: `self.ptr` is valid and uniquely borrowed.
        let rc = unsafe { synax_axon_myelinate(self.ptr.as_ptr()) };
        if rc != 0 {
            return Err(SynaxError::MyelinationFailed(rc));
        }
        Ok(())
    }

    /// Retrieve a snapshot of conduction velocity and Immune Shield statistics.
    #[must_use]
    pub fn stats(&self) -> AxonStats {
        // SAFETY: `self.ptr` is valid for shared read-only inspection.
        unsafe { synax_axon_get_stats(self.ptr.as_ptr()) }
    }

    /// Query the current [`AxonMyelinState`] of the channel.
    #[must_use]
    pub fn state(&self) -> AxonMyelinState {
        // SAFETY: `self.ptr` is valid for shared read-only inspection.
        let raw = unsafe { synax_axon_get_state(self.ptr.as_ptr()) };
        AxonMyelinState::from_raw(raw)
    }

    /// Return the active or bound specialized kernel identifier.
    #[must_use]
    pub fn kernel_name(&self) -> String {
        // SAFETY: `synax_axon_get_kernel_name` returns a NUL-terminated buffer owned by the channel.
        unsafe {
            let ptr = synax_axon_get_kernel_name(self.ptr.as_ptr());
            if ptr.is_null() {
                String::new()
            } else {
                CStr::from_ptr(ptr).to_string_lossy().into_owned()
            }
        }
    }

    /// Return the underlying raw C channel pointer.
    #[must_use]
    pub fn as_raw_ptr(&self) -> *mut SynaxAxonChannel {
        self.ptr.as_ptr()
    }
}

impl Drop for AxonChannel {
    fn drop(&mut self) {
        // SAFETY: `self.ptr` was allocated by `synax_axon_create` and is destroyed exactly once.
        unsafe {
            synax_axon_destroy(self.ptr.as_ptr());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_mismatched_slice_lengths() {
        let mut ch = AxonChannel::new("rust_len_check", 64, 4).expect("channel alloc");
        let a = vec![1.0_f32; 64];
        let b = vec![1.0_f32; 32];
        assert_eq!(
            ch.transmit(&a, &b),
            Err(SynaxError::LengthMismatch {
                expected: 64,
                actual: 32
            })
        );
    }

    #[test]
    fn myelination_and_immune_shield_equivalence() {
        let mut ch = AxonChannel::new("rust_myelin_verify", 128, 2).expect("channel alloc");
        assert_eq!(ch.state(), AxonMyelinState::Unmyelinated);

        let mut a = vec![80.0_f32; 128];
        let mut b = vec![10.0_f32; 128];
        a[4] = f32::NAN;
        b[11] = f32::INFINITY;

        let out_scalar = ch.transmit(&a, &b).expect("burst 1");
        assert_eq!(ch.state(), AxonMyelinState::Unmyelinated);

        let _ = ch.transmit(&a, &b).expect("burst 2 triggers myelination");
        assert_eq!(ch.state(), AxonMyelinState::Myelinated);

        let out_simd = ch.transmit(&a, &b).expect("burst 3 saltatory");
        assert_eq!(out_scalar, out_simd);

        let st = ch.stats();
        assert_eq!(st.total_transmissions, 3);
        assert_eq!(st.healed_anomalies_count, 6);
        assert!(!ch.kernel_name().is_empty());
    }
}
