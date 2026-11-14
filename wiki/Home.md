# 🧬 SYNAX (`v1.0.0`) Official Wiki

Welcome to the official **SYNAX (`v1.0.0`)** documentation and technical wiki.

SYNAX (`.sx`) is a verified neuro-symbolic kernel programming language, multi-target silicon compiler (`C11`, `ARM64 NEON`, `x86_64 AVX2`, `LLVM IR`, `Q16.16 MCU`), and autonomous software engineering workbench (`SYNAX Studio IDE` & `./synax code`).

---

## 📚 Wiki Contents

1. **[SYNAX 1.0 Language Reference](Language-Reference-v1.0)** — Canonical `.sx` syntax, `select()` branchless mux, `fma()`, multi-`let` bindings, dendritic reductions, and `safety` blocks.
2. **[E-Graph Equality Saturation & Formal Interval Prover](E-Graph-and-Formal-Prover)** — Non-destructive equivalence graph saturation (`src/synax/egraph.py`) and static IEEE-754 interval abstract interpretation (`src/synax/formal_prover.py`).
3. **[SYNAX Studio IDE & Autonomous Coding Agent](Autonomous-Coding-Agent)** — Running `./synax studio` (`/Applications/SYNAX Studio.app`), VS Code Full-Screen Studio mode, and the `./synax code` tool-calling agent (`src/synax/agent.py`).
4. **[Universal AI Plugin Ecosystem (Claude, Codex, Antigravity, Cursor)](Plugin-Ecosystem-Claude-Codex-Antigravity)** — Using SYNAX inside Claude Code, OpenAI Codex CLI, Google Antigravity, Cursor IDE, and OpenCode via MCP and native skills.

---

## ⚡ Quick Start

```bash
# 1. Check & formally verify a .sx kernel
./synax check examples/synax_v1_showcase.sx

# 2. Compile & execute with 19-suite IEEE-754 0-ULP verification
./synax run examples/synax_v1_showcase.sx

# 3. Launch SYNAX Studio IDE (Standalone Application)
./synax studio

# 4. Launch Autonomous Coding Agent
./synax code
```
