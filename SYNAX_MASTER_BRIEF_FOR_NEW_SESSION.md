# SYNAX (.sx) PROJE MASTER DEVİR & ÇALIŞMA DOSYASI
**Hedef:** Yeni Antigravity / Claude / GPT Oturumuna Doğrudan Aktarım  
**Sahibi:** Dr. Ömer Faruk Aydın (Acil Tıp Hekimi & Sistem Mimarı)  
**Tarih:** 3 Kasım 2026 | **Sürüm:** v0.5.0 (8-Katmanlı Tam Platform Mimarisi)  
**Resmi Lisans:** Apache License 2.0 (`LICENSE`, `NOTICE`, `TRADEMARKS.md`, `MEDICAL_RESEARCH_DISCLAIMER.md`)

---

## 1. EKOSİSTEM VE CANLI ALTYAPI DURUMU
* **Ana Tanıtım Platformu:** https://synaxcode.com (v0.5.0 — Apache-2.0)
* **Teknik Dokümantasyon & Egemen Git:** https://synaxcode.org (`git clone https://synaxcode.org/git/synax.git`)
* **Cloud Studio IDE:** https://synaxcode.online (Yerel sunucu: `./synax studio`)
* **Resmi GitHub Deposu & Sürümler:** https://github.com/ofaemd-creator/synax (`v0.5.0` etiketli resmi sürüm, macOS/Ubuntu/Windows Cross-Platform CI %100 Yeşil)
* **GitHub Project Panosu:** https://github.com/users/ofaemd-creator/projects/1/views/1

---

## 2. TAMAMLANAN 8 KATMANLI PLATFORM MİMARİSİ (v0.5.0 — DONE)
1. **Katman 1 — Dil & Tip Sistemi (`spec/`, `src/synax/{lexer,parser,type_system}.py`):**
   * ISO/IEC 14977 EBNF grameri (`spec/synax.ebnf`) ve resmi dil spesifikasyonu (`spec/LANGUAGE_SPEC.md`).
   * Satır/sütun `^` işaretli deterministik Lexer, Recursive-Descent Typed AST Parser ve Statik `TypeChecker` (`tensor<f32>`, `tensor<f32, N>`, `require shape(a) == shape(b)`, kapsam ve arite denetimi).
2. **Katman 2 — Derleyici, Çoklu-Backend & Semantik Kilit (`synaxc.py`, `src/synax/backends/`, `semantic_lock.py`):**
   * Saf Python IEEE-754 `binary32` `ReferenceInterpreter` (`interpreter.py`), C11 Skaler, ARM64 NEON (`float32x4_t` + Cody-Waite `expf`), x86_64 AVX2+FMA (`__m256`), Apple GCD Çok-Çekirdek ve doğrudan **SSA LLVM IR (`.ll`)** arka ucu (`llvm_ir_backend.py`).
   * 32 altın IEEE-754 hex vektörlü ve SHA-256 imzalı `.sx.lock` Semantik Kilit yöneticisi (`semantic_lock.py`).
3. **Katman 3 — TYCON / MYELIN & Donanım Parmak İzi (`hardware.py`, `myelin_store.py`):**
   * Kriptografik `hw_fingerprint` (`detect_hardware_fingerprint()`), ısınmış önbellek medyan seçimi ve `~/.cache/synax/hafiza/<ir_hash>/` imzalı optimizasyon hafızası + `SynaxAxonChannel` O(1) fonksiyon işaretçisi hot-swap.
4. **Katman 4 — Çok-Dilli SDK & Sıfır-Bağımlılıklı Paketleme (`pyproject.toml`, `include/`, `bindings/rust/`):**
   * Sıfır dış bağımlılıklı PEP 517/660 derleme arka ucu (`_pep517_backend.py`) ile çevrimdışı/çevrimiçi çalışan `pip install .` / `pip install -e .` ve `import synax` Python SDK'sı (`sdk.py`).
   * Resmi C99/C11 başlığı (`include/synax.h`), C++17 RAII sarmalayıcısı (`include/synax.hpp`) ve güvenli Rust FFI paketi (`bindings/rust/`).
5. **Katman 5 — Test, Fuzzing, Benchmark & Cross-Platform CI (`tests/`, `benchmarks/`, `.github/workflows/ci.yml`):**
   * 5 tam otomatik test paketi (`./synax test`): Frontend/Type/Lock birim testleri, C11/C++17 FFI testleri, Miyelin diferansiyel testleri, 19-küme birleşik derleyici regresyonu ve rastgele AST/IEEE-754 diferansiyel fuzzer (`test_fuzz_differential.py`).
   * Tekrarlanabilir benchmark motoru (`benchmarks/run_benchmarks.py` -> `BENCHMARK_REPORT.md`) ve macOS/Ubuntu/Windows GitHub Actions CI.
6. **Katman 6 — Geliştirici Araçları (`synax_cli.py`, `formatter.py`, `profiler_debugger.py`, `editors/vscode-synax/`):**
   * İdempotent biçimlendirici (`synax fmt`), çok-katmanlı denetleyici (`synax inspect --llvm|--avx2|--neon|--c|--ast|--ir`), adım adım IEEE-754 hex hata ayıklayıcı (`synax debug`), Roofline profilleyici (`synax profile`) ve VS Code eklentisi (`editors/vscode-synax/`).
7. **Katman 7 — Dağıtım & Sürüm Altyapısı (`.github/workflows/release.yml`, `scripts/install.sh`, `updater.py`):**
   * Etiket tabanlı (`v*`) macOS/Linux/PyPI otomatik sürüm boru hattı, `SHA256SUMS.txt` doğrulamalı kurucu betik ve `synax update --check` sürüm denetleyicisi.
8. **Katman 8 — Kurumsal Yönetişim (`SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `ROADMAP.md`, `CITATION.cff`):**
   * Tam kurumsal açık kaynak yönetişim paketi ve AB MDR / IEC 60601-2-4 uyumlu klinik-dışı araştırma sınırları.

---

## 3. SIRADAKİ BİLİMSEL ARAŞTIRMA PAKETİ (ISSUE #6)
* **İş #1–#7:** **TAMAMLANDI (DONE)**. İş #6 sonuçları: `research/vf_retrospective/results/EVALUATION_REPORT.md` (kaba VF duyarlılığı %73.5 — AHA %90 hedefi karşılanmadı; dürüstçe raporlandı).
* **İş #6 (TAMAMLANDI — v0.1 bulgular, sonraki adım: harici doğrulama):** PhysioNet açık veri tabanları (CU Ventricular Tachyarrhythmia `cudb` ve MIT-BIH Malignant Ventricular Ectopy `vfdb`) üzerinde retrospektif Ventriküler Fibrilasyon (VF) sinyal işleme çalışması, AHA AED performans hedeflerine göre duyarlılık/özgüllük raporu ve akademik makale taslağı.
