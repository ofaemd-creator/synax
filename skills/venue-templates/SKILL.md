---
name: venue-templates
description: Target Q1 SCIE journal formatting (Nature Medicine, The Lancet, Intensive Care Medicine, IEEE TMI), word limit auditing, ICMJE declarations, sanitized LaTeX (.tex) templates, and Editor-in-Chief Cover Letters. (Hedef derginin biçim, beyan ve LaTeX/Word gönderim şartlarına hazırlık)
---

# SYNAX Academic Skill #06: `venue-templates` — Hedef Dergi & Kongre Şablon Hazırlığı

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Hedef derginin biçim, beyan ve LaTeX/Word gönderim şartlarına hazırlık  
**İngilizce Kapsam:** Target Q1 SCIE journal formatting (Nature Medicine, The Lancet, Intensive Care Medicine, IEEE TMI), word limit auditing, ICMJE declarations, sanitized LaTeX (.tex) templates, and Editor-in-Chief Cover Letters.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "venue-templates" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "venue-templates", "topic_or_text": "<konu_veya_metin>"}`
