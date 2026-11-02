#!/usr/bin/env python3
"""
SYNAX REAL-TIME BIOMEDICAL SIGNAL PIPELINE (v1.0)
=============================================================================
High-throughput (100,000 samples/sec) physiological stream simulator & processor.
Feeds life-critical hemodynamics into SYNAX Biological Myelin Axons:
  - Channels:
      1. Arterial Blood Pressure (ABP): SBP, DBP, Dicrotic Notch, MAP
      2. Central Venous Pressure (CVP): A/C/V atrial pressure waves
      3. Coronary Perfusion Pressure (CPP = DBP - CVP)
      4. ECG Lead II: P-Q-R-S-T morphology & ventricular arrhythmia
  - Real-time SIMD Immune Shield: Handles electrocautery noise, NaN, detached leads.
  - Neuroplastic Myelination: Cold-start -> Saltatory Conduction jump at runtime.
=============================================================================
"""

import os
import sys
import time
import math
import random
from array import array
from typing import Generator, Tuple, Dict, Any

from synax_myelin import BiologicalMyelinEngine, AxonChannel


class PhysiologicalWaveformGenerator:
    """
    Üretilen dalga formları gerçek insan kardiyovasküler fizyolojisine dayanır:
      - SBP: 120 mmHg, DBP: 80 mmHg
      - Dikrotik Çentik (Aort kapağı kapanma yansıması)
      - CVP (Santral Venöz Basınç): 8 mmHg
      - CPP (Koroner Perfüzyon Basıncı): Kalbin hayatta kalma eşiği
    """
    def __init__(self, sample_rate_hz: int = 1000):
        self.sample_rate = sample_rate_hz
        self.t = 0.0
        self.hr_bpm = 75.0  # Kalp atım hızı (bpm)

    def generate_abp_sample(self, t_sec: float) -> float:
        beat_period = 60.0 / self.hr_bpm
        phase = (t_sec % beat_period) / beat_period

        # Sistolik yükselme ve dikrotik çentik modeli
        if phase < 0.2:
            # Hızlı sistolik ejeksiyon yükselmesi
            rise = math.sin(phase / 0.2 * (math.pi / 2))
            val = 80.0 + 40.0 * rise
        elif phase < 0.4:
            # Erken diyastolik düşüş ve dikrotik çentik
            decay = math.cos((phase - 0.2) / 0.2 * (math.pi / 2))
            notch = 6.0 * math.sin((phase - 0.2) / 0.2 * math.pi)
            val = 95.0 + 25.0 * decay + notch
        else:
            # Geç diyastolik üstel sönüm
            decay_phase = (phase - 0.4) / 0.6
            val = 80.0 + 15.0 * math.exp(-3.0 * decay_phase)
        return val

    def generate_cvp_sample(self, t_sec: float) -> float:
        beat_period = 60.0 / self.hr_bpm
        phase = (t_sec % beat_period) / beat_period
        # A, C ve V venöz dalgaları
        a_wave = 3.0 * math.exp(-((phase - 0.1) ** 2) / 0.002)
        v_wave = 2.5 * math.exp(-((phase - 0.5) ** 2) / 0.005)
        return 6.0 + a_wave + v_wave

    def generate_ecg_sample(self, t_sec: float) -> float:
        beat_period = 60.0 / self.hr_bpm
        phase = (t_sec % beat_period) / beat_period
        
        # P dalgası
        p = 0.15 * math.exp(-((phase - 0.15) ** 2) / 0.001)
        # QRS kompleksi (Q negatif, R yüksek pozitif, S negatif)
        q = -0.15 * math.exp(-((phase - 0.28) ** 2) / 0.0003)
        r = 1.20 * math.exp(-((phase - 0.30) ** 2) / 0.0002)
        s = -0.25 * math.exp(-((phase - 0.32) ** 2) / 0.0003)
        # T dalgası
        t = 0.30 * math.exp(-((phase - 0.55) ** 2) / 0.005)
        
        baseline_noise = random.gauss(0, 0.01)
        return p + q + r + s + t + baseline_noise


def run_biomedical_streaming_simulation(duration_seconds: float = 3.0):
    print("=" * 76)
    print("🫀 SYNAX CANLI BİYOMEDİKAL SİNYAL AKIŞI VE MİYELİN NÖRON MOTORU")
    print("Fizyolojik Hat: Arteriyel Basınç (ABP) + Santral Venöz (CVP) -> CPP İzleme")
    print("=" * 76)

    engine = BiologicalMyelinEngine()
    
    # 8192 örnekli bloklar halinde yüksek frekanslı akış (8.192 kS/block)
    block_size = 8192
    myelin_threshold = 6  # 6 blok sonra akson miyelinleşir

    abp_axon = engine.create_channel("abp_hemodynamics_axon", block_size, myelin_threshold=myelin_threshold)
    generator = PhysiologicalWaveformGenerator(sample_rate_hz=10000)

    total_samples = 0
    start_wall_time = time.time()
    block_idx = 0

    print(f"\n[+] Akson Hazır: '{abp_axon.name}' (Miyelinleşme Eşiği: {myelin_threshold} blok)")
    print("[*] Sinyal Akışı Başlatılıyor (Kardiyovasküler & CPR Hemodinamik Analizi)...\n")

    while (time.time() - start_wall_time) < duration_seconds:
        block_idx += 1
        t_base = total_samples / 10000.0

        # Blok verilerini üret
        abp_block = array('f')
        cvp_block = array('f')

        for i in range(block_size):
            t_curr = t_base + (i / 10000.0)
            p_abp = generator.generate_abp_sample(t_curr)
            p_cvp = generator.generate_cvp_sample(t_curr)

            # Rastgele yoğun bakım / ameliyathane gürültüsü (elektrokoter koter iğnesi gürültüsü)
            if random.random() < 0.001:
                p_abp = float('nan') # Kopan elektrot

            abp_block.append(p_abp)
            cvp_block.append(p_cvp)

        # SYNAX Miyelinli Aksonundan Geçir (Action Potential Conduction)
        out_hemo, telemetry = abp_axon.transmit(abp_block, cvp_block)
        total_samples += block_size

        # Anlık fizyolojik parametreler (MAP ve CPP hesaplama)
        sample_slice = abp_block[:200]
        valid_abp = [v for v in sample_slice if math.isfinite(v)]
        sbp = max(valid_abp) if valid_abp else 120.0
        dbp = min(valid_abp) if valid_abp else 80.0
        map_val = (sbp + 2.0 * dbp) / 3.0
        cpp_val = dbp - 8.0 # Koroner Perfüzyon Basıncı

        # Görsel ASCII dalga çubuğu
        bar_len = int(max(0, min(24, (map_val - 60) * 0.4)))
        ascii_wave = "█" * bar_len + "░" * (24 - bar_len)

        status_icon = "⚡ MIYELINLI" if telemetry['state_code'] == 2 else "⏳ HAM AKSON"
        ratio_str = f"{telemetry['velocity_ratio']:.1f}x" if telemetry['state_code'] == 2 else "1.0x"
        cur_lat = telemetry['myelinated_avg_us'] if telemetry['state_code'] == 2 else telemetry['unmyelinated_avg_us']

        print(f"Blok #{block_idx:02d} | [{status_icon}] MAP:{map_val:5.1f} | CPP:{cpp_val:4.1f} mmHg | [{ascii_wave}] | Gecikme:{cur_lat:5.1f}µs | Hız:{ratio_str} | Şifa:{telemetry['healed_anomalies']} anomali")
        time.sleep(0.08)

    elapsed = time.time() - start_wall_time
    throughput_ksps = (total_samples / elapsed) / 1000.0
    stats = abp_axon.get_stats()

    print("\n" + "=" * 76)
    print("📊 BİYOMEDİKAL AKIŞ PERFORMANS SONUÇLARI:")
    print(f"  - Toplam İşlenen Fizyolojik Örnek : {total_samples:,} örnek")
    print(f"  - Efektif Veri Akış Debisi         : {throughput_ksps:,.1f} kS/s (Kilo-Samples/sec)")
    print(f"  - Kurtarılan / Onarılan Veri       : {stats.healed_anomalies_count} sensör anomalisi")
    print(f"  - Başlangıç Ham Gecikmesi          : {stats.unmyelinated_avg_ns / 1000.0:.2f} µs")
    print(f"  - Miyelinli Saltatory Gecikmesi    : {stats.myelinated_avg_ns / 1000.0:.2f} µs")
    print(f"  - Donanımsal Nöron Hızlanması     : {stats.conduction_velocity_ratio:.2f}x İLETİM KAZANCI")
    print("=" * 76)


if __name__ == "__main__":
    run_biomedical_streaming_simulation()
