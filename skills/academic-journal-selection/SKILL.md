---
name: academic-journal-selection
description: Quantitative comparison of Q1 SCIE target journals by scope fit, Impact Factor, SCIE/PubMed indexing, Open Access APC policies, and first-decision review timelines. (Konu uyumu, SCIE indeksi, Q1 durumu, APC ücreti ve politikalara göre dergi karşılaştırma)
---

# SYNAX Academic Skill #16: `academic-journal-selection` — Q1/SCIE Hedef Dergi Seçimi & Karşılaştırma

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Konu uyumu, SCIE indeksi, Q1 durumu, APC ücreti ve politikalara göre dergi karşılaştırma  
**İngilizce Kapsam:** Quantitative comparison of Q1 SCIE target journals by scope fit, Impact Factor, SCIE/PubMed indexing, Open Access APC policies, and first-decision review timelines.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-journal-selection" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-journal-selection", "topic_or_text": "<konu_veya_metin>"}`
