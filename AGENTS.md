# SYNAX Sovereign Ecosystem — Custom GitHub Agents Specification (v6.3.0)

This repository defines **13 autonomous domain specialist agents** for **SYNAX-OS, 3D Agent Office & Q1 SCIE Academic Publishing Suite**, engineered by **Dr. Ömer Faruk Aydın** ([@ofaemd-creator](https://github.com/ofaemd-creator)).

All custom agents are configured in `.github/agents/` using the official `*.agent.md` standard (as well as `.claude/agents/` and `.codex/agents.toml`). They are automatically indexed by GitHub's **Agents Tab** (`/agents?author=ofaemd-creator`), GitHub Copilot, Claude Code, OpenAI Codex, and Google Antigravity.

---

## 🤖 Active Custom Agents Roster (13 Specialized Agents)

| # | Agent Identifier | Display Name | Specialty & Domain Tools | Agent Definition |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **`@synax-omni-super-llm`** | SYNAX-OMNI Super-LLM | Master ReAct reasoning, Perplexity Live RAG, Claude Canvas & AST Sandbox | [.github/agents/synax-omni-super-llm.agent.md](.github/agents/synax-omni-super-llm.agent.md) |
| **2** | **`@synax-q1-manuscript-author`** | Q1 SCIE Manuscript Author | EQUATOR (PRISMA 2020, TRIPOD+AI, CONSORT, STROBE) IMRaD, LaTeX & Cover Letter | [.github/agents/synax-q1-manuscript-author.agent.md](.github/agents/synax-q1-manuscript-author.agent.md) |
| **3** | **`@synax-academic-humanizer`** | Academic Humanizer & Editor | De-AI-ification (45+ clichés stripped), Burstiness CV & AMA 11th Ed. / Nature style | [.github/agents/synax-academic-humanizer.agent.md](.github/agents/synax-academic-humanizer.agent.md) |
| **4** | **`@synax-scie-peer-reviewer`** | SCIE 3-Referee Peer-Reviewer | Triple-blind referee simulation, 6-axis scorecard (0-100), auto-upgrade & Rebuttal | [.github/agents/synax-scie-peer-reviewer.agent.md](.github/agents/synax-scie-peer-reviewer.agent.md) |
| **5** | **`@synax-biostat-analyst`** | Biostatistical Meta-Analyst | DerSimonian-Laird ($\tau^2$, $Q$, $I^2$, 95% CI/PI, Power $1-\beta$) & Forest Plot | [.github/agents/synax-biostat-analyst.agent.md](.github/agents/synax-biostat-analyst.agent.md) |
| **6** | **`@synax-academic-researcher`** | Academic Scholar (PubMed) | Live NCBI PubMed E-Utilities, CrossRef DOIs, PICO, PRISMA 2020 & BibTeX | [.github/agents/synax-academic-researcher.agent.md](.github/agents/synax-academic-researcher.agent.md) |
| **7** | **`@synax-biomed-autocal`** | Biomedical Autocal ($V_{k+1}<V_k$) | Contractive Lyapunov-Kalman zero-drift calibration for ICU ECG, IBP & SpO2 | [.github/agents/synax-biomed-autocal.agent.md](.github/agents/synax-biomed-autocal.agent.md) |
| **8** | **`@synax-egraph-prover`** | E-Graph 0-ULP Prover | Equality saturation, 19-suite IEEE-754 interval proof & multi-silicon codegen | [.github/agents/synax-egraph-prover.agent.md](.github/agents/synax-egraph-prover.agent.md) |
| **9** | **`@synax-token-shield`** | Token Shield Optimizer | AST code skeletonizer & terminal log RLE deduplication (-88.4% token cut) | [.github/agents/synax-token-shield.agent.md](.github/agents/synax-token-shield.agent.md) |
| **10** | **`@synax-context-vault`** | Context Vault Handoff | Zero-token cross-agent memory handoffs via `<180` token SHA-256 capsules | [.github/agents/synax-context-vault.agent.md](.github/agents/synax-context-vault.agent.md) |
| **11** | **`@synax-fullstack-dev`** | Full-Stack & Silicon Architect | 5-Target Hardware Codegen (C11, ARM64 NEON, AVX2, MCU, LLVM IR) & TDD Suites | [.github/agents/synax-fullstack-dev.agent.md](.github/agents/synax-fullstack-dev.agent.md) |
| **12** | **`@synax-telegram-bot`** | Telegram Remote Operations | Mobile bot daemon (`@synax_compiler_bot`) & remote command dispatch | [.github/agents/synax-telegram-bot.agent.md](.github/agents/synax-telegram-bot.agent.md) |
| **13** | **`@synax-tycoon-architect`** | 3D Agent Office Coordinator | 2.5D/3D isometric diorama coordinator, PCB microkernel & task scheduling | [.github/agents/synax-tycoon-architect.agent.md](.github/agents/synax-tycoon-architect.agent.md) |

---

## 🛠️ Active MCP Server Tools (`office_mcp_server.py`)

- `synax_q1_full_publication_pipeline(topic, target_journal, equator_guideline)` — Runs the 5-Agent Q1 SCIE pipeline producing an 8-file camera-ready submission bundle.
- `synax_q1_manuscript_writer(topic, target_journal, equator_guideline)` — Authors a full Q1 IMRaD manuscript, sanitized LaTeX source, Cover Letter & EQUATOR checklist.
- `synax_academic_humanizer_editor(manuscript_text, target_journal_style)` — Removes 100% of AI clichés and calibrates burstiness while preserving all citations and numbers.
- `synax_scie_peer_review_simulator(manuscript_text, target_journal)` — Executes a 3-Referee blind peer review, auto-upgrades to `UNCONDITIONAL_ACCEPT_READY`, and writes the Rebuttal Letter.
- `synax_academic_literature_review(research_topic)` — Executes live PubMed/CrossRef search, dynamic PRISMA 2020 flow, and DerSimonian-Laird meta-analysis.
- `synax_office_multitask(prompt, target_agent_id)` — Dispatches tasks across all 8 agent desks in the SYNAX Agent Office.
- `synax_token_shield_compress(content)` — Saves 75%–92% tokens via AST skeletonization.
- `synax_context_vault_handoff(task_summary)` — Seals a `<180 token` SHA-256 memory capsule.
