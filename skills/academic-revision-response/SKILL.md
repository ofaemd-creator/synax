---
name: academic-revision-response
description: Point-by-Point Response to Reviewers (Rebuttal Matrix) generation, revision change tracking, and camera-ready resubmission packaging. (Hakemlere madde madde yanıt (Rebuttal Matrix), revizyon takibi ve yeniden gönderim hazırlığı)
---

# SYNAX Academic Skill #17: `academic-revision-response` — Hakemlere Madde Madde Yanıt & Revizyon Takibi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Hakemlere madde madde yanıt (Rebuttal Matrix), revizyon takibi ve yeniden gönderim hazırlığı  
**İngilizce Kapsam:** Point-by-Point Response to Reviewers (Rebuttal Matrix) generation, revision change tracking, and camera-ready resubmission packaging.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-revision-response" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-revision-response", "topic_or_text": "<konu_veya_metin>"}`
