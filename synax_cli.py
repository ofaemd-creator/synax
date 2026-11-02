#!/usr/bin/env python3
"""
SYNAX CLI (v1.0) — Unified Neuro-Symbolic & Biological Myelin Interface
=============================================================================
Usage:
  synax run <file.sx>        Compile & execute a SYNAX intent script
  synax myelin               Run Biological Myelin Conduction benchmark (Ranvier JIT)
  synax stream               Run Real-time Biomedical Hemodynamics Stream (100 kS/s)
  synax benchmark            Run Hardware Axon/Tycon Evolution Matrix
  synax status               Inspect active hardware, myelin cache & telemetry
  synax version              Show version & sovereign repository details
=============================================================================
"""

import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_banner():
    banner = """
   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██╗  ██╗
   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗╚██╗██╔╝
   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║ ╚███╔╝ 
   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║ ██╔██╗ 
   ███████║   ██║   ██║ ╚████║██║  ██║██╔╝ ██╗
   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝
   Biologically Inspired Neuro-Symbolic Language & Myelin Engine v1.0
   Sovereign Server: https://synaxcode.org/git/synax.git
"""
    print(banner)


def cmd_help():
    print_banner()
    print("""KOMUTLAR:
  synax run <dosya.sx>    : .sx doğal dil niyet dosyasını AST ve C/SIMD'e derleyip çalıştırır
  synax myelin            : Biyolojik Ranvier Düğümleri ve Miyelin Kılıfı JIT deneyini yürütür
  synax stream            : 100,000 örnek/sn Biyomedikal Kardiyovasküler & CPP akışını başlatır
  synax benchmark         : Apple Silicon M1 çok çekirdek ve NEON evrim matrisini test eder
  synax status            : Miyelin hafızasını (myelin_memory.json) ve telemetriyi gösterir
  synax version           : Sürüm, donanım kimliği ve egemen git deposu bilgisini basar
""")


def cmd_version():
    print("SYNAX Neuro-Symbolic Runtime v1.0-OMEGA (Darwin arm64 / Apple Silicon)")
    print("Egemen Git Deposu : https://synaxcode.org/git/synax.git")
    print("Dokümantasyon     : https://synaxcode.org")
    print("Resmi Platform    : https://synaxcode.com")


def cmd_status():
    mem_path = os.path.join(BASE_DIR, "myelin_memory.json")
    print("\n🧠 SYNAX MİYELİN HAFIZA DURUMU:")
    if os.path.exists(mem_path):
        with open(mem_path, "r") as f:
            data = json.load(f)
        for k, v in data.items():
            print(f"  • Senaryo: {k:<30} -> Kazanan Gen: {v.get('winner_gene')} ({v.get('best_time_us')} µs)")
    else:
        print("  (Henüz kayıtlı miyelin hafızası bulunamadı. 'synax benchmark' çalıştırın)")


def main():
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    subcmd = sys.argv[1].lower()

    if subcmd in ("-h", "--help", "help"):
        cmd_help()
    elif subcmd in ("-v", "--version", "version"):
        cmd_version()
    elif subcmd == "status":
        cmd_status()
    elif subcmd == "myelin":
        from synax_myelin import run_myelin_verification_demo
        run_myelin_verification_demo()
    elif subcmd in ("stream", "live"):
        from synax_biomedical_stream import run_biomedical_streaming_simulation
        dur = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
        run_biomedical_streaming_simulation(duration_seconds=dur)
    elif subcmd == "benchmark":
        import synax_core
        synax_core.run_omega_evolution()
    elif subcmd == "run":
        if len(sys.argv) < 3:
            print("Hata: Lütfen çalıştırılacak .sx dosyasını belirtin. Örnek: synax run examples/biyomedikal_kardiyo.sx")
            sys.exit(1)
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"Hata: Dosya bulunamadı: {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        import synax_core
        synax_core.run_omega_evolution(content)
    else:
        # Doğrudan dosya yolu verilmişse
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                content = f.read()
            import synax_core
            synax_core.run_omega_evolution(content)
        else:
            print(f"Bilinmeyen komut veya dosya: {sys.argv[1]}")
            cmd_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
