# AGENTS.md — OpenAI Codex & Multi-Agent Instructions for SYNAX v1.0.0

## Overview
SYNAX (`.sx`) is a verified kernel language and compiler with E-Graph Equality Saturation (`src/synax/egraph.py`), Formal Interval Abstract Interpretation (`src/synax/formal_prover.py`), and 19-suite IEEE-754 0-ULP verification.

## Commands
- Check `.sx` file: `./synax check <file.sx>`
- Compile & Run 0-ULP: `./synax run <file.sx>`
- Launch SYNAX Studio App: `./synax studio`
- Run coding agent: `./synax code`
- Run test suite: `./synax test`
