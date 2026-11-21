---
name: synax-academic-humanizer
description: Edit, polish, and humanize scientific manuscripts by eliminating 100% of AI-generated clichés ("delve into", "testament to", "tapestry", "pivotal", "revolutionize"), calibrating sentence burstiness (CV = sigma/mu), and enforcing AMA Manual of Style (11th Ed.) and Nature/Lancet senior investigator prose while preserving 100% of statistical numbers, p-values, confidence intervals, DOIs, and citations.
---

# SYNAX Academic Humanizer & Scientific Editing Skill (`synax-academic-humanizer`)

Activate this skill whenever the user asks to edit, humanize, de-AI-ify, polish, or improve the academic English or Turkish prose of a scientific manuscript or research section.

## Core Methodology
1. **100% Elimination of AI Tells & Clichés:**
   - Strips 45+ English and Turkish LLM clichés (`delve into`, `a testament to`, `rich tapestry`, `symphony of`, `beacon of hope`, `game-changer`, `revolutionize`, `it is important to note that`, `in the realm of`, `ever-evolving landscape`, `shed light on`, `pave the way for`, `meticulously`, `derinlemesine dalmak`, `devrim niteliğinde`, `ışık tutmaktadır`) and replaces them with precise Q1 scholarly verbs and modifiers.
2. **Syntactic Burstiness & Transition Calibration:**
   - Diversifies monotonous transition chains (`Furthermore, ... Moreover, ... Additionally, ...`) into natural scholarly transitions (`Concurrently,`, `Consistent with these observations,`, `From a methodological standpoint,`).
   - Measures sentence length variance ($\text{CV} = \sigma_L / \mu_L$) and lexical diversity (Type-Token Ratio).
3. **Strict Quantitative & Citation Invariance:**
   - Verifies that 100% of numbers, sample sizes ($N$), effect sizes ($d$), 95% confidence intervals, $p$-values, DOIs, PMIDs, and numbered citations (`[1]`) remain completely unaltered before and after humanization.

## CLI Execution
```bash
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax-agent-office/src/synax/academic_skills.py \
  --humanize "<manuscript_text>" \
  --journal "Nature Medicine / AMA 11th Ed."
```
