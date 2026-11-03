// Copyright 2026 Dr. Ömer Faruk Aydın and SYNAX Project Contributors
// SPDX-License-Identifier: Apache-2.0

use std::env;
use std::path::PathBuf;

fn main() {
    println!("cargo:rerun-if-env-changed=SYNAX_LIB_DIR");

    let search_dir = if let Ok(custom_dir) = env::var("SYNAX_LIB_DIR") {
        PathBuf::from(custom_dir)
    } else {
        let manifest_dir = PathBuf::from(
            env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be set by Cargo"),
        );
        manifest_dir
            .join("..")
            .join("..")
            .canonicalize()
            .unwrap_or_else(|_| manifest_dir.join("..").join(".."))
    };

    println!("cargo:rustc-link-search=native={}", search_dir.display());
    println!("cargo:rustc-link-lib=dylib=synax_myelin");

    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    if target_os == "macos" || target_os == "linux" {
        println!("cargo:rustc-link-arg=-Wl,-rpath,{}", search_dir.display());
    }
}
