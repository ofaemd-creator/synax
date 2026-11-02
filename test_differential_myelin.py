#!/usr/bin/env python3
"""
SYNAX DIFFERENTIAL EQUIVALENCE & FAIR BENCHMARK TEST
=============================================================================
Verifies 1:1 mathematical equivalence between:
  - Scalar reference execution
  - Explicit ARM64 NEON Saltatory execution

Specifically tests the Claude/Codex findings:
  ✓ Channel B NaN/Inf/Spike sanitization in NEON path
  ✓ Accurate anomaly counter in NEON path (must match scalar 100%)
  ✓ Unaligned lengths (vector tail edge cases)
  ✓ Fair benchmark: 201 warm runs median latency
=============================================================================
"""

import math
import random
import statistics
import time
from array import array
from synax_myelin import BiologicalMyelinEngine

def run_tests():
    print("=" * 72)
    print("🧪 SYNAX DIFFERENTIAL EQUIVALENCE & INTEGRITY SUITE")
    print("=" * 72)

    engine = BiologicalMyelinEngine()
    N = 8192

    # İki ayrı kanal oluştur: biri skaler, biri NEON
    axon_scalar = engine.create_channel("test_scalar", N, myelin_threshold=999999)
    axon_neon = engine.create_channel("test_neon", N, myelin_threshold=1)
    axon_neon.force_myelination()

    assert axon_scalar.get_state() == 0, "Scalar axon must be in state 0"
    assert axon_neon.get_state() == 2, "NEON axon must be in state 2 (myelinated)"

    print("[+] Test Kanalları Hazır (Skaler vs NEON Sıçramalı)")

    test_scenarios = [
        ("Normal Temiz Sinyaller", False, False, False),
        ("Kanal A: NaN ve Sonsuz Değerler", True, False, False),
        ("Kanal B: NaN ve Sonsuz Değerler (Claude Bug Check)", False, True, False),
        ("Kanal A & B: Aşırı Sınır Dışı Değerler (+/-99999)", True, True, True),
        ("Unaligned Boyut (8197 örnek - Vektör Kuyruk Testi)", True, True, True)
    ]

    for title, corrupt_a, corrupt_b, corrupt_spikes in test_scenarios:
        count = 8197 if "8197" in title else N
        sig_a = array('f', [random.uniform(20.0, 100.0) for _ in range(count)])
        sig_b = array('f', [random.uniform(5.0, 25.0) for _ in range(count)])

        if corrupt_a:
            sig_a[10] = float('nan')
            sig_a[25] = float('inf')
            sig_a[100] = -float('inf')

        if corrupt_b:
            sig_b[15] = float('nan')
            sig_b[30] = float('inf')
            sig_b[200] = -float('inf')

        if corrupt_spikes:
            sig_a[50] = 50000.0
            sig_b[50] = -99999.0

        # Skaler iletim
        out_scalar, tel_scalar = axon_scalar.transmit(sig_a, sig_b)
        # NEON iletim
        out_neon, tel_neon = axon_neon.transmit(sig_a, sig_b)

        # Doğrulama 1: Çıktı dizileri arasındaki maksimum fark
        max_diff = 0.0
        for i in range(count):
            diff = abs(out_scalar[i] - out_neon[i])
            if diff > max_diff:
                max_diff = diff

        # Doğrulama 2: İyileştirilen anomali sayacı uyumu
        healed_diff = abs(tel_scalar['healed_anomalies'] - tel_neon['healed_anomalies'])

        assert max_diff < 1e-4, f"FAIL [{title}]: Sayısal fark yüksek! max_diff={max_diff}"
        assert healed_diff == 0, f"FAIL [{title}]: Anomali sayaçları uyuşmuyor! Skaler:{tel_scalar['healed_anomalies']} vs NEON:{tel_neon['healed_anomalies']}"

        print(f"  ✓ {title:<46} => Maks Fark: {max_diff:.2e} | Şifa: {tel_neon['healed_anomalies']} [TAM EŞDEĞER]")

    print("\n" + "=" * 72)
    print("⏱️ ADİL VE TEKRARLANABİLİR DONANIM BENCHMARK'I")
    print("Ölçüm: Isınmış önbellek (Warm Cache), 201 Tekrar Medyan Süresi")
    print("=" * 72)

    RUNS = 201
    bench_len = 32768
    raw_a = array('f', [random.uniform(10.0, 120.0) for _ in range(bench_len)])
    raw_b = array('f', [random.uniform(5.0, 20.0) for _ in range(bench_len)])

    # Isınma (Warmup)
    for _ in range(15):
        axon_scalar.transmit(raw_a, raw_b)
        axon_neon.transmit(raw_a, raw_b)

    # 1. Skaler Süreleri
    scalar_times = []
    for _ in range(RUNS):
        t0 = time.perf_counter_ns()
        axon_scalar.transmit(raw_a, raw_b)
        t1 = time.perf_counter_ns()
        scalar_times.append((t1 - t0) / 1000.0)

    # 2. NEON Sıçramalı Süreleri
    neon_times = []
    for _ in range(RUNS):
        t0 = time.perf_counter_ns()
        axon_neon.transmit(raw_a, raw_b)
        t1 = time.perf_counter_ns()
        neon_times.append((t1 - t0) / 1000.0)

    med_scalar = statistics.median(scalar_times)
    med_neon = statistics.median(neon_times)
    ratio = med_scalar / med_neon

    print(f"  • Skaler Medyan Süre (32K float) : {med_scalar:>7.2f} µs")
    print(f"  • NEON Sıçramalı Medyan Süre     : {med_neon:>7.2f} µs")
    print(f"  • Gerçek ve Adil Hızlanma Katsayısı: {ratio:>6.2f}x (Medyan)")
    print("=" * 72)
    print("🎉 TÜM DOĞRULUK VE ADİL ÖLÇÜM TESTLERİ GEÇTİ!")

if __name__ == "__main__":
    run_tests()

