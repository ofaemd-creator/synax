---
name: academic-pdf-evidence
description: Location-anchored extraction of study methods, sample sizes, outcomes, and tables from PDFs or manuscripts with exact [Section / Paragraph] locators. (PDF/metinden yöntem, sonuç ve tablo çıkarma; bölüm/konum göstererek soru yanıtlama)
---

# SYNAX Academic Skill #15: `academic-pdf-evidence` — PDF & Metin Kanıt Çıkarımı (Konum İzlenebilir)

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** PDF/metinden yöntem, sonuç ve tablo çıkarma; bölüm/konum göstererek soru yanıtlama  
**İngilizce Kapsam:** Location-anchored extraction of study methods, sample sizes, outcomes, and tables from PDFs or manuscripts with exact [Section / Paragraph] locators.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-pdf-evidence" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-pdf-evidence", "topic_or_text": "<konu_veya_metin>"}`
