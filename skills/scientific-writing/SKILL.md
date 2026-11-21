---
name: scientific-writing
description: Scientific manuscript authoring, IMRaD structural consistency, EQUATOR Network compliance (PRISMA 2020, CONSORT, STROBE, TRIPOD+AI), Research-in-Context panels, and ICMJE/CRediT declarations. (Bilimsel makale yazımı, IMRaD yapısı ve bölümler arası tutarlılık)
---

# SYNAX Academic Skill #01: `scientific-writing` — Bilimsel Makale Yazımı & IMRaD Tutarlılığı

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Bilimsel makale yazımı, IMRaD yapısı ve bölümler arası tutarlılık  
**İngilizce Kapsam:** Scientific manuscript authoring, IMRaD structural consistency, EQUATOR Network compliance (PRISMA 2020, CONSORT, STROBE, TRIPOD+AI), Research-in-Context panels, and ICMJE/CRediT declarations.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "scientific-writing" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "scientific-writing", "topic_or_text": "<konu_veya_metin>"}`
