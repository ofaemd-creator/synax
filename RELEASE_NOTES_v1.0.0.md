# SYNAX v1.0.0 — Tam Sürüm Programlama Dili & Merkeziyetsiz Frugal AI (Production Release)

**Sürüm:** `v1.0.0`  
**Tarih:** 13 Kasım 2026  
**Yazar:** Dr. Ömer Faruk Aydın  

---

## 🚀 Öne Çıkan Yenilikler (`v1.0.0` Dil Tamamlanması)

1. **`SYNAX 1.0` Tam Sürüm Programlama Dili Ergonomisi (`synax 1.0`):**
   - **Dallanmasız Koşullu Seçici (`select(cond, val_true, val_false)` / `mux`):** Boru hattı duraklaması (branch misprediction) yaratmadan C11 (`synax_selectf`), ARM64 NEON (`vbslq_f32` + `vcgtq_f32`), x86_64 AVX2 (`_mm256_blendv_ps`), SSA LLVM IR (`fcmp ogt` + `select i1`) ve Q16.16 MCU hedeflerine **0-ULP** bit-birebir doğrulukla indirgenir.
   - **Birleşik Çarpma-Toplama (`fma(a, b, c)`):** Tüm 5 derleyici arka ucunda ve `ReferenceInterpreter` üzerinde IEEE-754 binary32 0-ULP garantisiyle çalışır.
   - **Çok Adımlı Tip Bildirimli `let` Bağlamaları:** `let cpp: tensor<f32> = ...`, `let gate: tensor<f32> = ...` şeklinde ardışık sembolik değişken zincirleri hem yapısal AST hem de IR katmanında tam desteklenir.
   - **Dendritik İndirgeme ve Aktivasyon Primitifleri:** `sum`, `mean`, `l2_norm`, `dot`, `window_mean`, `sigmoid`, `tanh`, `relu`, `sin`, `cos`, `exp`, `log`, `sqrt`, `abs`, `clamp`.

2. **Canlı `.sx` Yürütme Motoru (`synax.run_sx`, `/run` ve VS Code CodeLens):**
   - Python SDK (`synax.run_sx`), Sohbet/CLI (`/run`) ve VS Code editöründe her `kernel` bloğunun üstünde yer alan **`▶️ SYNAX Çalıştır & Doğrula (0-ULP Run)`** CodeLens butonu ile herhangi bir `.sx` programı anında derlenir, 19-küme testinden geçirilir, örnek tenzörler üzerinde koşturulur ve mikrosaniye (`µs`) gecikmesi + `IMMUNE` onarım sayısı raporlanır.

3. **Merkeziyetsiz Frugal AI (`~0.38 mJ` / Sorgu) & Otonom Omni-Ajan:**
   - **Yerel `SynaxLLM` (`2.52 MB`) + `SynapseNano` (`4.2 KB`):** Bulut LLM'lerine kıyasla **4.737x daha az enerji** tüketimi ve FPU'suz mikrodenetleyicilerde `< 2 KB RAM` (`Q16.16` sabit noktalı C89) üzerinde çalışma.
   - **5-Aşamalı Otonom Görev (`/gorev`), Canlı 250 Hz VF Telemetrisi (`/vf`), 3B Uzay & Biyomedikal MP4 Video (`/video`) ve Ekran Analizi (`/ekran`).**
