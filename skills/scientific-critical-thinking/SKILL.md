---
name: scientific-critical-thinking
description: Critical appraisal of study methodology, Risk of Bias assessment (Cochrane RoB-2, ROBINS-I, QUADAS-2), causal inference (Bradford Hill criteria, Directed Acyclic Graphs), and GRADE evidence certainty. (Yöntem, yanlılık (RoB-2/QUADAS-2), nedensellik (Bradford Hill/DAG) ve kanıtların eleştirel değerlendirmesi)
---

# SYNAX Academic Skill #02: `scientific-critical-thinking` — Bilimsel Eleştirel Düşünme & Yanlılık Analizi

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Yöntem, yanlılık (RoB-2/QUADAS-2), nedensellik (Bradford Hill/DAG) ve kanıtların eleştirel değerlendirmesi  
**İngilizce Kapsam:** Critical appraisal of study methodology, Risk of Bias assessment (Cochrane RoB-2, ROBINS-I, QUADAS-2), causal inference (Bradford Hill criteria, Directed Acyclic Graphs), and GRADE evidence certainty.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "scientific-critical-thinking" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "scientific-critical-thinking", "topic_or_text": "<konu_veya_metin>"}`
