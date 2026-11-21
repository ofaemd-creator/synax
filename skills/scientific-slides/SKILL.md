---
name: scientific-slides
description: International scientific congress 10-slide presentation decks, academic poster layouts, and patient-accessible Plain Language Summaries (Lay Abstracts). (Bilimsel kongre sunumu (12 slayt), poster ve sade dilde araştırma özeti (Plain Language Summary) hazırlama)
---

# SYNAX Academic Skill #12: `scientific-slides` — Bilimsel Sunum, Poster & Sade Dil Özeti

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Bilimsel kongre sunumu (12 slayt), poster ve sade dilde araştırma özeti (Plain Language Summary) hazırlama  
**İngilizce Kapsam:** International scientific congress 10-slide presentation decks, academic poster layouts, and patient-accessible Plain Language Summaries (Lay Abstracts).  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "scientific-slides" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "scientific-slides", "topic_or_text": "<konu_veya_metin>"}`
