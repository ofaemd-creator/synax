"""Compatibility response envelope for CLI and editor clients."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ChatResponse:
    text: str
    code: Optional[str] = None
    language: str = "synax"
    action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "code": self.code,
            "language": self.language,
            "action": self.action,
            "metadata": self.metadata or {},
        }
