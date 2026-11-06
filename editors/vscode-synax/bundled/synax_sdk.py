#!/usr/bin/env python3.11
"""
SYNAX Python SDK — Kendi projelerinizde tek satırla SYNAX kullanımı!
"""
import ctypes
import time
from typing import List, Union
from synax_core import (
    SynapseEngine,
    AxonProfiler,
    TyconGeneticSynthesizer,
    MYELIN_MEMORY_PATH
)

class SynaxKernel:
    def __init__(self, niyet_metni: str, simulate_tiny_mcu: bool = False):
        self.intent = SynapseEngine.parse_intent(niyet_metni)
        self.hw = AxonProfiler.probe(simulate_tiny_cpu=simulate_tiny_mcu)
        self.so_path, self.population = TyconGeneticSynthesizer.build_evolutionary_population(self.intent, self.hw)
        self.lib = ctypes.CDLL(self.so_path)

        # C fonksiyonlarını bağla
        self._funcs = {}
        for chrom in self.population:
            fn = getattr(self.lib, chrom.fn_name)
            fn.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
                ctypes.c_float
            ]
            fn.restype = None
            self._funcs[chrom.gene_id] = fn

        self._immune_fn = self.lib.synax_immune_scan_and_heal
        self._immune_fn.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
        self._immune_fn.restype = ctypes.c_size_t

        self.champion = None

    def run(self, sinyal_a: List[float], sinyal_b: List[float], bias: float = 0.0, auto_heal: bool = True) -> dict:
        n = min(len(sinyal_a), len(sinyal_b))
        ArrType = ctypes.c_float * n
        a_c = ArrType(*sinyal_a[:n])
        b_c = ArrType(*sinyal_b[:n])
        out_c = ArrType(*([0.0] * n))

        healed = 0
        if auto_heal:
            healed += int(self._immune_fn(a_c, n))
            healed += int(self._immune_fn(b_c, n))

        # İlk çalıştırmada en hızlı DNA'yı bul ve kilitlen (Miyelinlenme)
        if self.champion is None:
            candidates = self.population[:2] if self.hw.tier == "TINY_MCU" else self.population
            for chrom in candidates:
                fn = self._funcs[chrom.gene_id]
                t0 = time.perf_counter_ns()
                fn(a_c, b_c, out_c, n, bias)
                elapsed_us = (time.perf_counter_ns() - t0) / 1000.0
                chrom.record(elapsed_us)
            self.champion = min(candidates, key=lambda c: c.best_time_us)

        # Kilitlenen şampiyon gen ile çalıştır
        fn = self._funcs[self.champion.gene_id]
        t0 = time.perf_counter_ns()
        fn(a_c, b_c, out_c, n, bias)
        elapsed_us = (time.perf_counter_ns() - t0) / 1000.0

        return {
            "sonuc_ilk_5": [round(out_c[i], 4) for i in range(min(5, n))],
            "secilen_dna": self.champion.gene_id,
            "sure_us": round(elapsed_us, 2),
            "onarilan_bozuk_veri": healed,
            "raw_output_buffer": out_c
        }

def compile_intent(niyet: str, simulate_tiny_mcu: bool = False) -> SynaxKernel:
    """Doğal dil niyetini kendi kendine evrimleşen SYNAX çekirdeğine dönüştürür."""
    return SynaxKernel(niyet, simulate_tiny_mcu=simulate_tiny_mcu)


# ─────────────────────────────────────────────────────────────────
# ÖRNEK KULLANIM (Kullanıcının Kendi Projesi)
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== SYNAX SDK: KENDİ PROJENİZDE KULLANIM ÖRNEĞİ ===\n")

    # 1. Doğal dille ne istediğinizi söyleyin:
    motor = compile_intent("""
        niyet: İki veri serisi arasındaki farkın karesini (anomali enerjisini) hesapla.
        kural: Bozuk verileri (NaN/Sonsuz) otomatik temizle.
    """)

    # 2. İçinde bozuk (NaN / Sonsuz) veriler de olan 500,000 elemanlı veri gönderin:
    veri_1 = [10.5, float("nan"), 25.0, float("inf"), 40.0] * 100_000
    veri_2 = [8.5,  12.0,         20.0, 5.0,          30.0] * 100_000

    # 3. Çalıştırın!
    rapor = motor.run(veri_1, veri_2, bias=1.0)

    print(f"✓ Seçilen Şampiyon DNA : {rapor['secilen_dna']}")
    print(f"✓ Çalışma Süresi       : {rapor['sure_us']} µs (500,000 eleman!)")
    print(f"✓ Onarılan Bozuk Veri  : {rapor['onarilan_bozuk_veri']:,} adet NaN/Inf temizlendi")
    print(f"✓ İlk 5 Sonuç          : {rapor['sonuc_ilk_5']}")

