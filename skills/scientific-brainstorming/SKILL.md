---
name: scientific-brainstorming
description: Identification of high-impact literature gaps, translational bottlenecks, novel clinical/computational study architectures, and FINER feasibility scoring. (Araştırma sorusu, literatür boşluğu, özgün fikir ve çalışma tasarımı geliştirme)
---

# SYNAX Academic Skill #09: `scientific-brainstorming` — Bilimsel Beyin Fırtınası & Çalışma Tasarımı

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Araştırma sorusu, literatür boşluğu, özgün fikir ve çalışma tasarımı geliştirme  
**İngilizce Kapsam:** Identification of high-impact literature gaps, translational bottlenecks, novel clinical/computational study architectures, and FINER feasibility scoring.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "scientific-brainstorming" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "scientific-brainstorming", "topic_or_text": "<konu_veya_metin>"}`
