---
name: hypothesis-generation
description: Formulation of falsifiable null (H0), primary alternative (H1), and competing mechanistic (H2) hypotheses using FINER and PICO criteria alongside discriminating experimental designs. (Sınanabilir hipotezler (H0/H1, FINER) ve bunları ayırt edecek deney önerileri)
---

# SYNAX Academic Skill #08: `hypothesis-generation` — Sınanabilir Hipotez & Deney Tasarımı

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Sınanabilir hipotezler (H0/H1, FINER) ve bunları ayırt edecek deney önerileri  
**İngilizce Kapsam:** Formulation of falsifiable null (H0), primary alternative (H1), and competing mechanistic (H2) hypotheses using FINER and PICO criteria alongside discriminating experimental designs.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "hypothesis-generation" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "hypothesis-generation", "topic_or_text": "<konu_veya_metin>"}`
