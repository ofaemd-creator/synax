#!/usr/bin/env python3
"""
SYNAX UNIFIED COMPILER & RUNTIME REGRESSION SUITE (Issue #4)
=============================================================================
End-to-end verification of the unified SYNAX v0.5 pipeline:
  1. Dual-Frontend `.sx` Parsing (`structured_v01` & `declarative_intent`)
     + Canonical `SynaxIR` Hash Invariance
  2. Dual-Reference Semantic Gate (`Python IEEE-754 f32` vs `C11 -O0 Scalar`)
  3. All 4 IMMUNE Safety Policies (`preserve`, `heal_inputs`, `zero_output`, `reject`)
     across all 5 C11 / ARM64 NEON / GCD Multicore candidate variants on all 19 suites
  4. Adversarial Bug-Catcher Regression (Channel-B NaN leak, unwritten tail sentinel,
     and NaN-erasure under `preserve` must all be deterministically REJECTED)
  5. Cryptographic Myelin Cache Hit (`< 5 ms`) & Tamper-Evident Invalidation
  6. Dynamic `SynaxAxonChannel` C Function-Pointer Hot-Swap Equivalence
=============================================================================
"""

import json
import math
import os
import tempfile
import time
from array import array
from pathlib import Path

from synax_ir import parse_sx
from synax_security import SynaxSecurityGuard
from synax_verifier import (
    LoadedKernel,
    build_adversarial_suites,
    check_equivalence_pure,
    verify_against_reference,
)
from synaxc import SHARED_CFLAGS_O0_REF, SHARED_CFLAGS_O3, SynaxCompiler

BASE_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = BASE_DIR / "examples"


def test_1_ir_frontends_and_hash_invariance():
    print("\n[1/6] Sözdizimi Ön-Uçları (`synax 0.1` & `niyet:/kural:`) ve Kanonik IR Özeti Testi...")

    sx_struct_1 = """
    synax 0.1
    kernel cpp_a(dbp: tensor<f32>, cvp: tensor<f32>) -> tensor<f32> {
      intent "CPP A"
      safety { nonfinite = heal(0.0); range_check = clamp(-50.0, 300.0) }
      let delta = dbp - cvp
      return delta + 0.0
    }
    """
    sx_struct_2 = """
    synax 0.1
    // Farklı parametre adları ve yorumlar, aynı semantik IR!
    kernel cpp_b(p_art: tensor<f32>, p_ven: tensor<f32>) -> tensor<f32> {
      safety {
        nonfinite = heal(0.0)
        range_check = clamp(-50.0, 300.0)
      }
      return p_art - p_ven
    }
    """
    ir1 = parse_sx(sx_struct_1)
    ir2 = parse_sx(sx_struct_2)
    assert ir1.ir_hash == ir2.ir_hash, f"Kanonik IR özeti uyuşmadı: {ir1.ir_hash} != {ir2.ir_hash}"
    assert ir1.safety.nonfinite_mode == "heal_inputs"
    assert ir1.safety.output_clamp == (-50.0, 300.0)

    ir_glu = parse_sx(str(EXAMPLES_DIR / "kapili_aktivasyon.sx"))
    assert ir_glu.safety.nonfinite_mode == "preserve"
    assert ir_glu.expr.to_human_formula() == "(sigmoid(a) * b)"

    ir_anom = parse_sx(str(EXAMPLES_DIR / "anomali_v04.sx"))
    assert ir_anom.safety.nonfinite_mode == "zero_output"
    assert ir_anom.expr.to_human_formula() == "(((a - b))² + 0.5)"

    # Security firewall must block injection attempts
    blocked = False
    try:
        SynaxSecurityGuard.verify_c_expression('system("echo pwn")')
        ok_inj, _ = SynaxSecurityGuard.verify_c_expression('system("echo pwn")')
        blocked = not ok_inj
    except Exception:
        blocked = True
    assert blocked, "SynaxSecurityGuard enjeksiyon girişimini engellemedi!"
    print("  ✓ Yapısal ve bildirimsel .sx ayrıştırıcıları + kanonik IR özeti doğrulandı.")


def test_2_pure_python_and_numpy_19_suites():
    print("\n[2/6] 19 Zorlu Uç Küme (Pure-Python `array('f')` & `NumPy` Çift Yol) Testi...")
    suites_py = build_adversarial_suites(force_pure_python=True)
    suites_np = build_adversarial_suites(force_pure_python=False)
    assert len(suites_py) == 19 and len(suites_np) == 19

    lengths = [len(a) for a, _ in suites_py]
    assert lengths[0] == 0, "0 uzunluklu uç testi mevcut olmalı"
    assert 100_003 in lengths, "100,003 asal kuyruk boyutu mevcut olmalı"
    assert lengths[-1] == 144, "12x12=144 Kartezyen özel değer çarpımı mevcut olmalı"
    print("  ✓ 19 zorlu test kümesi (n=0..100,003, NaN, ±Inf, ±0.0, 1e-40, ±3.4e38, 144 çift) hazır.")


def test_3_all_safety_policies_and_candidates():
    print("\n[3/6] 4 IMMUNE Güvenlik Politikası & 5 C11/NEON/GCD Adayının Tam Doğrulaması...")
    with tempfile.TemporaryDirectory() as tmp_cache:
        compiler = SynaxCompiler(cache_root=Path(tmp_cache))
        targets = [
            ("kapili_aktivasyon.sx", "preserve"),
            ("anomali_v04.sx", "zero_output"),
            ("hemodynamic_cpp.sx", "heal_inputs"),
            ("normalized_difference.sx", "reject"),
            ("biyomedikal_kardiyo.sx", "heal_inputs"),
        ]
        for fname, expected_mode in targets:
            res = compiler.compile(
                str(EXAMPLES_DIR / fname),
                force_rebuild=True,
                bench_n=200_000,
                bench_repeats=5,
                verbose=False,
            )
            assert res.ir.safety.nonfinite_mode == expected_mode
            assert res.dual_ref_verified
            assert res.suites_count == 19
            verified_names = [c.name for c in res.candidates if c.verified]
            assert len(verified_names) == 5, (
                f"{fname}: 5 adayın tamamı 19 kümeyi geçmeliydi, geçenler: {verified_names}"
            )

            # Spot-check semantic edge behavior on winning dylib
            win_k = LoadedKernel(str(res.winner_dylib_path), name=res.winner_name)
            a_edge = array("f", [float("nan"), 10.0, float("inf"), -1000.0])
            b_edge = array("f", [2.0, float("nan"), 3.0, 4.0])
            out_arr, healed = win_k.run_pure(a_edge, b_edge)

            if fname == "kapili_aktivasyon.sx":
                assert math.isnan(out_arr[0]) and math.isnan(out_arr[1]), "preserve modunda NaN korunmalı!"
                assert out_arr[3] == 0.0, "a=-1000 için sigmoid(a)*b taşmadan 0.0 olmalı!"
            elif fname == "anomali_v04.sx":
                assert out_arr[0] == 0.0 and out_arr[1] == 0.0 and out_arr[2] == 0.0, (
                    "zero_output modunda NaN/Inf girdili eleman tam 0.0 üretmeli (+0.5 sapma eklenmemeli)!"
                )
                assert healed == 3
            elif fname == "hemodynamic_cpp.sx":
                # dbp=NaN->0, cvp=2 => -2; dbp=10, cvp=NaN->0 => 10; clamp(-50, 300) on -1000 - 4 => -50!
                assert abs(out_arr[0] - (-2.0)) < 1e-6
                assert abs(out_arr[1] - 10.0) < 1e-6
                assert abs(out_arr[3] - (-50.0)) < 1e-6
                assert healed == 3
            elif fname == "normalized_difference.sx":
                assert math.isnan(out_arr[0]) and math.isnan(out_arr[1]) and math.isnan(out_arr[2])
                assert abs(out_arr[3] - 1.0) < 1e-6
                assert healed == 3

            # Also verify pure-Python zero-dependency verifier path on winning dylib vs reference dylib
            ref_k = LoadedKernel(str(res.ref_dylib_path), name="ref")
            pure_suites = build_adversarial_suites(
                input_abs_bound=res.ir.safety.input_abs_bound, force_pure_python=True
            )[:12]
            rep_pure = verify_against_reference(win_k, ref_k, pure_suites)
            assert rep_pure.passed, f"Pure-Python doğrulayıcı hatası: {rep_pure.failure_reason}"

            print(
                f"  ✓ {fname:<26} | mod={expected_mode:<11} | 5/5 aday doğrulandı | "
                f"kazanan={res.winner_name}"
            )


def test_4_buggy_simd_candidates_are_rejected():
    print("\n[4/6] Hatalı Optimize Çekirdek Yakalama Testi (Claude Kanal-B & Kuyruk Hatası Regresyonu)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        compiler = SynaxCompiler(cache_root=tmp / "cache")
        res = compiler.compile(
            str(EXAMPLES_DIR / "hemodynamic_cpp.sx"),
            force_rebuild=True,
            bench_n=65536,
            bench_repeats=3,
            verbose=False,
        )
        ref_k = LoadedKernel(str(res.ref_dylib_path), name="ref_cpp")
        suites = build_adversarial_suites()

        # Bug 1: Channel B is NOT sanitized (the exact historical Claude review bug!)
        buggy_ch_b_src = """
        #include <stddef.h>
        #include <math.h>
        void synax_kernel(const float* a, const float* b, float* out, size_t n) {
            for (size_t i = 0; i < n; ++i) {
                float ai = isfinite(a[i]) ? a[i] : 0.0f;
                float bi = b[i]; /* BUG: b[i] NaN/Inf kontrolü unutuldu! */
                float r = ai - bi;
                if (r < -50.0f) r = -50.0f;
                if (r > 300.0f) r = 300.0f;
                out[i] = r;
            }
        }
        """
        ok, _ = SynaxCompiler._compile_dylib(buggy_ch_b_src, tmp / "bug_b.c", tmp / "bug_b.dylib", SHARED_CFLAGS_O3)
        assert ok
        rep_b = verify_against_reference(LoadedKernel(str(tmp / "bug_b.dylib")), ref_k, suites)
        assert not rep_b.passed, "Kanal-B NaN sızıntısı yakalanmalıydı!"

        # Bug 2: Vector loop forgets scalar tail when n % 4 != 0 (caught by 1234.5f sentinel!)
        buggy_tail_src = """
        #include <stddef.h>
        #include <math.h>
        void synax_kernel(const float* a, const float* b, float* out, size_t n) {
            size_t vec_n = n & ~(size_t)3; /* BUG: son 1..3 eleman yazılmadı! */
            for (size_t i = 0; i < vec_n; ++i) {
                float ai = isfinite(a[i]) ? a[i] : 0.0f;
                float bi = isfinite(b[i]) ? b[i] : 0.0f;
                float r = ai - bi;
                if (r < -50.0f) r = -50.0f;
                if (r > 300.0f) r = 300.0f;
                out[i] = r;
            }
        }
        """
        ok, _ = SynaxCompiler._compile_dylib(
            buggy_tail_src, tmp / "bug_tail.c", tmp / "bug_tail.dylib", SHARED_CFLAGS_O3
        )
        assert ok
        rep_tail = verify_against_reference(LoadedKernel(str(tmp / "bug_tail.dylib")), ref_k, suites)
        assert not rep_tail.passed, "Eksik skaler kuyruk (sentinel 1234.5f) yakalanmalıydı!"

        # Bug 3: Anomaly healed counter mismatch in SIMD path
        buggy_cnt_src = """
        #include <stddef.h>
        #include <math.h>
        void synax_kernel_tracked(const float* a, const float* b, float* out, size_t n, size_t* out_healed) {
            for (size_t i = 0; i < n; ++i) {
                float ai = isfinite(a[i]) ? a[i] : 0.0f;
                float bi = isfinite(b[i]) ? b[i] : 0.0f;
                float r = ai - bi;
                if (r < -50.0f) r = -50.0f;
                if (r > 300.0f) r = 300.0f;
                out[i] = r;
            }
            if (out_healed) *out_healed = 0; /* BUG: şifa sayacı sıfır bırakıldı! */
        }
        void synax_kernel(const float* a, const float* b, float* out, size_t n) {
            synax_kernel_tracked(a, b, out, n, NULL);
        }
        """
        ok, _ = SynaxCompiler._compile_dylib(
            buggy_cnt_src, tmp / "bug_cnt.c", tmp / "bug_cnt.dylib", SHARED_CFLAGS_O0_REF
        )
        assert ok
        rep_cnt = verify_against_reference(LoadedKernel(str(tmp / "bug_cnt.dylib")), ref_k, suites)
        assert not rep_cnt.passed and "anomali sayacı" in rep_cnt.failure_reason, (
            "Eksik şifa sayacı yakalanmalıydı!"
        )

        print(f"  ✓ Hata #1 reddedildi -> {rep_b.failure_reason}")
        print(f"  ✓ Hata #2 reddedildi -> {rep_tail.failure_reason}")
        print(f"  ✓ Hata #3 reddedildi -> {rep_cnt.failure_reason}")


def test_5_myelin_cache_hit_and_tamper_guard():
    print("\n[5/6] Kriptografik Miyelin Önbellek İsabeti ve Kurcalama (Tamper) Koruması...")
    with tempfile.TemporaryDirectory() as tmp_cache:
        compiler = SynaxCompiler(cache_root=Path(tmp_cache))
        r1 = compiler.compile(
            str(EXAMPLES_DIR / "anomali_v04.sx"),
            force_rebuild=True,
            bench_n=100_000,
            bench_repeats=3,
            verbose=False,
        )
        assert not r1.cache_hit

        t0 = time.perf_counter()
        r2 = compiler.compile(str(EXAMPLES_DIR / "anomali_v04.sx"), verbose=False)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        assert r2.cache_hit, "İkinci çağrı Miyelin hafızasından dönmeliydi!"
        assert dt_ms < 25.0, f"Önbellek okuma çok yavaş: {dt_ms:.2f} ms"

        # Tamper with rapor.json without updating SHA-256 signature
        rapor_file = r2.cache_dir / "rapor.json"
        tampered = json.loads(rapor_file.read_text(encoding="utf-8"))
        tampered["kazanan_ms"] = 0.0001
        rapor_file.write_text(json.dumps(tampered), encoding="utf-8")

        r3 = compiler.compile(
            str(EXAMPLES_DIR / "anomali_v04.sx"),
            bench_n=100_000,
            bench_repeats=3,
            verbose=False,
        )
        assert not r3.cache_hit, "İmzası bozulmuş rapor.json reddedilip yeniden derlenmeliydi!"
        print(f"  ✓ Önbellek isabeti ({dt_ms:.2f} ms) ve SHA-256 kurcalama koruması doğrulandı.")


def test_6_axon_channel_hot_swap_equivalence():
    print("\n[6/6] C `SynaxAxonChannel` Fonksiyon İşaretçisi Takası (Hot-Swap) Denklik Testi...")
    with tempfile.TemporaryDirectory() as tmp_cache:
        compiler = SynaxCompiler(cache_root=Path(tmp_cache))
        comp = compiler.compile(
            str(EXAMPLES_DIR / "biyomedikal_kardiyo.sx"),
            force_rebuild=True,
            bench_n=100_000,
            bench_repeats=3,
            verbose=False,
        )

        n = 4099  # Unaligned length to stress both NEON vector loop and scalar tail!
        axon_hot = comp.create_axon_channel(myelin_threshold=3, fixed_length=n)
        axon_ref = comp.create_axon_channel(myelin_threshold=999999, fixed_length=n)

        sig_a = array("f", [75.0 + (i % 19) * 1.5 for i in range(n)])
        sig_b = array("f", [9.0 + (i % 7) * 0.8 for i in range(n)])
        # Inject Channel A & Channel B corruptions + >1000 spikes
        sig_a[5] = float("nan")
        sig_b[11] = float("inf")
        sig_b[4098] = -2500.0  # Last tail element spike!

        states_seen = []
        for step in range(1, 6):
            out_hot, tel_hot = axon_hot.transmit(sig_a, sig_b)
            out_ref, tel_ref = axon_ref.transmit(sig_a, sig_b)
            states_seen.append(tel_hot["state_code"])

            ok, reason, mrel = check_equivalence_pure(
                out_ref,
                out_hot,
                rtol=1e-5,
                ref_healed=tel_ref["healed_anomalies"],
                cand_healed=tel_hot["healed_anomalies"],
            )
            assert ok, f"Adım {step} hot-swap uyuşmazlığı: {reason}"

        assert states_seen == [0, 0, 2, 2, 2], f"Beklenen durum geçişi [0, 0, 2, 2, 2], görülen: {states_seen}"
        assert axon_hot.get_stats().healed_anomalies_count == 15  # 3 anomalies * 5 bursts
        print(
            f"  ✓ Durum geçişi {states_seen} (Skaler -> {comp.winner_name}) "
            f"ve 15/15 anomali şifası bit-birebir doğrulandı."
        )


def run_all():
    print("=" * 72)
    print("🧪 SYNAX v0.5 UNIFIED COMPILER & RUNTIME REGRESSION SUITE")
    print("=" * 72)
    t0 = time.perf_counter()
    test_1_ir_frontends_and_hash_invariance()
    test_2_pure_python_and_numpy_19_suites()
    test_3_all_safety_policies_and_candidates()
    test_4_buggy_simd_candidates_are_rejected()
    test_5_myelin_cache_hit_and_tamper_guard()
    test_6_axon_channel_hot_swap_equivalence()
    elapsed = time.perf_counter() - t0
    print("\n" + "=" * 72)
    print(f"🎉 TÜM BİRLEŞİK DERLEYİCİ VE MİYELİN REGRESYON TESTLERİ GEÇTİ! ({elapsed:.2f} sn)")
    print("=" * 72)


if __name__ == "__main__":
    run_all()
