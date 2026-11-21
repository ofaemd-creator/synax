---
name: citation-management
description: Bibliographic formatting (Vancouver, APA 7th, IEEE, BibTeX), live DOI/PMID provenance verification, and claim-to-citation alignment auditing. (Kaynakça, DOI/PMID ve kaynakların iddiaları destekleyip desteklemediğinin kontrolü)
---

# SYNAX Academic Skill #04: `citation-management` — Kaynakça & İddia-Atıf Doğrulama Yönetimi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Kaynakça, DOI/PMID ve kaynakların iddiaları destekleyip desteklemediğinin kontrolü  
**İngilizce Kapsam:** Bibliographic formatting (Vancouver, APA 7th, IEEE, BibTeX), live DOI/PMID provenance verification, and claim-to-citation alignment auditing.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "citation-management" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "citation-management", "topic_or_text": "<konu_veya_metin>"}`
