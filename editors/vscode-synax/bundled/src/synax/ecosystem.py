"""
SYNAX Universal AI Ecosystem & Plugin Installer (`src/synax/ecosystem.py`)
==========================================================================
Generates and installs native SYNAX v1.0.0 compiler, E-Graph optimizer,
Formal Interval Prover, and MCP server integrations for:
  1. Google Antigravity (`~/.gemini/config/plugins/synax/` & `plugins/antigravity/`)
  2. Claude Code (`.claude-plugin/plugin.json`, `.mcp.json`, `CLAUDE.md`)
  3. OpenAI Codex CLI (`AGENTS.md`, `.codex/config.toml`)
  4. Cursor IDE (`.cursor/mcp.json`, `.cursor/rules/synax.mdc`)
  5. OpenCode (`opencode.json`)

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable or "/usr/bin/env python3"


SKILL_MARKDOWN = """---
name: synax-compiler
description: Compile, formally prove (Interval Abstract Interpretation), E-Graph saturate, and verify (.sx) kernels to C11, ARM64 NEON, x86 AVX2, LLVM IR, and Q16.16 MCU with 19-suite IEEE-754 0-ULP verification.
---

# SYNAX v1.0.0 Compiler, Formal Prover & E-Graph Engine

Use this skill whenever the user works with `.sx` kernels, high-assurance numerical/signal processing, embedded MCU fixed-point (`Q16.16`) codegen, SIMD vectorization (`ARM64 NEON` / `x86 AVX2`), or formal interval verification.

## Core Capabilities

1. **Check & Type-Verify `.sx` Kernels:**
   ```bash
   python3 synax_cli.py check examples/synax_v1_showcase.sx
   ```
2. **Execute & Benchmark `.sx` Kernels (19-Suite 0-ULP Differential Check):**
   ```bash
   python3 synax_cli.py run examples/synax_v1_showcase.sx
   ```
3. **E-Graph Equality Saturation & Formal Interval Proof (Python SDK):**
   ```python
   import synax
   from synax.egraph import saturate_and_extract
   from synax.formal_prover import prove_kernel_safety

   ir = synax.check_sx("examples/synax_v1_showcase.sx")
   eg = saturate_and_extract(ir.expr, target="neon")
   cert = prove_kernel_safety(ir, (-500.0, 500.0), (-500.0, 500.0))
   ```
4. **Autonomous Coding Agent (`./synax code`):**
   ```bash
   ./synax code "Inspect examples/ and verify all .sx kernels"
   ```
"""


def install_all_ecosystem_integrations(root: Path = REPO_ROOT) -> Dict[str, Any]:
    """Write workspace and user-level plugin manifests for Antigravity, Claude, Codex, Cursor, and OpenCode."""
    installed: List[Dict[str, str]] = []
    mcp_cmd = PYTHON_BIN
    mcp_args = [str(root / "synax_cli.py"), "mcp"]

    # 1. Claude Code (.mcp.json, .claude-plugin/plugin.json, CLAUDE.md)
    mcp_json_path = root / ".mcp.json"
    mcp_payload = {
        "mcpServers": {
            "synax": {
                "command": mcp_cmd,
                "args": mcp_args,
                "env": {"PYTHONPATH": f"{root}:{root / 'src'}"},
            }
        }
    }
    mcp_json_path.write_text(json.dumps(mcp_payload, indent=2) + "\n", encoding="utf-8")
    installed.append({"platform": "Claude Code (MCP)", "path": str(mcp_json_path)})

    claude_plugin_dir = root / ".claude-plugin"
    claude_plugin_dir.mkdir(parents=True, exist_ok=True)
    claude_plugin_json = claude_plugin_dir / "plugin.json"
    claude_plugin_json.write_text(
        json.dumps(
            {
                "name": "synax",
                "version": "1.0.0",
                "description": "SYNAX v1.0.0 Compiler, E-Graph Optimizer, Formal Interval Prover & 0-ULP Silicon Verifier",
                "author": {"name": "Dr. Ömer Faruk Aydın"},
                "skills": "./skills",
                "mcpServers": "../.mcp.json",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    installed.append({"platform": "Claude Code Plugin", "path": str(claude_plugin_json)})

    claude_md = root / "CLAUDE.md"
    claude_md.write_text(
        "# CLAUDE.md — SYNAX v1.0.0 Workspace Guide\n\n"
        "- **Language & Compiler**: `src/synax/` (`parser.py`, `type_system.py`, `egraph.py`, `formal_prover.py`, `backends/`).\n"
        "- **Autonomous Agent**: `src/synax/agent.py` (`./synax code`).\n"
        "- **Studio Application**: `src/synax/studio_app.py` (`./synax studio` or `/Applications/SYNAX Studio.app`).\n"
        "- **Verification**: Run `./synax test` or `python3 tests/test_language_v1.py`.\n",
        encoding="utf-8",
    )
    installed.append({"platform": "Claude Code Memory (CLAUDE.md)", "path": str(claude_md)})

    # 2. OpenAI Codex CLI (AGENTS.md & .codex/config.toml)
    agents_md = root / "AGENTS.md"
    agents_md.write_text(
        "# AGENTS.md — OpenAI Codex & Multi-Agent Instructions for SYNAX v1.0.0\n\n"
        "## Overview\n"
        "SYNAX (`.sx`) is a verified kernel language and compiler with E-Graph Equality Saturation (`src/synax/egraph.py`), "
        "Formal Interval Abstract Interpretation (`src/synax/formal_prover.py`), and 19-suite IEEE-754 0-ULP verification.\n\n"
        "## Commands\n"
        "- Check `.sx` file: `./synax check <file.sx>`\n"
        "- Compile & Run 0-ULP: `./synax run <file.sx>`\n"
        "- Launch SYNAX Studio App: `./synax studio`\n"
        "- Run coding agent: `./synax code`\n"
        "- Run test suite: `./synax test`\n",
        encoding="utf-8",
    )
    codex_dir = root / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    codex_toml = codex_dir / "config.toml"
    codex_toml.write_text(
        f'[mcp_servers.synax]\ncommand = "{mcp_cmd}"\nargs = ["{root / "synax_cli.py"}", "mcp"]\n',
        encoding="utf-8",
    )
    installed.append({"platform": "OpenAI Codex CLI", "path": str(codex_toml)})

    # 3. Cursor IDE (.cursor/mcp.json & .cursor/rules/synax.mdc)
    cursor_dir = root / ".cursor"
    cursor_rules = cursor_dir / "rules"
    cursor_rules.mkdir(parents=True, exist_ok=True)
    (cursor_dir / "mcp.json").write_text(json.dumps(mcp_payload, indent=2) + "\n", encoding="utf-8")
    (cursor_rules / "synax.mdc").write_text(
        "---\ndescription: SYNAX v1.0.0 Language, E-Graph & Formal Prover Rules\nglobs: **/*.sx, **/*.py\n---\n\n"
        + SKILL_MARKDOWN,
        encoding="utf-8",
    )
    installed.append({"platform": "Cursor IDE", "path": str(cursor_dir / "mcp.json")})

    # 4. OpenCode (opencode.json)
    opencode_json = root / "opencode.json"
    opencode_json.write_text(
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "mcp": {
                    "synax": {
                        "type": "local",
                        "command": [mcp_cmd, str(root / "synax_cli.py"), "mcp"],
                        "enabled": True,
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    installed.append({"platform": "OpenCode CLI", "path": str(opencode_json)})

    # 5. Google Antigravity Plugin (~/.gemini/config/plugins/synax/ & repo skills/synax-compiler/)
    repo_skill_dir = root / "skills" / "synax-compiler"
    repo_skill_dir.mkdir(parents=True, exist_ok=True)
    (repo_skill_dir / "SKILL.md").write_text(SKILL_MARKDOWN, encoding="utf-8")

    agy_plugin_dir = Path.home() / ".gemini" / "config" / "plugins" / "synax"
    try:
        (agy_plugin_dir / "skills" / "synax-compiler").mkdir(parents=True, exist_ok=True)
        (agy_plugin_dir / "rules").mkdir(parents=True, exist_ok=True)
        (agy_plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "synax",
                    "version": "1.0.0",
                    "description": "SYNAX v1.0.0 Compiler, E-Graph Equality Saturation, Formal Interval Prover & 0-ULP Verifier",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (agy_plugin_dir / "skills" / "synax-compiler" / "SKILL.md").write_text(SKILL_MARKDOWN, encoding="utf-8")
        (agy_plugin_dir / "rules" / "AGENTS.md").write_text(
            "# SYNAX Compiler & Formal Verification Guidelines\n\n"
            "- For `.sx` kernel optimization and hardware code generation (ARM64 NEON, AVX2, LLVM IR, Q16.16 MCU), use `synax` (`src/synax/egraph.py` and `src/synax/formal_prover.py`).\n",
            encoding="utf-8",
        )
        installed.append({"platform": "Google Antigravity Plugin", "path": str(agy_plugin_dir)})
    except Exception:
        installed.append({"platform": "Google Antigravity Skill (Repo)", "path": str(repo_skill_dir / "SKILL.md")})

    return {"installed_count": len(installed), "integrations": installed}
