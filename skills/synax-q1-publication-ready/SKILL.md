---
name: synax-q1-publication-ready
description: End-to-end 5-Agent Q1 SCIE Publication Packager uniting Agent-Scholar, Agent-Biostat, Agent-Author-Q1, Agent-Humanizer-Editor, and Agent-Peer-Reviewer to generate a complete camera-ready submission bundle (Markdown Manuscript, Sanitized LaTeX .tex, Editor-in-Chief Cover Letter, 3-Referee Peer Review & Point-by-Point Rebuttal, EQUATOR Checklist, Humanization Audit, and Verified BibTeX).
---

# SYNAX Q1 SCIE Camera-Ready Publication Pipeline (`synax-q1-publication-ready`)

Activate this skill whenever Dr. Aydın or a user wants to take a research topic or draft from start to finish and produce a complete, unconditional-accept-ready Q1 SCIE journal submission package.

## 8-File Camera-Ready Submission Package
Running `Q1PublicationPipeline.run_full_q1_pipeline` generates and verifies:
1. `01_MANUSCRIPT_Q1_SCIE.md` — Peer-reviewed, humanized, auto-upgraded Q1 IMRaD manuscript.
2. `02_MANUSCRIPT_CAMERA_READY.tex` — Zero-injection sanitized LaTeX source ready for Overleaf / journal submission.
3. `03_COVER_LETTER_TO_EDITOR.md` — High-impact Editor-in-Chief Cover Letter with ICMJE attestations.
4. `04_PEER_REVIEW_AND_REBUTTAL.md` — 3-Referee Pre-Submission Audit Scorecard + Point-by-Point Author Rebuttal Letter.
5. `05_EQUATOR_COMPLIANCE_CHECKLIST.md` — Item-by-item verified PRISMA 2020 / TRIPOD+AI / STROBE / CONSORT checklist.
6. `06_HUMANIZATION_AND_STYLE_AUDIT.md` — Before/After de-AI-ification, burstiness CV, and numerical invariance proof.
7. `07_PRISMA_AND_BIOSTAT_REPORT.md` — Dynamic PRISMA 2020 flow, PICO table, DerSimonian-Laird calculations, and Forest Plot.
8. `08_REFERENCES.bib` — Verified PMIDs and DOIs in BibTeX format.

## CLI Execution
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --q1-pipeline "<research_topic>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)" \
  --guideline "PRISMA_2020" \
  --output-dir "/Users/o.farukaydin/.gemini/antigravity/scratch/q1_submission_bundle"
```
