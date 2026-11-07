#!/usr/bin/env python3
"""
SYNAX ECC (Engineering & Coding Capabilities) Bridge
===================================================
Provides deep integration between SYNAX and the 314 ECC engineering skills
and 71 specialized agents (cloned from https://github.com/affaan-m/ECC.git).

Enables:
  - Instant discovery of any ECC skill or agent.
  - Integration of TDD workflows, verification loops, and security reviews
    into SYNAX compiler generation and biomedical signal processing.
  - Native dispatch from the SYNAX chat REPL, LSP, and Swift bridge.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ECC_ROOT_CANDIDATES = [
    Path.home() / ".gemini" / "config" / "plugins" / "ecc",
    Path.home() / ".gemini" / "antigravity" / "scratch" / "ECC",
    Path.home() / "Desktop" / "AI modeller" / "SYNAX" / "ECC_becerileri",
]


class ECCBridge:
    """Manages discovery, search, and procedural retrieval of ECC skills and agents."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root = root_dir or self._detect_root()
        self.skills_dir = self.root / "skills" if self.root else None
        self.agents_dir = self.root / "agents" if self.root else None

    def _detect_root(self) -> Optional[Path]:
        for candidate in ECC_ROOT_CANDIDATES:
            if candidate.exists() and (candidate / "skills").is_dir():
                return candidate
        return None

    def is_available(self) -> bool:
        return self.skills_dir is not None and self.skills_dir.is_dir()

    def list_skills(self) -> List[str]:
        if not self.skills_dir or not self.skills_dir.exists():
            return []
        return sorted([d.name for d in self.skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])

    def list_agents(self) -> List[str]:
        if not self.agents_dir or not self.agents_dir.exists():
            return []
        return sorted([f.stem for f in self.agents_dir.glob("*.md")])

    def search_skills(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search ECC skills by name or description."""
        query_lower = query.lower().strip()
        results = []

        for skill_name in self.list_skills():
            skill_file = self.skills_dir / skill_name / "SKILL.md"
            try:
                content = skill_file.read_text(encoding="utf-8", errors="ignore")
                # Parse description from frontmatter
                m_desc = re.search(r"description:\s*(.+?)(?=\n[a-z_]+:|\n---)", content, re.S)
                desc = m_desc.group(1).strip() if m_desc else ""

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
                        "path": str(skill_file),
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_skill_doc(self, skill_name: str) -> Optional[str]:
        """Fetch the full markdown of a skill."""
        if not self.skills_dir:
            return None
        target = self.skills_dir / skill_name / "SKILL.md"
        if target.exists():
            return target.read_text(encoding="utf-8", errors="ignore")
        return None

    def get_agent_spec(self, agent_name: str) -> Optional[str]:
        """Fetch the system prompt / role spec of an ECC agent."""
        if not self.agents_dir:
            return None
        target = self.agents_dir / f"{agent_name}.md"
        if target.exists():
            return target.read_text(encoding="utf-8", errors="ignore")
        return None


# Global singleton instance
_ecc_bridge: Optional[ECCBridge] = None


def get_ecc_bridge() -> ECCBridge:
    global _ecc_bridge
    if _ecc_bridge is None:
        _ecc_bridge = ECCBridge()
    return _ecc_bridge
