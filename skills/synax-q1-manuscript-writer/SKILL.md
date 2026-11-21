---
name: synax-q1-manuscript-writer
description: Author full-length, publication-grade Q1 SCIE scientific manuscripts compliant with EQUATOR Network guidelines (PRISMA 2020, CONSORT 2010, STROBE, TRIPOD+AI, STARD 2015), complete with Research-in-Context panels, structured abstracts, IMRaD sections, ICMJE/CRediT declarations, sanitized LaTeX (.tex) source, Editor-in-Chief Cover Letter, and verified Vancouver/BibTeX references.
---

# SYNAX Q1 SCIE Scientific Manuscript Authoring Skill (`synax-q1-manuscript-writer`)

Activate this skill whenever the user wants to write, structure, or format a high-impact scientific manuscript for top Q1 SCIE journals (*Nature Medicine*, *The Lancet Digital Health*, *Intensive Care Medicine*, *Critical Care*, *IEEE TMI*, *NEJM AI*, *JAMA Network Open*).

## Core Capabilities
1. **EQUATOR Network Reporting Standards:**
   - `PRISMA_2020` (Systematic Reviews & Random-Effects Meta-Analyses)
   - `TRIPOD_AI` (Clinical AI, Deep Learning & Formal Biomedical Algorithm Validation)
   - `STROBE` (Observational Cohort, Case-Control & Cross-Sectional Studies)
   - `CONSORT_2010` (Randomized & Comparative Clinical Trials)
2. **Q1 Manuscript Architecture:**
   - Title Page, Running Head, Affiliations & CRediT Author Statement
   - *Research in Context* Panel (Evidence before this study, Added value, Clinical implications)
   - 4-Part Structured Abstract (Background, Methods, Findings with exact 95% CIs & $p$-values, Interpretation)
   - Full IMRaD Sections (Introduction, Methods with formal mathematical derivations, Results with Table 1 & Forest Plot, Discussion with Strengths & Methodological Limitations, Conclusions)
   - Mandatory ICMJE Declarations (Ethics/Helsinki, Data Availability, Competing Interests, Funding, CRediT)
3. **Zero-Injection LaTeX & Submission Deliverables:**
   - Produces sanitized LaTeX (`.tex`) source protected by `AcademicSecuritySanitizer.escape_latex` (neutralizing `\write18`, `\input`, and macro injection).
   - Generates a persuasive Editor-in-Chief Cover Letter and an item-by-item EQUATOR Compliance Checklist.

## CLI Execution
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --q1-pipeline "<research_topic>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)" \
  --guideline "PRISMA_2020"
```
