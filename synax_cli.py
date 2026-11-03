#!/usr/bin/env python3
"""
SYNAX CLI (v0.5) — Unified Neuro-Symbolic Compiler & Myelin Runtime Interface
=============================================================================
Usage:
  synax compile <file.sx> [--yeniden] [--n 4000000]   Compile, verify (19 suites) & cache
  synax run <file.sx> [--n 32768] [--atim 10]         Compile & stream via Axon hot-swap
  synax check <file.sx>                               Inspect IR, AST & Dual-Reference check
  synax test                                          Run full differential & compiler suites
  synax myelin                                        Run Builtin Ranvier Myelin demo
  synax stream [seconds]                              Run 100 kS/s Biomedical Stream demo
  synax benchmark                                     Run Hardware Axon/Tycon Evolution Matrix
  synax status                                        Inspect hardware & signed Myelin cache
  synax version                                       Show version & repository details
=============================================================================
"""

import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time
from array import array
from pathlib import Path

from synax_ir import parse_sx
from synax_security import SynaxSecurityGuard
from synax_verifier import (
    DualReferenceMismatchError,
    LoadedKernel,
    build_adversarial_suites,
    verify_dual_reference_offline,
)
from synaxc import SHARED_CFLAGS_O0_REF, SynaxCodeGenerator, SynaxCompiler, get_hafiza_root

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def print_banner():
    banner = """
   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██╗  ██╗
   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗╚██╗██╔╝
   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║ ╚███╔╝ 
   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║ ██╔██╗ 
   ███████║   ██║   ██║ ╚████║██║  ██║██╔╝ ██╗
   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝
   Neuro-Symbolic Compiler & Adaptive Myelin Runtime (v0.5-Unified)
   GitHub: https://github.com/ofaemd-creator/synax | Cloud IDE: https://synaxcode.online
"""
    print(banner)


def cmd_help():
    print_banner()
    print(
        """KOMUTLAR:
  synax compile <dosya.sx> [--yeniden] : .sx dosyasını IR'a indirger, 19 test kümesiyle doğrular ve derler
  synax run <dosya.sx> [--yeniden]     : .sx dosyasını derler ve SynaxAxonChannel fonksiyon işaretçisi takasıyla yürütür
  synax check <dosya.sx>               : .sx sözdizimi, kanonik IR, C11/NEON çıktısı ve çift-referans denetimini yapar
  synax test                           : Tüm diferansiyel denklik ve birleşik derleyici regresyon testlerini koşar
  synax myelin                         : Yerleşik Ranvier Düğümleri ve Miyelin JIT deneyini yürütür
  synax stream [süre_sn]               : 100,000 örnek/sn Biyomedikal Hemodinamik sinyal akışını başlatır
  synax benchmark                      : Apple Silicon donanım evrim matrisini çalıştırır
  synax status                         : Donanım profilini ve kriptografik Miyelin hafıza önbelleğini listeler
  synax version                        : Sürüm, lisans (Apache-2.0) ve ekosistem bilgilerini gösterir
"""
    )


def cmd_version():
    print("SYNAX Unified Compiler & Runtime v0.5.0 (Apache License 2.0)")
    print("Resmi GitHub Deposu : https://github.com/ofaemd-creator/synax")
    print("Egemen Git Sunucusu : https://synaxcode.org/git/synax.git")
    print("Cloud Studio IDE    : https://synaxcode.online")
    print("Teknik Dokümantasyon: https://synaxcode.org")


def cmd_status():
    from synax_core import AxonProfiler

    hw = AxonProfiler.probe()
    print("\n🖥️  AXON DONANIM PROFİLİ:")
    print(f"  • İşlemci / Mimari : {hw.cpu_brand} ({hw.arch}) — {hw.cores} çekirdek ({hw.p_cores}P + {hw.e_cores}E)")
    print(f"  • Bellek / SIMD    : {hw.ram_mb} MB RAM | ARM64 NEON: {'Aktif' if hw.has_neon else 'Yok'}")

    hafiza_root = get_hafiza_root()
    print(f"\n🧠 BİRLEŞİK MİYELİN HAFIZASI ({hafiza_root}):")
    entries = sorted(hafiza_root.glob("*/rapor.json"))
    if entries:
        for rpath in entries:
            ok_sig, _ = SynaxSecurityGuard.verify_json_file(str(rpath))
            try:
                data = json.loads(rpath.read_text(encoding="utf-8"))
                badge = "✓ İMZALI" if ok_sig else "✗ İMZA HATASI"
                print(
                    f"  • [{data.get('ir_hash', '?')}] {data.get('modul', '?'):<28} -> "
                    f"{data.get('kazanan', '?'):<22} ({data.get('kazanan_ms')} ms | "
                    f"Skaler {data.get('hizlanma_skaler')}x, O3 {data.get('hizlanma_clang_o3')}x) [{badge}]"
                )
            except Exception:
                continue
    else:
        print("  (Henüz derlenmiş .sx önbelleği yok. 'synax compile examples/kapili_aktivasyon.sx' çalıştırın)")


def cmd_check(argv):
    ap = argparse.ArgumentParser(prog="synax check")
    ap.add_argument("sx", help="Denetlenecek .sx dosyası")
    args = ap.parse_args(argv)

    ir = parse_sx(args.sx)
    p0, p1 = ir.param_names
    print("=" * 72)
    print(f"🔍 SYNAX STATİK & SEMANTİK DENETİM — {ir.name} [IR #{ir.ir_hash}]")
    print("=" * 72)
    print(f"  • Kaynak Biçimi   : {ir.syntax_format} (v{ir.version})")
    print(f"  • Parametreler    : ({p0}: tensor<f32>, {p1}: tensor<f32>) -> tensor<f32>")
    print(f"  • Niyet           : {ir.intent_text}")
    print(f"  • Kanonik Formül  : out = {ir.expr.to_human_formula(p0, p1)}")
    print(f"  • IMMUNE Politikası: {json.dumps(ir.safety.to_dict(), ensure_ascii=False)}")
    print(f"  • C11 Skaler İfade: {ir.expr.to_c_scalar(var_a='ai', var_b='bi')}")
    if ir.expr.can_use_pure_neon_intrinsics():
        print(f"  • ARM64 NEON SIMD : {ir.expr.to_neon_f32x4()}")
    else:
        print("  • ARM64 NEON SIMD : Hibrit 4-yollu vektör boru hattı")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ref_c = SynaxCodeGenerator.emit_scalar_variant(
            ir, pragma_line="#pragma clang loop vectorize(disable) unroll(disable)"
        )
        ok, err = SynaxCompiler._compile_dylib(ref_c, tmp / "ref.c", tmp / "ref.dylib", SHARED_CFLAGS_O0_REF)
        if not ok:
            print(f"\n✗ Referans derleme hatası: {err}")
            sys.exit(1)
        ref_k = LoadedKernel(str(tmp / "ref.dylib"), name="check_ref")
        suites = build_adversarial_suites(input_abs_bound=ir.safety.input_abs_bound)
        rep = verify_dual_reference_offline(ir, ref_k, suites)
        print(
            f"\n  ✓ ÇİFT-REFERANS DENETİMİ GEÇTİ: Python IEEE-754 AST == C11 (-O0) "
            f"({rep.suites_tested} küme, {rep.total_elements} eleman, maks göreli fark: {rep.max_abs_diff:.2e})"
        )
    print("=" * 72)


def cmd_compile(argv):
    ap = argparse.ArgumentParser(prog="synax compile")
    ap.add_argument("sx", help="Derlenecek .sx dosyası veya ifade")
    ap.add_argument("--yeniden", action="store_true", help="Önbelleği yok say ve yeniden doğrula")
    ap.add_argument("--n", type=int, default=4_000_000, help="Benchmark eleman sayısı")
    ap.add_argument("--tekrar", type=int, default=15, help="Medyan tekrar sayısı")
    ap.add_argument("--nesil", type=int, default=0, help="İsteğe bağlı LLM mutasyon nesli")
    ap.add_argument("--llm", choices=["off", "claude"], default="off", help="LLM sağlayıcısı")
    args = ap.parse_args(argv)

    compiler = SynaxCompiler()
    compiler.compile(
        args.sx,
        force_rebuild=args.yeniden,
        bench_n=args.n,
        bench_repeats=args.tekrar,
        evolve_generations=args.nesil,
        llm_provider=args.llm,
        verbose=True,
    )


def cmd_run(argv):
    ap = argparse.ArgumentParser(prog="synax run")
    ap.add_argument("sx", help="Çalıştırılacak .sx dosyası veya ifade")
    ap.add_argument("--yeniden", action="store_true", help="Önbelleği yok say")
    ap.add_argument("--n", type=int, default=32768, help="Her aksiyon potansiyeli atımındaki örnek sayısı")
    ap.add_argument("--atim", type=int, default=10, help="İletilecek sinyal paketi (burst) sayısı")
    ap.add_argument("--esik", type=int, default=4, help="Otonom miyelinleşme eşiği (atım sayısı)")
    ap.add_argument("--bozuk", action="store_true", help="Bozuk NaN/Inf sensör darbeleri enjekte et")
    args = ap.parse_args(argv)

    compiler = SynaxCompiler()
    comp = compiler.compile(args.sx, force_rebuild=args.yeniden, verbose=True)
    axon = comp.create_axon_channel(myelin_threshold=args.esik, fixed_length=args.n)

    print("\n" + "=" * 72)
    print(f"🧬 CANLI AKSON İLETİMİ & FONKSİYON İŞARETÇİSİ HOT-SWAP ({comp.ir.name})")
    print(f"   Miyelin Eşiği: {args.esik}. atımda baseline_o1 -> {comp.winner_name}")
    print("=" * 72)

    rng = random.Random(42)
    base_a = array("f", [80.0 + 25.0 * math.sin(i * 0.01) + rng.gauss(0.0, 0.3) for i in range(args.n)])
    base_b = array("f", [10.0 + 4.0 * math.cos(i * 0.01) for i in range(args.n)])

    inject_corrupt = args.bozuk or comp.ir.safety.nonfinite_mode in ("heal_inputs", "zero_output")

    for step in range(1, args.atim + 1):
        sig_a = array("f", base_a)
        sig_b = array("f", base_b)
        prev_healed = axon.get_stats().healed_anomalies_count

        if inject_corrupt and step in (2, args.esik + 2) and args.n >= 8:
            sig_a[1] = float("nan")
            sig_a[2] = float("inf")
            sig_b[3] = float("-inf")

        out, tel = axon.transmit(sig_a, sig_b)
        step_healed = tel["healed_anomalies"] - prev_healed

        if comp.ir.safety.nonfinite_mode == "reject" and step_healed > 0:
            raise RuntimeError(
                f"[IMMUNE REJECT] Atım #{step:02d}: safety {{ nonfinite = reject }} politikası "
                f"{step_healed} adet NaN/Inf girdi tespit etti ve yürütmeyi durdurdu!"
            )

        if tel["state_code"] == 2:
            mode_str = f"MYELINATED -> {tel['active_kernel']}"
            lat_str = f"{tel['myelinated_avg_us']:6.1f} µs ({tel['velocity_ratio']:.2f}x)"
        else:
            mode_str = "UNMYELINATED -> baseline_o1"
            lat_str = f"{tel['unmyelinated_avg_us']:6.1f} µs"

        sample_preview = f"out[0]={out[0]:.3f}" if len(out) > 0 else "out=[]"
        print(
            f"  Atım #{step:02d} | [{mode_str:<40}] | {lat_str:<18} | "
            f"Anomali: +{step_healed} | {sample_preview}"
        )


def cmd_test():
    suite_files = [
        os.path.join(BASE_DIR, "test_differential_myelin.py"),
        os.path.join(BASE_DIR, "test_unified_compiler.py"),
    ]
    for sf in suite_files:
        if os.path.exists(sf):
            rc = subprocess.call([sys.executable, sf])
            if rc != 0:
                sys.exit(rc)


def main():
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    subcmd = sys.argv[1].lower()
    rest = sys.argv[2:]

    try:
        if subcmd in ("-h", "--help", "help"):
            cmd_help()
        elif subcmd in ("-v", "--version", "version"):
            cmd_version()
        elif subcmd == "status":
            cmd_status()
        elif subcmd == "check":
            cmd_check(rest)
        elif subcmd == "compile":
            cmd_compile(rest)
        elif subcmd == "run":
            cmd_run(rest)
        elif subcmd == "test":
            cmd_test()
        elif subcmd == "myelin":
            from synax_myelin import run_myelin_verification_demo
            run_myelin_verification_demo()
        elif subcmd in ("stream", "live"):
            from synax_biomedical_stream import run_biomedical_streaming_simulation
            dur = float(rest[0]) if rest else 3.0
            run_biomedical_streaming_simulation(duration_seconds=dur)
        elif subcmd == "benchmark":
            import synax_core
            synax_core.run_omega_evolution()
        else:
            # Direct `.sx` file execution shorthand: `synax examples/kapili_aktivasyon.sx`
            if os.path.exists(sys.argv[1]):
                cmd_run(sys.argv[1:])
            else:
                print(f"Bilinmeyen komut veya dosya: {sys.argv[1]}")
                cmd_help()
                sys.exit(1)
    except DualReferenceMismatchError as exc:
        print(f"\n✗ [SEMANTİK BELİRSİZLİK] {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"\n✗ [SYNAX HATA] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
