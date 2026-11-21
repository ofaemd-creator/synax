---
name: academic-publication-pipeline
description: Master 21-Skill Autonomous Coordinator that selects and executes all required scientific skills end-to-end to deliver a complete Q1 SCIE submission dossier. (Makaleye uygun becerileri seçerek bütün Q1 SCIE yayın hazırlığını uçtan uca koordine etme)
---

# SYNAX Academic Skill #20: `academic-publication-pipeline` — 21-Beceri Otonom Yayın Orkestratörü

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Makaleye uygun becerileri seçerek bütün Q1 SCIE yayın hazırlığını uçtan uca koordine etme  
**İngilizce Kapsam:** Master 21-Skill Autonomous Coordinator that selects and executes all required scientific skills end-to-end to deliver a complete Q1 SCIE submission dossier.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-publication-pipeline" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-publication-pipeline", "topic_or_text": "<konu_veya_metin>"}`
