# SYNAX (.sx) PROJE MASTER DEVİR & ÇALIŞMA DOSYASI
**Hedef:** Yeni Antigravity / Claude / GPT Oturumuna Doğrudan Aktarım  
**Sahibi:** Dr. Ömer Faruk Aydın (Acil Tıp Hekimi & Sistem Mimarı)  
**Tarih:** 3 Kasım 2026 | **Sürüm:** v0.5.0-unified-compiler  
**Resmi Lisans:** Apache License 2.0 (Resmi Haklar, Ticari Marka & Tıbbi Araştırma Sorumluluk Reddi)

---

## 1. EKOSİSTEM VE CANLI ALTYAPI DURUMU
* **Ana Tanıtım Platformu:** https://synaxcode.com (Vizyon, özellikler, mimari, installer)
* **Teknik Dokümantasyon & Git:** https://synaxcode.org (Dil spesifikasyonu, araştırma makaleleri, `synaxcode.org/repos.html`)
* **Sovereign Git Deposu:** `git clone https://synaxcode.org/git/synax.git` (Dumb-HTTP repacked, bağımsız, çalışan Git sunucusu)
* **Cloud Studio IDE (Amiral Gemisi):** https://synaxcode.online (Canlı 60 FPS Biyomedikal EKG Osiloskopu, AST Parser, IEEE 754 Kalkanı, Prompt-to-Code)
* **Başlangıç Düzeyi Rehberi (16 Sayfa):** https://synaxcode.org/guide.html ve https://synaxcode.com/guide.html (Eksiksiz 14 bölüm, sözlük, SSS)
* **Resmi GitHub Deposu:** https://github.com/ofaemd-creator/synax (Tüm kodlar, C motoru, testler ve dokümantasyon senkronize)
* **GitHub Project Panosu:** https://github.com/users/ofaemd-creator/projects/1/views/1 (7 adet aktif mühendislik iş paketi)

---

## 2. TAMAMLANAN VE DOĞRULANAN ÇEKİRDEK İŞLER (DONE)
1. **NEON Bağışıklık Kalkanı Kanal B Hatası Çözüldü (`synax_myelin_engine.c`):**
   * Claude ve Codex hakem incelemesinde tespit edilen Kanal B (CVP) elektrot kopması ve NaN zehirlenmesi açığı kapatıldı.
   * IEEE 754 bit-seviyesinde unsigned SIMD maskesi (`abs_bits <= 0x447A0000`) ile tek talimatta hem Kanal A hem Kanal B normalize edildi.
2. **Diferansiyel Denklik Testleri (%100 Bit-Exact Doğruluk):**
   * `test_differential_myelin.py`: Skaler C yolu ile ARM64 NEON sıçramalı yolu 5 zorlu senaryoda (Temiz sinyal, A NaN, B NaN, Aşırı uçlar +/-99999, 8197 elemanlık kuyruk) test edildi.
   * Sonuç: **Maksimum Sayısal Fark: 0.00e+00 | Anomali Sayaç Farkı: 0**.
3. **Adil ve Dürüst Benchmark Standartları:**
   * Soğuk önbellek şişirmeleri kaldırıldı; Apple Silicon M1 üzerinde `clang -O3` karşısında **2.4x - 3.5x gerçek hızlanma** (201 warm run median) tescillendi.
4. **Hukuki Zırh ve Regülasyon Koruması:**
   * `LICENSE` (Apache-2.0), `NOTICE`, `TRADEMARKS.md`, `LICENSING.md`.
   * `MEDICAL_RESEARCH_DISCLAIMER.md`: Projenin kesinlikle bir AED/defibrilatör tıbbi cihazı olmadığı, açık veriler (PhysioNet) üzerinde algoritmik bir retrospektif araştırma yazılımı olduğu deklare edilerek AB MDR ve IEC 60601-2-4 regülatif riskleri bertaraf edildi.
5. **İş #4 Tamamlandı — Birleşik Derleyici & Miyelin Boru Hattı (`synaxc` v0.5):**
   * `synax_ir.py`: Hem yapısal `synax 0.1 kernel ...` (Cloud Studio uyumlu) hem de bildirimsel `niyet:/kural:/hedef:` (v0.4 uyumlu) `.sx` dosyalarını tek bir kanonik IEEE-754 `SynaxIR` temsili altında birleştirir (`preserve`, `heal_inputs`, `zero_output`, `reject`).
   * `synax_verifier.py`: Çift-Referans Semantik Kapısı (Python IEEE-754 binary32 AST == C11 `-O0` Skaler) + v0.4'ün **19 zorlu uç test kümesi** (`n=0..100,003`, `NaN`, `±Inf`, `±0.0`, `1e-40` denormal, `±3.4e38`, 144 Kartezyen çift, `1234.5f` sentinel ve anomali sayaç denkliği).
   * `synaxc.py` & `synax_myelin_engine.c`: `-ffast-math` kullanmadan 5 C11/NEON/GCD varyantı üretir, 19 kümeyi geçemeyeni eler, `~/.cache/synax/hafiza/<ir_hash>/` altına SHA-256 imzalı kaydeder ve `SynaxAxonChannel` C fonksiyon işaretçisi takasıyla (`synax_axon_bind_compiled_kernels`) canlı akışta skalerden optimize çekirdeğe O(1) geçiş yapar (`kapili_aktivasyon.sx` üzerinde `clang -O3`'e karşı **6.48x** doğrulanmış hızlanma).

---

## 3. MEVCUT KOD DİZİNİ (`/Users/o.farukaydin/.gemini/antigravity/scratch/synax`)
* `synax_ir.py`: Kanonik Ara Temsil (`SynaxIR`), `SafetyPolicy` ve birleşik `.sx` ayrıştırıcısı.
* `synax_verifier.py`: 19 kümeli diferansiyel doğrulayıcı, çift-referans kapısı ve adil medyan benchmark motoru.
* `synaxc.py`: Birleşik C11 / ARM64 NEON / Apple GCD derleyici boru hattı (`SYNAPSE -> IMMUNE -> AXON -> TYCON -> MYELIN`).
* `synax_myelin_engine.c` & `synax_myelin.py`: Dinamik `.dylib` fonksiyon işaretçisi takası destekli C Miyelin motoru.
* `synax_cli.py` & `./synax`: Birleşik CLI (`compile`, `check`, `run`, `test`, `status`, `myelin`, `stream`).
* `test_differential_myelin.py` & `test_unified_compiler.py`: Diferansiyel ve regresyon doğrulama paketleri.
* `sites/online_index.html`, `sites/guide.html`, `sites/org_index.html`, `sites/com_index.html`: Canlı web ekosistemi.

---

## 4. SIRADAKİ AKTİF İŞ PAKETLERİ (ROADMAP)
* **İş #4 (DONE):** Masaüstündeki v0.4 çekirdeği ile Antigravity v2.0/v0.5 NEON miyelin motoru tek bir standart `synaxc` derleyicisinde birleştirildi ve doğrulandı.
* **İş #5 (NEXT / TODO):** `.sx` dosyaları için resmi PEG/Recursive-descent gramer ve AST spesifikasyonu (`neuron`, `pulse`, `channel`, `immune`, `myelin`).
* **İş #6 (TODO):** PhysioNet (CU-VA & MIT-BIH) verileri üzerinde AHA AED performans hedeflerine göre Ventriküler Fibrilasyon (VF) ritim sınıflandırma araştırması ve teknik makale taslağı.
* **İş #7 (TODO):** `pip install synax` paketlemesi ve GitHub Actions cross-platform CI/CD.
