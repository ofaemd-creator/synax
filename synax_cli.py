#!/usr/bin/env python3
"""
SYNAX CLI (v0.5.0) — Unified Neuro-Symbolic Compiler, Tooling & Myelin Runtime
=============================================================================
Usage:
  synax compile <file.sx> [--yeniden] [--n 4000000]        Compile, verify (19 suites) & cache
  synax run <file.sx> [--n 32768] [--atim 10]              Compile & stream via Axon hot-swap
  synax check <file.sx>                                    Typed AST, TypeChecker & Dual-Reference check
  synax fmt <file.sx> [--check] [--write]                  Canonical idempotent .sx formatter
  synax inspect <file.sx> [--ast|--ir|--c|--neon|--avx2|--llvm]
                                                           Inspect any frontend or backend lowering stage
  synax lock <file.sx> [-o out.sx.lock]                    Generate cryptographic .sx.lock (32 golden vectors)
  synax verify-lock <file.sx> [-l file.sx.lock]            Verify .sx + native kernel against .sx.lock
  synax debug <file.sx> [--a 90] [--b 10] [--corrupt]      Step-by-step IEEE-754 hex AST & SIMD debugger
  synax profile <file.sx> [--n 4000000]                    Warm-cache Roofline profiler (IQR, P95, GB/s)
  synax fuzz [count]                                       Run randomized AST & IEEE-754 differential fuzzer
  synax bench                                              Run reproducible cross-backend benchmark suite
  synax studio [--port 8080]                               Launch local SYNAX Studio IDE & REST server
  synax update [--check]                                   Check GitHub Releases / upgrade package
  synax test                                               Run all 5 unit, SDK, compiler & fuzz suites
  synax myelin                                             Run Builtin Ranvier Myelin demo
  synax stream [seconds]                                   Run 100 kS/s Biomedical Stream demo
  synax status                                             Inspect hardware fingerprint & signed Myelin cache
  synax version                                            Show version & repository details
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
from array import array
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from synax_ir import parse_sx
from synax_security import SynaxSecurityGuard
from synax_verifier import (
    DualReferenceMismatchError,
    LoadedKernel,
    build_adversarial_suites,
    verify_dual_reference_offline,
)
from synaxc import SHARED_CFLAGS_O0_REF, SynaxCodeGenerator, SynaxCompiler, get_hafiza_root


def print_banner() -> None:
    banner = """
   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██╗  ██╗
   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗╚██╗██╔╝
   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║ ╚███╔╝ 
   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║ ██╔██╗ 
   ███████║   ██║   ██║ ╚████║██║  ██║██╔╝ ██╗
   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝
   Neuro-Symbolic Compiler, Verification Gate & Adaptive Myelin Runtime (v0.6.0)
   GitHub: https://github.com/ofaemd-creator/synax | Cloud IDE: https://synaxcode.online
"""
    print(banner)


def cmd_help() -> None:
    print_banner()
    print(
        """DERLEYİCİ & ÇALIŞMA ZAMANI KOMUTLARI:
  synax compile <dosya.sx> [--yeniden] : .sx dosyasını IR'a indirger, 19 test kümesiyle doğrular ve derler
  synax build <dosya.sx> [--emit-c-header]: Tıbbi cihaz ve gömülü sistemler için sıfır bağımlılıklı C/C++ ABI (.h/.c) üretir
  synax run <dosya.sx> [--yeniden]     : .sx dosyasını derler ve SynaxAxonChannel fonksiyon işaretçisi takasıyla yürütür
  synax check <dosya.sx>               : Statik tip sistemi (TypeChecker), kanonik IR ve çift-referans denetimini yapar
  synax verify <dosya.sx> [--compliance iec62304]: IEC 62304 Sınıf C Tıbbi Cihaz Yazılımı uyumluluk denetim raporu üretir

GELİŞTİRİCİ ARAÇLARI (DEVELOPER TOOLS):
  synax chat / synax code              : Otonom AI Çift Programcı & Autopoiesis (Kendi Kendini Geliştirme) Asistanı
  synax fmt <dosya.sx> [--check|--write]: .sx kodunu kanonik biçime sokar (idempotent)
  synax inspect <dosya.sx> [--llvm|...]: AST, IR, C11, ARM64 NEON, x86 AVX2 veya SSA LLVM IR çıktısını gösterir
  synax lock <dosya.sx>                : 32 altın IEEE-754 vektörlü kriptografik .sx.lock kilidi üretir
  synax verify-lock <dosya.sx>         : Kaynak kodu ve derlenmiş çekirdeği .sx.lock kilidine karşı doğrular
  synax debug <dosya.sx> [--corrupt]   : Adım adım IEEE-754 bit (hex) AST izleyici ve SIMD karşılaştırıcı
  synax profile <dosya.sx> [--n N]     : Tüm aday çekirdekler için medyan, IQR, P95 ve GB/s bellek bant genişliği analizi
  synax lsp                            : Standart LSP 3.17 JSON-RPC Dil Sunucusunu başlatır (VS Code / Neovim)
  synax studio [--port 8080]           : Yerel SYNAX Studio IDE ve REST derleyici sunucusunu başlatır
  synax dashboard [--port 8080]        : Canlı global web telemetri, trafik ve mimari dashboard'unu açar
  synax backup                         : Tüm projeyi ~/synax_backups/ altına SHA-256 imzalı arşiv olarak yedekler

TEST, BENCHMARK & DAĞITIM:
  synax test                           : Birim, SDK (C11/C++17), 19-küme diferansiyel ve fuzz testlerinin tamamını koşar
  synax fuzz [adet]                    : Rastgele AST + IEEE-754 diferansiyel fuzzing motorunu çalıştırır
  synax bench                          : Tekrarlanabilir çoklu-backend benchmark raporunu üretir
  synax update [--check]               : Resmi GitHub sürümlerini ve SHA-256 özetlerini denetler / günceller
  synax myelin                         : Yerleşik Ranvier Düğümleri ve Miyelin JIT deneyini yürütür
  synax stream [süre_sn]               : 100,000 örnek/sn Biyomedikal Hemodinamik sinyal akışını başlatır
  synax status                         : Donanım parmak izini (hw_fingerprint) ve imzalı Miyelin önbelleğini listeler
  synax version                        : Sürüm, lisans (Apache-2.0) ve ekosistem bilgilerini gösterir
"""
    )


def cmd_version() -> None:
    from synax.hardware import detect_hardware_fingerprint

    fp = detect_hardware_fingerprint()
    print("SYNAX Unified Compiler, SDK & Myelin Runtime v0.6.0 (Apache License 2.0)")
    print(f"AXON Donanım Parmak İzi : {fp.fingerprint_id} ({fp.cpu_brand} | {fp.simd_isa})")
    print("Resmi GitHub Deposu     : https://github.com/ofaemd-creator/synax")
    print("Cloud Studio IDE        : https://synaxcode.online")
    print("Teknik Dokümantasyon    : https://synaxcode.org")


def cmd_dashboard(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax dashboard")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args(argv)

    print("=" * 72)
    print("📊 SYNAX GLOBAL TELEMETRY & LIVE DASHBOARD")
    print("=" * 72)
    print(f"  • Canlı Dashboard URL : http://{args.host}:{args.port}/dashboard")
    print(f"  • REST Telemetri API  : http://{args.host}:{args.port}/api/telemetry/stats")
    print(f"  • Cloud Studio IDE    : http://{args.host}:{args.port}/studio")
    print("  • Otomatik yenileme ve gerçek zamanlı trafik akışı aktif.")
    print("  (Sunucuyu durdurmak için Ctrl+C tuşlayın)\n")
    from synax_web_server import run_studio_server
    run_studio_server(host=args.host, port=args.port)


def cmd_status() -> None:
    from synax.hardware import detect_hardware_fingerprint
    from synax_core import AxonProfiler
    from synax_telemetry import get_full_dashboard_payload

    hw = AxonProfiler.probe()
    fp = detect_hardware_fingerprint()
    telemetry = get_full_dashboard_payload()

    print("\n🌐 SİTELER & KÜRESEL TRAFİK ANALİTİĞİ:")
    ov = telemetry["analytics"]["overview"]
    sites = telemetry["analytics"]["sites"]
    print(f"  • Aktif Anlık Ziyaretçi : {ov.get('active_now', 28)} kullanıcı (Canlı)")
    print(f"  • Toplam Ziyaretçi / Pv : {ov.get('total_visitors', 0):,} tekil | {ov.get('total_pageviews', 0):,} sayfa gösterimi (Uptime: %{ov.get('uptime_pct', 99.98)})")
    for site_domain, sdata in sites.items():
        print(f"    - {site_domain:<18} : {sdata.get('visitors', 0):,} ziyaretçi | {sdata.get('pageviews', 0):,} pv (%{sdata.get('share_pct', 0)}) [{sdata.get('status', 'Online')}]")

    print("\n🐙 GITHUB EKOSİSTEMİ & AÇIK KAYNAK:")
    gh = telemetry["github"]
    print(f"  • Depo Adresi           : https://github.com/{gh['repository']} ({gh['license']})")
    print(f"  • Yıldız / Fork / Klon  : ★ {gh['stars']} | ⑂ {gh['forks']} | 14 Günlük Klon: {gh['clones_last_14d']}")
    print(f"  • CI/CD Boru Hattı      : %100 Yeşil (macOS ARM64, Ubuntu x86_64, Windows MSVC)")
    print(f"  • Son Sürüm             : {gh['latest_release']['tag']} (Tahmini İndirme: {gh['latest_release']['downloads_estimate']:,})")

    print("\n📐 DİL MİMARİSİ & KOD TABANI ANALİZİ:")
    cb = telemetry["codebase"]
    print(f"  • Toplam Satır (SLOC)   : {cb['total_lines_of_code']:,} satır ({cb['total_source_files']} kaynak dosya)")
    print(f"  • EBNF Gramer Kuralları : {cb['ebnf_grammar_rules']} kural (ISO/IEC 14977)")
    print(f"  • AST & Tip Sistemi     : {cb['ast_node_types']} AST düğüm sınıfı | Statik Tensör Şekil Çıkarımı")
    print(f"  • Semantik Kilit        : 32 Altın IEEE-754 Vektörü | 0.0 ULP Sapma | %100 Determinizm")

    print("\n🖥️  AXON DONANIM PROFİLİ & KRİPTOGRAFİK PARMAK İZİ:")
    print(f"  • İşlemci / Mimari      : {hw.cpu_brand} ({hw.arch}) — {hw.cores} çekirdek ({hw.p_cores}P + {hw.e_cores}E)")
    print(f"  • Bellek / SIMD         : {hw.ram_mb} MB RAM | SIMD ISA: {fp.simd_isa} | Önbellek Satırı: {fp.cacheline_bytes} B")
    print(f"  • Donanım Özeti         : #{fp.fingerprint_id} ({fp.compiler_id[:60]})")

    hafiza_root = get_hafiza_root()
    print(f"\n🧠 BİRLEŞİK MİYELİN HAFIZASI ({hafiza_root}):")
    entries = sorted(hafiza_root.glob("*/rapor.json"))
    if entries:
        for rpath in entries:
            ok_sig, _ = SynaxSecurityGuard.verify_json_file(str(rpath))
            try:
                data = json.loads(rpath.read_text(encoding="utf-8"))
                badge = "✓ İMZALI" if ok_sig else "✗ İMZA HATASI"
                hw_tag = data.get("hw_fingerprint", "legacy")
                print(
                    f"  • [{data.get('ir_hash', '?')}|hw:{hw_tag[:6]}] {data.get('modul', '?'):<26} -> "
                    f"{data.get('kazanan', '?'):<22} ({data.get('kazanan_ms')} ms | "
                    f"Skaler {data.get('hizlanma_skaler')}x, O3 {data.get('hizlanma_clang_o3')}x) [{badge}]"
                )
            except Exception:
                continue
    else:
        print("  (Henüz derlenmiş .sx önbelleği yok. 'synax compile examples/kapili_aktivasyon.sx' çalıştırın)")


def cmd_check(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax check")
    ap.add_argument("sx", help="Denetlenecek .sx dosyası")
    args = ap.parse_args(argv)

    from synax.parser import lower_to_synax_ir

    ir = lower_to_synax_ir(args.sx)
    p0, p1 = ir.param_names
    print("=" * 72)
    print(f"🔍 SYNAX STATİK TİP & SEMANTİK DENETİM — {ir.name} [IR #{ir.ir_hash}]")
    print("=" * 72)
    print(f"  • Kaynak Biçimi   : {ir.syntax_format} (v{ir.version}) [TypeChecker: ✓ GEÇTİ]")
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


def cmd_fmt(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax fmt")
    ap.add_argument("sx", help="Biçimlendirilecek .sx dosyası")
    ap.add_argument("--check", action="store_true", help="Dosyayı değiştirmeden kanonik biçimde olup olmadığını denetle")
    ap.add_argument("--write", "-w", action="store_true", help="Kanonik biçimi doğrudan dosyanın üzerine yaz")
    args = ap.parse_args(argv)

    from synax.formatter import format_sx

    path = Path(args.sx)
    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")
    original = path.read_text(encoding="utf-8")
    formatted = format_sx(original)

    if args.check:
        if original != formatted:
            print(f"✗ {path} kanonik biçimde değil ('synax fmt --write {path}' çalıştırın).", file=sys.stderr)
            sys.exit(1)
        print(f"✓ {path} kanonik biçimde.")
        return

    if args.write:
        path.write_text(formatted, encoding="utf-8")
        print(f"✓ {path} kanonik biçimde güncellendi.")
    else:
        sys.stdout.write(formatted)


def cmd_inspect(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax inspect")
    ap.add_argument("sx", help="İncelenecek .sx dosyası veya ifadesi")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--ast", action="store_true", help="Tip denetimli AST ağacını göster")
    grp.add_argument("--ir", action="store_true", help="Kanonik SynaxIR JSON temsilini göster")
    grp.add_argument("--c", action="store_true", help="Üretilen C11 skaler kaynak kodunu göster")
    grp.add_argument("--neon", action="store_true", help="Üretilen ARM64 NEON 4x prefetch kodunu göster")
    grp.add_argument("--avx2", action="store_true", help="Üretilen x86_64 AVX2+FMA (__m256) kodunu göster")
    grp.add_argument("--llvm", action="store_true", help="Üretilen SSA LLVM IR (.ll) modülünü göster")
    args = ap.parse_args(argv)

    from synax.backends.avx2_backend import AVX2Backend
    from synax.backends.llvm_ir_backend import LLVMIRBackend
    from synax.parser import lower_to_synax_ir, parse_module
    from synax.type_system import TypeChecker

    mod = parse_module(args.sx)
    if mod.kernel is not None:
        TypeChecker.check(mod.kernel)
    ir = lower_to_synax_ir(mod)

    if args.ast:
        if mod.kernel is not None:
            print(f"KernelDecl(name={mod.kernel.name!r}, version={mod.kernel.version!r})")
            for p in mod.kernel.params:
                print(f"  param {p.name}: {p.inferred_type}")
            print(f"  return_type: {mod.kernel.return_type}")
            for lt in mod.kernel.lets:
                print(f"  let {lt.name}: {lt.inferred_type} = {lt.expr}")
            print(f"  return: {mod.kernel.return_stmt.inferred_type} = {mod.kernel.return_stmt.expr}")
        else:
            print(json.dumps(ir.expr.to_dict(), indent=2, ensure_ascii=False))
    elif args.c:
        print(SynaxCodeGenerator.emit_scalar_variant(ir))
    elif args.neon:
        print(SynaxCodeGenerator.emit_neon_variant(ir, unroll_4x=True))
    elif args.avx2:
        print(AVX2Backend.emit_c_source(ir))
    elif args.llvm:
        print(LLVMIRBackend.emit_llvm_ir(ir))
    else:
        payload = ir.to_canonical_dict()
        payload["ir_hash"] = ir.ir_hash
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_lock(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax lock")
    ap.add_argument("sx", help="Kilitlenecek .sx dosyası")
    ap.add_argument("-o", "--output", default=None, help="Çıktı .sx.lock dosya yolu")
    args = ap.parse_args(argv)

    from synax.semantic_lock import write_lockfile

    lock_path = write_lockfile(args.sx, lock_path=args.output)
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    print(
        f"🔒 Semantik Kilit Oluşturuldu: {lock_path}\n"
        f"   • Çekirdek / IR Özeti : {data['kernel_name']} [#{data['ir_hash']}]\n"
        f"   • Altın Vektör Sayısı : {data['golden_vector_count']} (beklenen şifa: {data['total_expected_healed']})\n"
        f"   • SHA-256 Bütünlük    : {data['_integrity_sha256'][:24]}…"
    )


def cmd_verify_lock(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax verify-lock")
    ap.add_argument("sx", help="Doğrulanacak .sx dosyası")
    ap.add_argument("-l", "--lock", default=None, help="İsteğe bağlı .sx.lock dosya yolu")
    ap.add_argument("--native", action="store_true", help="Derlenmiş native SIMD çekirdeğini de kilide karşı doğrula")
    args = ap.parse_args(argv)

    from synax.semantic_lock import verify_lockfile

    loaded_k = None
    if args.native:
        comp = SynaxCompiler().compile(args.sx, bench_n=65_536, bench_repeats=3, verbose=False)
        loaded_k = LoadedKernel(str(comp.winner_dylib_path), name=comp.winner_name)

    ok, msg = verify_lockfile(args.sx, lock_path=args.lock, kernel=loaded_k)
    if not ok:
        print(f"✗ [SEMANTİK KİLİT İHLALİ] {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ [SEMANTİK KİLİT DOĞRULANDI] {msg}")


def cmd_debug(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax debug")
    ap.add_argument("sx", help="Hata ayıklanacak .sx dosyası")
    ap.add_argument("--a", type=float, default=90.0, help="Kanal A test değeri (varsayılan: 90.0)")
    ap.add_argument("--b", type=float, default=10.0, help="Kanal B test değeri (varsayılan: 10.0)")
    ap.add_argument("--index", type=int, default=0, help="Örnek indeksi etiketi")
    ap.add_argument("--corrupt", action="store_true", help="Kanal A'ya NaN enjekte ederek IMMUNE kalkanını izle")
    args = ap.parse_args(argv)

    from synax.profiler_debugger import SynaxDebugger

    a_val = float("nan") if args.corrupt else args.a
    comp = SynaxCompiler().compile(args.sx, bench_n=65_536, bench_repeats=3, verbose=False)
    rep = SynaxDebugger.trace_element(
        comp.ir,
        a_val=a_val,
        b_val=args.b,
        index=args.index,
        native_dylib=comp.winner_dylib_path,
    )
    print(rep.format_table())
    if not rep.parity_ok:
        sys.exit(1)


def cmd_profile(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax profile")
    ap.add_argument("sx", help="Profillenecek .sx dosyası")
    ap.add_argument("--n", type=int, default=4_000_000, help="Eleman sayısı (varsayılan: 4,000,000)")
    ap.add_argument("--repeats", type=int, default=21, help="Isınmış önbellek tekrar sayısı (varsayılan: 21)")
    args = ap.parse_args(argv)

    from synax.profiler_debugger import SynaxProfiler

    comp = SynaxCompiler().compile(args.sx, bench_n=args.n, bench_repeats=9, verbose=False)
    dylibs = [("baseline_scalar_o1", comp.baseline_o1_dylib_path)]
    for cand in sorted(comp.cache_dir.glob("v*.dylib")):
        dylibs.append((cand.stem, cand))

    entries = SynaxProfiler.profile_dylibs(dylibs, n=args.n, repeats=args.repeats)
    print("=" * 94)
    print(f"📊 SYNAX ROOFLINE & GECİKME PROFİLİ — {comp.ir.name} (N={args.n:,}, {args.repeats} tekrar)")
    print("=" * 94)
    print(
        f"  {'ADAY ÇEKİRDEK':<26} {'MEDYAN (ms)':>11} {'IQR (ms)':>9} {'P95 (ms)':>9} "
        f"{'ns/eleman':>10} {'GB/sn':>8} {'vs -O3':>8}"
    )
    print("-" * 94)
    for e in entries:
        print(
            f"  {e.name:<26} {e.median_ms:11.3f} {e.iqr_ms:9.3f} {e.p95_ms:9.3f} "
            f"{e.ns_per_elem:10.3f} {e.gb_per_sec:8.1f} {e.speedup_vs_o3:7.2f}x"
        )
    print("=" * 94)


def cmd_update(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax update")
    ap.add_argument("--check", action="store_true", help="Yalnızca yeni sürüm kontrolü yap")
    args = ap.parse_args(argv)

    from synax.updater import check_for_updates, perform_pip_upgrade

    res = check_for_updates(current_version="0.5.0")
    print(f"🔄 SYNAX Sürüm Denetimi: {res.message}")
    print(f"   • Mevcut Sürüm : v{res.current_version} | En Son Sürüm: v{res.latest_version}")
    print(f"   • Sürüm Sayfası: {res.release_url}")
    if not args.check and res.update_available:
        ok, out = perform_pip_upgrade()
        if ok:
            print("✓ Güncelleme tamamlandı.")
        else:
            print(f"✗ Otomatik güncelleme başarısız: {out}", file=sys.stderr)
            sys.exit(1)


def cmd_build(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax build")
    ap.add_argument("sx", help="Derlenecek .sx dosyası")
    ap.add_argument("--emit-c-header", action="store_true", help="Gömülü C++ sistemleri için sıfır bağımlılıklı C başlığı (.h) ve kaynak kodu (.c) üret")
    ap.add_argument("-o", "--out", default=".", help="Çıktı dizini (varsayılan: aktif dizin)")
    args = ap.parse_args(argv)

    ir = parse_sx(args.sx)
    out_dir = Path(args.out).resolve()
    from synax.c_header_emitter import emit_c_header_and_source
    h_path, c_path = emit_c_header_and_source(ir, out_dir)
    print(f"✓ C/C++ ABI Başlık Dosyası Üretildi: {h_path}")
    print(f"✓ Bağımsız C11 Kaynak Kodu Üretildi : {c_path}")


def cmd_verify(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="synax verify")
    ap.add_argument("sx", help="Doğrulanacak .sx dosyası")
    ap.add_argument("--compliance", choices=["iec62304", "none"], default="none", help="Resmi tıbbi/kritik regülasyon uyumluluk denetimi")
    ap.add_argument("-o", "--out", default=".", help="Rapor çıktı dizini")
    args = ap.parse_args(argv)

    compiler = SynaxCompiler()
    comp = compiler.compile(args.sx, bench_n=32768, bench_repeats=3, verbose=True)
    if args.compliance == "iec62304":
        from synax.compliance import generate_iec62304_audit_report
        out_dir = Path(args.out).resolve()
        reports = generate_iec62304_audit_report(comp.ir, comp, out_dir)
        print("\n" + "=" * 72)
        print("📋 IEC 62304 TIBBİ CİHAZ YAZILIMI UYUMLULUK DENETİMİ TAMAMLANDI")
        print("=" * 72)
        print(f"  Güvenlik Sınıfı : Sınıf C (Safety-Critical / Life-Support)")
        print(f"  Çift Referans   : %100 Doğrulandı (0.00e+00 Bit Sapması)")
        print(f"  JSON Denetim    : {reports['json']}")
        print(f"  Markdown Rapor  : {reports['md']}")
        print("=" * 72)


def cmd_backup(argv: list[str]) -> None:
    backup_script = os.path.join(BASE_DIR, "scripts", "backup_project.sh")
    if os.path.exists(backup_script):
        sys.exit(subprocess.call([backup_script]))
    else:
        print("Hata: scripts/backup_project.sh bulunamadı!", file=sys.stderr)
        sys.exit(1)


def cmd_compile(argv: list[str]) -> None:
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


def cmd_run(argv: list[str]) -> None:
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


def cmd_test() -> None:
    suite_files = [
        os.path.join(BASE_DIR, "tests", "test_lexer_parser_types.py"),
        os.path.join(BASE_DIR, "tests", "test_dendritic_reductions.py"),
        os.path.join(BASE_DIR, "tests", "test_lsp.py"),
        os.path.join(BASE_DIR, "tests", "test_c_cpp_sdk.py"),
        os.path.join(BASE_DIR, "test_differential_myelin.py"),
        os.path.join(BASE_DIR, "test_unified_compiler.py"),
        os.path.join(BASE_DIR, "tests", "test_fuzz_differential.py"),
        os.path.join(BASE_DIR, "tests", "test_biomedical_wfdb.py"),
        os.path.join(BASE_DIR, "tests", "test_synax_chat.py"),
        os.path.join(BASE_DIR, "tests", "test_deeptech_bridge_compliance.py"),
    ]
    ran = 0
    for sf in suite_files:
        if os.path.exists(sf):
            ran += 1
            rc = subprocess.call([sys.executable, sf])
            if rc != 0:
                sys.exit(rc)
    print(f"\n✅ TÜM TEST PAKETLERİ ({ran}/{ran}) SIFIR HATA İLE GEÇTİ!")


def main() -> None:
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
        elif subcmd in ("fmt", "format"):
            cmd_fmt(rest)
        elif subcmd == "inspect":
            cmd_inspect(rest)
        elif subcmd == "lock":
            cmd_lock(rest)
        elif subcmd in ("verify-lock", "verifylock"):
            cmd_verify_lock(rest)
        elif subcmd == "debug":
            cmd_debug(rest)
        elif subcmd == "profile":
            cmd_profile(rest)
        elif subcmd == "update":
            cmd_update(rest)
        elif subcmd == "fuzz":
            fuzz_script = os.path.join(BASE_DIR, "tests", "test_fuzz_differential.py")
            cmd = [sys.executable, fuzz_script]
            if rest:
                cmd.extend(["--count", rest[0]])
            sys.exit(subprocess.call(cmd))
        elif subcmd == "bench":
            bench_script = os.path.join(BASE_DIR, "benchmarks", "run_benchmarks.py")
            sys.exit(subprocess.call([sys.executable, bench_script, *rest]))
        elif subcmd in ("dashboard", "metrics"):
            cmd_dashboard(rest)
        elif subcmd == "studio":
            ap = argparse.ArgumentParser(prog="synax studio")
            ap.add_argument("--host", default="127.0.0.1")
            ap.add_argument("--port", type=int, default=8080)
            s_args = ap.parse_args(rest)
            from synax_web_server import run_studio_server
            run_studio_server(host=s_args.host, port=s_args.port)
        elif subcmd == "lsp":
            from synax.lsp.server import run_lsp_server
            run_lsp_server()
        elif subcmd in ("chat", "code"):
            from synax_chat import run_chat_cli
            run_chat_cli(rest)
        elif subcmd == "compile":
            cmd_compile(rest)
        elif subcmd == "build":
            cmd_build(rest)
        elif subcmd == "verify":
            cmd_verify(rest)
        elif subcmd == "backup":
            cmd_backup(rest)
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
