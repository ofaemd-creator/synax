---
name: literature-review
description: Reproducible workflows for Systematic Reviews (PRISMA 2020), Scoping Reviews (PRISMA-ScR), and Narrative Reviews (SANRA 12/12 quality scale) with dynamic flow accounting. (Sistematik (PRISMA 2020), kapsam (PRISMA-ScR) ve anlatı (SANRA) derlemeleri için izlenebilir iş akışı)
---

# SYNAX Academic Skill #07: `literature-review` — Sistematik, Kapsam & Anlatı Derlemesi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Sistematik (PRISMA 2020), kapsam (PRISMA-ScR) ve anlatı (SANRA) derlemeleri için izlenebilir iş akışı  
**İngilizce Kapsam:** Reproducible workflows for Systematic Reviews (PRISMA 2020), Scoping Reviews (PRISMA-ScR), and Narrative Reviews (SANRA 12/12 quality scale) with dynamic flow accounting.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "literature-review" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "literature-review", "topic_or_text": "<konu_veya_metin>"}`
