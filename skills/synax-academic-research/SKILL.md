---
name: synax-academic-research
description: Conduct PRISMA 2020 systematic literature reviews, live PubMed/CrossRef academic searches, PICO framework formulation, GRADE evidence grading, inverse-variance & DerSimonian-Laird random-effects biostatistical meta-analysis (Hedges g, Cohen d, 95% CI, 95% Prediction Interval, Cochran Q, I^2, Statistical Power, Forest Plot), Q1 SCIE IMRaD manuscript drafting, academic humanization, and 3-referee pre-submission peer review.
---

# SYNAX Academic Research, Biostatistical Meta-Analysis & Q1 SCIE Publishing Suite (`synax-academic-research`)

Use this skill whenever Dr. Aydın or a user requests academic research, literature review, article critique, meta-analysis, biostatistics, Q1 SCIE manuscript writing, scientific humanization, or pre-submission peer review.

## Specialized Academic Agents
1. **Masa 2 (`Agent-Scholar` / `@academic-scholar`)**: Live CrossRef/PubMed search, PICO decomposition, PRISMA 2020 screening flow, GRADE evidence matrix, Vancouver, APA 7th & BibTeX bibliography. Zero-fabrication policy (never invents PMIDs, DOIs, or sample sizes).
2. **Masa 3 (`Agent-Biostat` / `@biostat-analyst`)**: Inverse-variance & DerSimonian-Laird random-effects meta-analysis ($\tau^2$), 95% Confidence & Prediction Intervals, statistical power ($1 - \beta$), Forest Plot visualization, and `INSUFFICIENT_VERIFIED_DATA` safety guard.
3. **`Agent-Author-Q1` (`@q1-manuscript-author`)**: Full EQUATOR Network (PRISMA 2020, CONSORT 2010, STROBE, TRIPOD+AI) IMRaD manuscript authoring, Research-in-Context panel, ICMJE/CRediT declarations, sanitized camera-ready LaTeX (`.tex`), and Editor-in-Chief Cover Letter.
4. **`Agent-Humanizer-Editor` (`@academic-humanizer-editor`)**: Eliminates 100% of AI clichés (`delve into`, `testament to`, `tapestry`, etc.), optimizes sentence burstiness, and enforces AMA 11th Ed. / Nature Medicine scholarly tone while preserving 100% of citations and statistical figures.
5. **`Agent-Peer-Reviewer` (`@scie-peer-reviewer`)**: 3-Referee Pre-Submission SCIE Blind Peer Review, 6-axis Readiness Scorecard (0–100), automated self-upgrade loop to `UNCONDITIONAL_ACCEPT_READY`, and Point-by-Point Author Rebuttal Letter.

## Security & Zero-Injection Guarantee
All inputs pass through `AcademicSecuritySanitizer`, blocking shell command injection, Python `eval`/`exec` injection, LaTeX macro execution (`\write18`), XSS, and prompt overrides.

## CLI Execution
```bash
# Systematic Review & Biostatistical Meta-Analysis
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py --research "<research_topic>"

# End-to-End 5-Agent Q1 SCIE Publication Pipeline
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py --q1-pipeline "<research_topic>" --journal "Nature Medicine (Q1 SCIE)" --guideline "PRISMA_2020"
```
