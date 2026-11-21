---
name: peer-review
description: Pre-submission 3-Referee SCIE Blind Peer-Review Simulation (Methodologist, Biostatistician, Q1 Associate Editor), 6-axis Readiness Scorecard (0-100), and prioritized Major/Minor revision planning. (Yayın öncesi hakem değerlendirmesi ve öncelikli (Major/Minor) düzeltme planı)
---

# SYNAX Academic Skill #05: `peer-review` — Yayın Öncesi 3-Hakemli Değerlendirme

**Kategori:** SYNAX 21-Skill Autonomous Q1 SCIE Academic Suite  
**Görev Tanımı:** Yayın öncesi hakem değerlendirmesi ve öncelikli (Major/Minor) düzeltme planı  
**İngilizce Kapsam:** Pre-submission 3-Referee SCIE Blind Peer-Review Simulation (Methodologist, Biostatistician, Q1 Associate Editor), 6-axis Readiness Scorecard (0-100), and prioritized Major/Minor revision planning.  
**Güvenlik Kalkanı:** `AcademicSecuritySanitizer` (Zero Shell / Python AST / LaTeX Macro / XSS / Prompt Injection)

## Tek Komutla Çalıştırma (CLI)
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --skill "peer-review" \
  --input "<araştırma_konusu_veya_makale_metni>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```

## MCP Sunucu Çağrısı (`synax-agent-office`)
- **MCP Tool:** `synax_execute_academic_21_skill`
- **Argümanlar:** `{"skill_id": "peer-review", "topic_or_text": "<konu_veya_metin>"}`
