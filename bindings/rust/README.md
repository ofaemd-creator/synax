# `synax-rs` — Official Rust SDK for SYNAX (`.sx`)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../../LICENSE)

Safe, zero-dependency Rust FFI wrapper (`ABI v1`) for `libsynax_myelin`, the adaptive C11 / ARM64 NEON / x86_64 SIMD runtime of the **SYNAX (`.sx`)** neuro-symbolic compiler.

> **Research Software Disclaimer:** `synax-rs` and SYNAX are purely experimental academic and computational research tools. They are **not** certified medical devices (`EU MDR 2017/745`, `FDA 21 CFR`, `IEC 60601-2-4`) and must **never** be used in clinical patient care or defibrillation. See [`MEDICAL_RESEARCH_DISCLAIMER.md`](../../MEDICAL_RESEARCH_DISCLAIMER.md).

---

## Features

- **Zero External Crate Dependencies:** Built solely on `std::ffi` and `std::ptr::NonNull`.
- **RAII Resource Safety:** [`AxonChannel`] automatically closes dynamic kernel handles and frees C heap allocations in `Drop` via `synax_axon_destroy`.
- **Compile-Time & Slice Invariants:** Enforces `a.len() == b.len()` and Rust aliasing guarantees (`&[f32]` inputs vs `&mut [f32]` output) before crossing the FFI boundary.
- **Hot-Swap Compiled `.sx` Kernels:** Bind `synaxc`-verified reference and SIMD winner shared libraries via [`AxonChannel::bind_compiled_kernels`].

---

## Building & Testing

1. Ensure the native `libsynax_myelin` shared library is built in the repository root:

   ```bash
   # macOS (ARM64 NEON / x86_64)
   clang -O3 -shared -fPIC ../../synax_myelin_engine.c -lm -ldl -o ../../libsynax_myelin.dylib

   # Linux (x86_64 / AArch64)
   clang -O3 -shared -fPIC ../../synax_myelin_engine.c -lm -ldl -o ../../libsynax_myelin.so
   ```

2. Build and run the Rust test suite (`build.rs` automatically resolves the repository root or `SYNAX_LIB_DIR`):

   ```bash
   cargo test
   ```

   If `libsynax_myelin` resides in a custom directory:

   ```bash
   SYNAX_LIB_DIR=/path/to/lib cargo test
   ```

---

## Quick Example

```rust
use synax_rs::{AxonChannel, AxonMyelinState};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Automatically myelinate after 2 bursts of 1024 f32 samples
    let mut channel = AxonChannel::new("hemodynamic_research", 1024, 2)?;
    assert_eq!(channel.state(), AxonMyelinState::Unmyelinated);

    let mut dbp = vec![80.0_f32; 1024];
    let mut cvp = vec![10.0_f32; 1024];
    dbp[42] = f32::NAN; // Simulated electrode dropout sanitized by Immune Shield

    let ref_out = channel.transmit(&dbp, &cvp)?;
    let _ = channel.transmit(&dbp, &cvp)?; // Reaches threshold -> hot-swaps to SIMD
    assert_eq!(channel.state(), AxonMyelinState::Myelinated);

    let simd_out = channel.transmit(&dbp, &cvp)?;
    assert_eq!(ref_out, simd_out); // 100% bit-exact scalar/SIMD parity

    let stats = channel.stats();
    println!(
        "Kernel: {} | Transmissions: {} | Healed Anomalies: {}",
        channel.kernel_name(),
        stats.total_transmissions,
        stats.healed_anomalies_count
    );
    Ok(())
}
```

---

## License

Licensed under the [Apache License, Version 2.0](../../LICENSE).
