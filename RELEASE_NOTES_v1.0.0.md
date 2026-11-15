# SYNAX v1.0.0 — Tam Sürüm Programlama Dili, E-Graph & Biçimsel Kanıt Motoru (Production Release)

**Sürüm:** `v1.0.0`  
**Tarih:** 15 Kasım 2026  
**Yazar:** Dr. Ömer Faruk Aydın  

---

## 🚀 Öne Çıkan Yenilikler (`v1.0.0`)

1. **`SYNAX 1.0` Tam Sürüm Programlama Dili Ergonomisi (`synax 1.0`):**
   - **Dallanmasız Koşullu Seçici (`select(cond, val_true, val_false)` / `mux`):** Boru hattı duraklaması yaratmadan C11 (`synax_selectf`), ARM64 NEON (`vbslq_f32` + `vcgtq_f32`), x86_64 AVX2 (`_mm256_blendv_ps`), SSA LLVM IR (`fcmp ogt` + `select i1`) ve Q16.16 MCU hedeflerine **0-ULP** bit-birebir doğrulukla indirgenir.
   - **Birleşik Çarpma-Toplama (`fma(a, b, c)`):** Tüm 5 derleyici arka ucunda ve `ReferenceInterpreter` üzerinde IEEE-754 binary32 0-ULP garantisiyle çalışır.
   - **Çok Adımlı Tip Bildirimli `let` Bağlamaları:** `let cpp: tensor<f32> = ...`, `let gate: tensor<f32> = ...` şeklinde ardışık sembolik değişken zincirleri hem yapısal AST hem de IR katmanında tam desteklenir.
   - **Dendritik İndirgeme ve Aktivasyon Primitifleri:** `sum`, `mean`, `l2_norm`, `dot`, `window_mean`, `sigmoid`, `tanh`, `relu`, `sin`, `cos`, `exp`, `log`, `sqrt`, `abs`, `clamp`.

2. **E-Graph Eşitlik Doygunluğu (`src/synax/egraph.py`) & Statik Aralık Kanıtlayıcı (`src/synax/formal_prover.py`):**
   - **E-Graph Equality Saturation:** Klasik ardışık optimizasyonların faz sıralama (phase-ordering) sorununu ortadan kaldırarak tüm eşdeğer ifade uzayını (`fma`, `pow2`, `pow3`, `relu`, `select`) aynı anda doyurur ve hedef donanım maliyet tablosuna göre en düşük çevrimli AST'yi çıkarır.
   - **Statik IEEE-754 Aralık Soyut Yorumlama (`[lo, hi]`):** Derleme zamanında sıfıra bölme (`0.0 not in denom`), tanım kümesi (`sqrt`/`log`) ve `float32` taşma (`overflow`) güvenliğini matematiksel olarak kanıtlayarak SHA-256 imzalı `FormalProofCertificate` üretir.

3. **Çoklu Model Ekosistemi & Telegram Bot Becerisi (`src/synax/telegram_bot.py`):**
   - **Claude Code, OpenAI Codex, Google Antigravity ve Cursor Eklentileri:** `.claude-plugin/plugin.json`, `.mcp.json`, `AGENTS.md`, `.codex/config.toml` ve `.cursor/mcp.json` ile tam entegrasyon.
   - **SYNAX Telegram Bot (`./synax telegram`):** Sıfır bağımlılıklı Telegram Bot API & MCP köprüsü ile `/status`, `/egraph`, `/prove`, `/check`, `/run` ve `/code` komutlarını uzaktan yürütme.
   - **Bağımsız Masaüstü Uygulaması (`SYNAX Studio.app`):** macOS uygulama paketi ve tam ekran VS Code çalışma istasyonu.
