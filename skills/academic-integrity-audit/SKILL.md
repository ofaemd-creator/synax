---
name: academic-integrity-audit
description: Comprehensive audit of citation provenance, text originality, COPE/ICMJE ethical compliance, CRediT authorship taxonomy, and transparent AI assistance disclosure statements. (Atıf, metin özgünlüğü, COPE/ICMJE etik, CRediT yazarlık ve şeffaf AI beyanı incelemesi)
---

# SYNAX Academic Skill #18: `academic-integrity-audit` — Akademik Dürüstlük, Etik & AI Beyanı Denetimi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Atıf, metin özgünlüğü, COPE/ICMJE etik, CRediT yazarlık ve şeffaf AI beyanı incelemesi  
**İngilizce Kapsam:** Comprehensive audit of citation provenance, text originality, COPE/ICMJE ethical compliance, CRediT authorship taxonomy, and transparent AI assistance disclosure statements.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-integrity-audit" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-integrity-audit", "topic_or_text": "<konu_veya_metin>"}`
