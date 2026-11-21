---
name: scientific-schematics
description: Scientific mechanism schematics, PRISMA 2020 / CONSORT flow diagrams, and Graphical Abstract blueprints in Mermaid and vector formats. (Bilimsel şema, mekanizma diyagramı (Mermaid/SVG) ve grafik özet tasarlama)
---

# SYNAX Academic Skill #11: `scientific-schematics` — Bilimsel Şema & Grafik Özet (Graphical Abstract)

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Bilimsel şema, mekanizma diyagramı (Mermaid/SVG) ve grafik özet tasarlama  
**İngilizce Kapsam:** Scientific mechanism schematics, PRISMA 2020 / CONSORT flow diagrams, and Graphical Abstract blueprints in Mermaid and vector formats.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "scientific-schematics" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "scientific-schematics", "topic_or_text": "<konu_veya_metin>"}`
