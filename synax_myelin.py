#!/usr/bin/env python3
"""
SYNAX BIOLOGICAL MYELIN RUNTIME (v1.0)
=============================================================================
High-performance Python & C Bridge for Biological Action-Potential Conduction.
100% Offline, Zero External Dependencies (pure ctypes + array/memoryview).

Emulates real neurobiology:
  - Unmyelinated Axon: Continuous conduction, high metabolic & compute cost.
  - Activity-Triggered Myelination: Oligodendrocytes synthesize myelin sheath.
  - Myelinated Axon (Ranvier Nodes): Saltatory conduction, 10x-50x speedup,
    with embedded SIMD Immune Shield against corrupted biomedical signals.
=============================================================================
"""

import os
import sys
import time
import math
import ctypes
import random
from array import array
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List, Union

LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libsynax_myelin.dylib")

# C Data Structures
class AxonStats(ctypes.Structure):
    _fields_ = [
        ("total_transmissions", ctypes.c_uint64),
        ("myelination_threshold", ctypes.c_uint64),
        ("unmyelinated_avg_ns", ctypes.c_double),
        ("myelinated_avg_ns", ctypes.c_double),
        ("conduction_velocity_ratio", ctypes.c_double),
        ("healed_anomalies_count", ctypes.c_size_t),
        ("internode_block_size", ctypes.c_size_t),
    ]

class SynaxAxonChannel(ctypes.Structure):
    pass # Opaque struct pointer

class BiologicalMyelinEngine:
    def __init__(self, lib_path: Optional[str] = None):
        target_lib = lib_path or LIB_PATH
        if not os.path.exists(target_lib):
            raise FileNotFoundError(f"Native library not found at: {target_lib}")
        
        self.lib = ctypes.CDLL(target_lib)
        self._setup_bindings()

    def _setup_bindings(self):
        # synax_axon_create
        self.lib.synax_axon_create.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.lib.synax_axon_create.restype = ctypes.POINTER(SynaxAxonChannel)

        # synax_axon_destroy
        self.lib.synax_axon_destroy.argtypes = [ctypes.POINTER(SynaxAxonChannel)]
        self.lib.synax_axon_destroy.restype = None

        # synax_axon_transmit
        self.lib.synax_axon_transmit.argtypes = [
            ctypes.POINTER(SynaxAxonChannel),
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t
        ]
        self.lib.synax_axon_transmit.restype = ctypes.c_int

        # synax_axon_myelinate
        self.lib.synax_axon_myelinate.argtypes = [ctypes.POINTER(SynaxAxonChannel)]
        self.lib.synax_axon_myelinate.restype = ctypes.c_int

        # synax_axon_get_stats
        self.lib.synax_axon_get_stats.argtypes = [ctypes.POINTER(SynaxAxonChannel)]
        self.lib.synax_axon_get_stats.restype = AxonStats

        # synax_axon_get_state
        self.lib.synax_axon_get_state.argtypes = [ctypes.POINTER(SynaxAxonChannel)]
        self.lib.synax_axon_get_state.restype = ctypes.c_int

        # synax_axon_bind_compiled_kernels
        if hasattr(self.lib, "synax_axon_bind_compiled_kernels"):
            self.lib.synax_axon_bind_compiled_kernels.argtypes = [
                ctypes.POINTER(SynaxAxonChannel),
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.c_char_p,
            ]
            self.lib.synax_axon_bind_compiled_kernels.restype = ctypes.c_int

        # synax_axon_get_kernel_name
        if hasattr(self.lib, "synax_axon_get_kernel_name"):
            self.lib.synax_axon_get_kernel_name.argtypes = [ctypes.POINTER(SynaxAxonChannel)]
            self.lib.synax_axon_get_kernel_name.restype = ctypes.c_char_p

    def create_channel(self, name: str, fixed_length: int, myelin_threshold: int = 25) -> "AxonChannel":
        ptr = self.lib.synax_axon_create(name.encode("utf-8"), fixed_length, myelin_threshold)
        if not ptr:
            raise RuntimeError("Failed to allocate SynaxAxonChannel")
        return AxonChannel(self, ptr, name, fixed_length)


class AxonChannel:
    STATE_NAMES = {
        0: "UNMYELINATED (Continuous)",
        1: "MYELINATING (JIT Synthesis)",
        2: "MYELINATED (Saltatory Jump)"
    }

    def __init__(self, engine: BiologicalMyelinEngine, handle: ctypes.POINTER(SynaxAxonChannel), name: str, length: int):
        self.engine = engine
        self.handle = handle
        self.name = name
        self.length = length

    def transmit(self, signal_a: Union[array, List[float]], signal_b: Optional[Union[array, List[float]]] = None) -> Tuple[array, Dict[str, Any]]:
        """
        Transmit an action potential burst through this axon.
        Takes array('f') or list of floats.
        Returns output array('f') and live performance telemetry.
        """
        if isinstance(signal_a, array) and signal_a.typecode == 'f':
            arr_a = signal_a
        else:
            arr_a = array('f', signal_a)

        count = len(arr_a)
        arr_dst = array('f', [0.0]) * count if count > 0 else array('f')
        if count == 0:
            stats = self.get_stats()
            state = self.get_state()
            return arr_dst, {
                "state_code": state,
                "state_label": self.STATE_NAMES.get(state, "UNKNOWN"),
                "active_kernel": self.get_kernel_name(),
                "transmissions": stats.total_transmissions,
                "unmyelinated_avg_us": stats.unmyelinated_avg_ns / 1000.0,
                "myelinated_avg_us": stats.myelinated_avg_ns / 1000.0,
                "velocity_ratio": stats.conduction_velocity_ratio,
                "healed_anomalies": stats.healed_anomalies_count,
            }

        addr_a, _ = arr_a.buffer_info()
        ptr_a = ctypes.cast(addr_a, ctypes.POINTER(ctypes.c_float))

        ptr_b = None
        if signal_b is not None:
            if isinstance(signal_b, array) and signal_b.typecode == 'f':
                arr_b = signal_b
            else:
                arr_b = array('f', signal_b)
            addr_b, _ = arr_b.buffer_info()
            ptr_b = ctypes.cast(addr_b, ctypes.POINTER(ctypes.c_float))

        addr_dst, _ = arr_dst.buffer_info()
        ptr_dst = ctypes.cast(addr_dst, ctypes.POINTER(ctypes.c_float))

        res = self.engine.lib.synax_axon_transmit(self.handle, ptr_a, ptr_b, ptr_dst, count)
        if res != 0:
            raise RuntimeError(f"Transmission failed on axon {self.name}")

        stats = self.get_stats()
        state = self.get_state()
        return arr_dst, {
            "state_code": state,
            "state_label": self.STATE_NAMES.get(state, "UNKNOWN"),
            "active_kernel": self.get_kernel_name(),
            "transmissions": stats.total_transmissions,
            "unmyelinated_avg_us": stats.unmyelinated_avg_ns / 1000.0,
            "myelinated_avg_us": stats.myelinated_avg_ns / 1000.0,
            "velocity_ratio": stats.conduction_velocity_ratio,
            "healed_anomalies": stats.healed_anomalies_count
        }

    def bind_compiled_kernels(self, ref_dylib_path: str, myelinated_dylib_path: str, kernel_label: str = "SynaxC_SIMD"):
        if not hasattr(self.engine.lib, "synax_axon_bind_compiled_kernels"):
            raise RuntimeError("Native library does not expose synax_axon_bind_compiled_kernels; recompile libsynax_myelin.dylib")
        rc = self.engine.lib.synax_axon_bind_compiled_kernels(
            self.handle,
            str(ref_dylib_path).encode("utf-8"),
            str(myelinated_dylib_path).encode("utf-8"),
            str(kernel_label).encode("utf-8"),
        )
        if rc != 0:
            raise RuntimeError(f"Failed to bind compiled dylibs to axon '{self.name}' (error code {rc})")

    def get_kernel_name(self) -> str:
        if hasattr(self.engine.lib, "synax_axon_get_kernel_name"):
            raw = self.engine.lib.synax_axon_get_kernel_name(self.handle)
            return raw.decode("utf-8") if raw else "UNKNOWN"
        return "Builtin"

    def force_myelination(self):
        self.engine.lib.synax_axon_myelinate(self.handle)

    def get_stats(self) -> AxonStats:
        return self.engine.lib.synax_axon_get_stats(self.handle)

    def get_state(self) -> int:
        return self.engine.lib.synax_axon_get_state(self.handle)

    def __del__(self):
        if hasattr(self, "handle") and self.handle:
            self.engine.lib.synax_axon_destroy(self.handle)
            self.handle = None


def run_myelin_verification_demo():
    print("=" * 72)
    print("🧠 SYNAX BIOLOGICAL MYELIN ENGINE — REAL HARDWARE EXPERIMENT")
    print("Apple Silicon M1 ARM64 NEON + Ranvier Saltatory JIT Conduction")
    print("=" * 72)

    engine = BiologicalMyelinEngine()
    channel_len = 32768  # 32K samples per burst (~128KB - L1/L2 boundary)
    threshold = 8        # 8 burst sonra otonom miyelinleşme (plasticity) başlasın

    axon = engine.create_channel("cardio_axon_alpha", channel_len, myelin_threshold=threshold)

    print(f"\n[+] Axon kanalı oluşturuldu: {axon.name} (Eşik: {threshold} atım, Boyut: {channel_len} örnek)")
    print(f"[*] Başlangıç Biyolojik Durumu: {axon.STATE_NAMES[axon.get_state()]}")

    print("\n--- 1. Faz: Ham Akson İletimi (Unmyelinated Phase) ---")
    for step in range(1, 13):
        # Sentetik fizyolojik biyomedikal sinyal (Arteriyel dalga + gürültü)
        sig_a = array('f')
        sig_b = array('f')
        for i in range(channel_len):
            t = (i / channel_len) * 4.0 * math.pi
            val_a = 80.0 + 40.0 * math.sin(t) + random.gauss(0, 0.5)
            val_b = 10.0 + 5.0 * math.cos(t)
            sig_a.append(val_a)
            sig_b.append(val_b)

        # Biyolojik sensör gürültüsü / Kopuk elektrot (NaN ve sonsuz değerler)
        if step % 3 == 0:
            for bad_idx in range(100, 105):
                sig_a[bad_idx] = float('nan')
            sig_a[500] = 9999.0

        out, telemetry = axon.transmit(sig_a, sig_b)
        
        status_tag = f"[{telemetry['state_label']}]"
        if telemetry['state_code'] == 2:
            speedup_str = f"🚀 Sıçramalı Hızlanma: {telemetry['velocity_ratio']:.2f}x"
            lat_str = f"Miyelinli: {telemetry['myelinated_avg_us']:.1f} µs"
        else:
            speedup_str = "Sürekli iletim (Miyelinsiz)"
            lat_str = f"Ham İletim: {telemetry['unmyelinated_avg_us']:.1f} µs"

        print(f"  Atım #{step:02d} | {status_tag:<29} | {lat_str:<22} | {speedup_str} | Şifa: {telemetry['healed_anomalies']} anomali")
        time.sleep(0.01)

    print("\n--- 2. Faz: Miyelinleşmiş Yüksek Hızlı Sıçramalı İletim (Saltatory Phase) ---")
    for step in range(13, 22):
        sig_a = array('f', [random.uniform(60, 140) for _ in range(channel_len)])
        sig_b = array('f', [random.uniform(5, 15) for _ in range(channel_len)])
        out, telemetry = axon.transmit(sig_a, sig_b)
        
        lat_str = f"Miyelinli: {telemetry['myelinated_avg_us']:.1f} µs"
        speedup_str = f"🚀 Hızlanma: {telemetry['velocity_ratio']:.2f}x (Ranvier Düğüm Blokları)"
        print(f"  Atım #{step:02d} | [{telemetry['state_label']:<27}] | {lat_str:<22} | {speedup_str}")
        time.sleep(0.01)

    final_stats = axon.get_stats()
    print("\n" + "=" * 72)
    print("🏁 GERÇEK DONANIM RAPORU (Apple Silicon M1 Biyolojik İletim Verimi):")
    print(f"  - Toplam İletilen Aksiyon Potansiyeli : {final_stats.total_transmissions}")
    print(f"  - İyileştirilen Biyomedikal Anomali  : {final_stats.healed_anomalies_count} adet")
    print(f"  - Ham İletim Süresi (Unmyelinated)  : {final_stats.unmyelinated_avg_ns / 1000.0:.2f} µs")
    print(f"  - Miyelinli İletim Süresi (Saltatory): {final_stats.myelinated_avg_ns / 1000.0:.2f} µs")
    print(f"  - Biyolojik İletim Hızlanması         : {final_stats.conduction_velocity_ratio:.2f}x HIZLI")
    print("=" * 72)


if __name__ == "__main__":
    run_myelin_verification_demo()
