---
name: academic-translation
description: Bidirectional (Turkish <-> English) academic translation preserving 100% of NCBI MeSH medical terminology, statistical parameters, p-values, and citations. (Teknik/MeSH terimleri, sayıları ve bilimsel anlamı %100 koruyarak çift yönlü çeviri)
---

# SYNAX Academic Skill #14: `academic-translation` — Terminoloji Korumalı Akademik Çeviri (TR <-> EN)

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Teknik/MeSH terimleri, sayıları ve bilimsel anlamı %100 koruyarak çift yönlü çeviri  
**İngilizce Kapsam:** Bidirectional (Turkish <-> English) academic translation preserving 100% of NCBI MeSH medical terminology, statistical parameters, p-values, and citations.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-translation" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-translation", "topic_or_text": "<konu_veya_metin>"}`
