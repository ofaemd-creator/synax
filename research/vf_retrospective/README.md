# Issue #6 — Retrospektif VF/VT Sinyal İşleme Araştırması

> [!CAUTION]
> Klinik olmayan araştırma. Tıbbi cihaz değildir; tanı veya şok kararı için kullanılamaz.

## Çalıştırma

```bash
python research/vf_retrospective/download_physionet.py   # ~40 MB, tek sefer (internet gerekir)
python research/vf_retrospective/run_evaluation.py       # ~10 sn, rapor üretir
```

Çıktılar: `results/EVALUATION_REPORT.md`, `results/evaluation_results.json`.
Makale taslağı: `MANUSCRIPT_DRAFT.md`.

## Bileşenler
- `src/synax/biomedical/wfdb_reader.py` — bağımlılıksız WFDB okuyucu (checksum doğrulamalı)
- `src/synax/biomedical/vf_features.py` — `.sx` çekirdekleri + 16 yorumlanabilir öznitelik
- `examples/vf_bandpass_sanitizer.sx`, `examples/vf_nonlinear_energy.sx` (+ `.sx.lock`)
- `tests/test_biomedical_wfdb.py` — indirme gerektirmeyen birim testleri (CI'da koşar)

## Özet sonuç (dürüst)
- ✅ Semantik koruma: 16 M gerçek EKG örneğinde native ≡ referans (sanitizer bit-birebir, enerji ≤1.5e-5), heal sayıları her kayıtta eşit.
- ✅ Hızlı VT, diğer non-şoklanabilir ve asistoli AHA hedeflerini karşılıyor.
- ❌ Kaba VF duyarlılığı %73.5 (hedef %90) — hasta bazlı katı doğrulamada hedefi **karşılamıyor**.
- ⚠️ SYNAX enerji özniteliği ablasyonda katkı **göstermedi**.
