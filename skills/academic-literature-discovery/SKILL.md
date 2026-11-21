---
name: academic-literature-discovery
description: Multi-database bibliographic discovery and comparative evidence matrix generation compatible with NCBI PubMed, CrossRef, and SciSpace workflows. (PubMed, CrossRef ve SciSpace uyumlu bibliyografik araçlarla makale bulma ve karşılaştırma)
---

# SYNAX Academic Skill #19: `academic-literature-discovery` — Bibliyografik & SciSpace Literatür Keşfi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** PubMed, CrossRef ve SciSpace uyumlu bibliyografik araçlarla makale bulma ve karşılaştırma  
**İngilizce Kapsam:** Multi-database bibliographic discovery and comparative evidence matrix generation compatible with NCBI PubMed, CrossRef, and SciSpace workflows.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "academic-literature-discovery" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "academic-literature-discovery", "topic_or_text": "<konu_veya_metin>"}`
