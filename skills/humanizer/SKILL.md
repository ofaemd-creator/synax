---
name: humanizer
description: Eliminates 100% of AI-generated clichés ('delve into', 'testament to', 'tapestry', 'game-changer') and calibrates natural sentence burstiness while preserving 100% of numbers, formulas, and citations. (Bilimsel anlamı, formülleri ve sayıları koruyarak daha doğal, akıcı ve otoriter anlatım sağlama)
---

# SYNAX Academic Skill #21: `humanizer` — Akademik Humanizer (Sıfır AI-Tell & Doğal Anlatım)

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Bilimsel anlamı, formülleri ve sayıları koruyarak daha doğal, akıcı ve otoriter anlatım sağlama  
**İngilizce Kapsam:** Eliminates 100% of AI-generated clichés ('delve into', 'testament to', 'tapestry', 'game-changer') and calibrates natural sentence burstiness while preserving 100% of numbers, formulas, and citations.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "humanizer" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "humanizer", "topic_or_text": "<konu_veya_metin>"}`
