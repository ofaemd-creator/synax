#!/usr/bin/env python3
"""
SYNAX ECC & Native Skill Bridge (`src/synax/ecc_bridge.py`)
===========================================================
Provides discovery of both local SYNAX skills (`skills/`) and external ECC
engineering skills and agents across macOS, Linux, and Windows.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

ECC_ROOT_CANDIDATES = [
    Path.home() / ".gemini" / "config" / "plugins" / "ecc",
    Path.home() / ".gemini" / "antigravity" / "scratch" / "ECC",
    Path.home() / "Desktop" / "AI modeller" / "SYNAX" / "ECC_becerileri",
    REPO_ROOT,
]

BUILTIN_FALLBACK_SKILLS: Dict[str, Dict[str, str]] = {
    "synax-compiler": {
        "description": "Compile, formally prove (Interval Abstract Interpretation), E-Graph saturate, and verify (.sx) kernels to C11, ARM64 NEON, x86 AVX2, LLVM IR, and Q16.16 MCU with 19-suite IEEE-754 0-ULP verification.",
        "doc": "# SYNAX Compiler Skill\nUse `./synax check`, `./synax prove`, `./synax egraph`, and `./synax compile`.",
    },
    "synax-telegram-bot": {
        "description": "Zero-dependency Telegram Bot & MCP remote agent skill bridging SYNAX, Claude Code, OpenAI Codex, and Google Antigravity to mobile Telegram commands (/check, /run, /egraph, /prove, /code).",
        "doc": "# SYNAX Telegram Bot Skill\nRun `./synax telegram --status` or `./synax telegram --poll`.",
    },
    "tdd-workflow": {
        "description": "Test-driven development (TDD) workflow: write a failing test first, implement minimal change to green, refactor with 19-suite IEEE-754 0-ULP verification.",
        "doc": "# TDD Workflow Skill\nWrite failing unit tests first, run `./synax test`, then implement.",
    },
    "security-review": {
        "description": "Comprehensive security review checklist: no hardcoded secrets, input validation, path sandboxing, and formal interval verification.",
        "doc": "# Security Review Skill\nValidate all inputs, keep secrets in env vars, verify intervals.",
    },
}


class ECCBridge:
    """Manages discovery, search, and procedural retrieval of SYNAX and ECC skills."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root = root_dir or self._detect_root()
        self.skills_dir = self.root / "skills" if self.root else None
        self.agents_dir = self.root / "agents" if self.root else None

    def _detect_root(self) -> Optional[Path]:
        for candidate in ECC_ROOT_CANDIDATES:
            if candidate.exists() and (candidate / "skills").is_dir():
                return candidate
        return REPO_ROOT if (REPO_ROOT / "skills").is_dir() else None

    def is_available(self) -> bool:
        return True

    def list_skills(self) -> List[str]:
        found = set(BUILTIN_FALLBACK_SKILLS.keys())
        for candidate in ECC_ROOT_CANDIDATES:
            sdir = candidate / "skills"
            if sdir.is_dir():
                for d in sdir.iterdir():
                    if d.is_dir() and (d / "SKILL.md").exists():
                        found.add(d.name)
        return sorted(found)

    def list_agents(self) -> List[str]:
        if not self.agents_dir or not self.agents_dir.exists():
            return ["planner", "tdd-guide", "code-reviewer", "security-reviewer"]
        return sorted([f.stem for f in self.agents_dir.glob("*.md")])

    def _locate_skill_file(self, skill_name: str) -> Optional[Path]:
        for candidate in ECC_ROOT_CANDIDATES:
            p = candidate / "skills" / skill_name / "SKILL.md"
            if p.exists():
                return p
        return None

    def search_skills(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search skills by name or description across disk and built-in fallbacks."""
        query_lower = query.lower().strip()
        results = []

        for skill_name in self.list_skills():
            skill_file = self._locate_skill_file(skill_name)
            desc = ""
            content = ""
            path_str = f"builtin://{skill_name}"

            if skill_file is not None:
                try:
                    content = skill_file.read_text(encoding="utf-8", errors="ignore")
                    m_desc = re.search(r"description:\s*(.+?)(?=\n[a-z_]+:|\n---)", content, re.S)
                    desc = m_desc.group(1).strip() if m_desc else ""
                    path_str = str(skill_file)
                except Exception:
                    pass

            if not desc and skill_name in BUILTIN_FALLBACK_SKILLS:
                desc = BUILTIN_FALLBACK_SKILLS[skill_name]["description"]
                content = BUILTIN_FALLBACK_SKILLS[skill_name]["doc"]

            score = 0
            if query_lower in skill_name.lower():
                score += 10
            if query_lower in desc.lower():
                score += 5
            if query_lower in content.lower():
                score += 1

            if score > 0:
                results.append({
                    "name": skill_name,
                    "description": desc,
                    "score": score,
                    "path": path_str,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_skill_doc(self, skill_name: str) -> Optional[str]:
        """Fetch the full markdown of a skill."""
        skill_file = self._locate_skill_file(skill_name)
        if skill_file and skill_file.exists():
            return skill_file.read_text(encoding="utf-8", errors="ignore")
        if skill_name in BUILTIN_FALLBACK_SKILLS:
            return BUILTIN_FALLBACK_SKILLS[skill_name]["doc"]
        return None

    def get_agent_spec(self, agent_name: str) -> Optional[str]:
        """Fetch the system prompt / role spec of an ECC agent."""
        if self.agents_dir:
            target = self.agents_dir / f"{agent_name}.md"
            if target.exists():
                return target.read_text(encoding="utf-8", errors="ignore")
        return None


_ecc_bridge: Optional[ECCBridge] = None


def get_ecc_bridge() -> ECCBridge:
    global _ecc_bridge
    if _ecc_bridge is None:
        _ecc_bridge = ECCBridge()
    return _ecc_bridge
