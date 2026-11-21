---
name: academic-language-editing
description: AMA Manual of Style (11th Ed.) grammar polishing, scholarly paraphrasing, syntactic burstiness optimization, and meaning-preserving word-count reduction. (Akademik dil, AMA 11th Ed. dilbilgisi, yeniden ifade ve anlamı/sayıları koruyarak kısaltma)
---

# SYNAX Academic Skill #13: `academic-language-editing` — Akademik Dil Editörlüğü & Kelime Kısaltma

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Akademik dil, AMA 11th Ed. dilbilgisi, yeniden ifade ve anlamı/sayıları koruyarak kısaltma  
**İngilizce Kapsam:** AMA Manual of Style (11th Ed.) grammar polishing, scholarly paraphrasing, syntactic burstiness optimization, and meaning-preserving word-count reduction.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-language-editing" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-language-editing", "topic_or_text": "<konu_veya_metin>"}`
