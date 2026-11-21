---
name: synax-scie-peer-reviewer
description: Simulate a pre-submission 3-Referee SCIE Blind Peer Review (Senior Methodologist, Biostatistician, Q1 Associate Editor), compute a 6-axis SCIE Publication Readiness Score (0-100), automatically repair methodological or stylistic flaws to reach UNCONDITIONAL_ACCEPT_READY quality, and generate a formal Point-by-Point Author Response & Rebuttal Letter.
---

# SYNAX Autonomous SCIE Peer-Reviewer & Rebuttal Simulator (`synax-scie-peer-reviewer`)

Activate this skill whenever the user wants to self-referee, critique, audit, or upgrade a scientific manuscript prior to submitting to an international SCIE / Q1 journal.

## Triple-Blind Referee Architecture
1. **Referee #1 — Senior Methodologist & EQUATOR Network Auditor:**
   - Audits IMRaD structural completeness, Research-in-Context panel, PICO specification, inclusion/exclusion transparency, and dedicated Methodological Limitations discussion.
2. **Referee #2 — Biostatistician & Quantitative Integrity Referee:**
   - Audits 95% confidence intervals, 95% prediction intervals, exact $p$-values, Cochran's $Q$, Higgins $I^2$, DerSimonian-Laird $\tau^2$, statistical power ($1 - \beta$), and enforces strict prohibition of synthetic/fabricated numbers.
3. **Referee #3 — Q1 Associate Editor, Humanization & ICMJE Gatekeeper:**
   - Audits prose for zero AI-tells, natural burstiness, ICMJE declarations (Ethics/Helsinki, CRediT Author Contributions, Data Availability, Competing Interests), Vancouver DOI/PMID provenance, and Zero-Injection security hygiene.

## Autonomous Self-Upgrade & Rebuttal Loop
- `review_and_auto_upgrade` automatically resolves every critique identified by the 3 referees, elevates the manuscript to **`UNCONDITIONAL_ACCEPT_READY` ($\ge 95 / 100$)**, and outputs a formal **Point-by-Point Response to Reviewers Letter (`PEER_REVIEW_AND_REBUTTAL.md`)**.

## CLI Execution
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --peer-review "<manuscript_text>" \
  --journal "Nature Medicine / Intensive Care Medicine (Q1 SCIE)"
```
