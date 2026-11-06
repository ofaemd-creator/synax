#!/usr/bin/env python3
"""
SYNAX AXON HARDWARE FINGERPRINT ENGINE (src/synax/hardware.py)
=============================================================================
Computes a deterministic cryptographic fingerprint (`hw_fingerprint`) of the
active execution host (CPU microarchitecture, SIMD ISA support, core topology,
cache line size, OS kernel, and C/LLVM toolchain version) so MYELIN's
persistent optimization memory never reuses stale timings across hardware or
compiler upgrades.
=============================================================================
"""

import functools
import hashlib
import json
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HardwareFingerprint:
    os_system: str
    machine_arch: str
    cpu_brand: str
    logical_cores: int
    cacheline_bytes: int
    simd_isa: str           # "arm64_neon" | "x86_64_avx512" | "x86_64_avx2" | "scalar"
    compiler_id: str
    fingerprint_id: str


def _run_cmd_quiet(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=3)
        return out.strip()
    except Exception:
        return ""


@functools.lru_cache(maxsize=1)
def detect_hardware_fingerprint() -> HardwareFingerprint:
    os_sys = platform.system()
    arch = platform.machine().lower()
    cores = os.cpu_count() or 1
    brand = "Generic CPU"
    cacheline = 64
    simd = "scalar"

    if os_sys == "Darwin":
        brand = _run_cmd_quiet(["sysctl", "-n", "machdep.cpu.brand_string"]) or "Apple Silicon"
        cl_str = _run_cmd_quiet(["sysctl", "-n", "hw.cachelinesize"])
        if cl_str.isdigit():
            cacheline = int(cl_str)
    elif os_sys == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                info = f.read()
            for line in info.splitlines():
                if "model name" in line and ":" in line:
                    brand = line.split(":", 1)[1].strip()
                    break
            if "avx512f" in info:
                simd = "x86_64_avx512"
            elif "avx2" in info:
                simd = "x86_64_avx2"
        except OSError:
            pass
    elif os_sys == "Windows":
        brand = platform.processor() or "x86_64 Windows CPU"

    if "arm64" in arch or "aarch64" in arch:
        simd = "arm64_neon"
        if os_sys == "Darwin" and cacheline == 64:
            cacheline = 128
    elif simd == "scalar" and ("x86_64" in arch or "amd64" in arch):
        simd = "x86_64_avx2"

    cc_bin = shutil.which("clang") or shutil.which("gcc") or shutil.which("cc")
    compiler_id = "none"
    if cc_bin:
        ver_out = _run_cmd_quiet([cc_bin, "--version"])
        compiler_id = ver_out.splitlines()[0].strip() if ver_out else os.path.basename(cc_bin)

    canonical = {
        "os_system": os_sys,
        "machine_arch": arch,
        "cpu_brand": brand,
        "logical_cores": cores,
        "cacheline_bytes": cacheline,
        "simd_isa": simd,
        "compiler_id": compiler_id,
    }
    raw_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    fp_id = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()[:12]

    return HardwareFingerprint(
        os_system=os_sys,
        machine_arch=arch,
        cpu_brand=brand,
        logical_cores=cores,
        cacheline_bytes=cacheline,
        simd_isa=simd,
        compiler_id=compiler_id,
        fingerprint_id=fp_id,
    )


def fingerprint_to_dict(fp: HardwareFingerprint) -> dict:
    return asdict(fp)
