"""
SYNAX Assistant Conversation Harness (`src/synax/assistant/conversation.py`)
=============================================================================
Provides a resilient, multi-tiered conversation session backed by:
  1. Local SynaxLLM Transformer (when trained checkpoints are configured).
  2. Multi-tier Hybrid Router (OpenCode / Free Models / Domain Expert).
Never crashes with fatal errors; automatically filters gibberish byte sampling.

SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from synax.llm.tokenizer import Message, encode

if TYPE_CHECKING:
    from synax.llm.runtime import LocalModel


class ModelError(RuntimeError):
    """The owned model is not ready for inference."""


def is_coherent(text: str) -> bool:
    """Detect repetitive token/byte loop gibberish from untrained or overfitting models."""
    if not text or len(text.strip()) < 3:
        return False
    words = text.strip().split()
    if len(words) >= 4:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.35:
            return False
        # Check repeated sub-word sequences (e.g. nimonimoyimeliko)
        for w in words:
            if len(w) > 14:
                sub = w[:4]
                if w.count(sub) >= 3:
                    return False
    return True


class Conversation:
    """Mutable bounded session with resilient hybrid routing and fallback."""

    def __init__(self) -> None:
        self.history: list[Message] = []
        self.model: Optional[LocalModel] = None
        self._router = None

    def reset(self) -> None:
        self.history.clear()

    def _get_router(self):
        if self._router is None:
            try:
                from synax.chat_router import HybridLLMRouter
                self._router = HybridLLMRouter()
            except Exception:
                self._router = None
        return self._router

    def reply(self, text: str, scientific: bool = False) -> tuple[str, str]:
        """Run local inference or resilient hybrid router; never crash with fatal error."""
        text_clean = text.strip()
        if not text_clean or len(text_clean) > 32000:
            raise ModelError("Mesaj 1–32.000 karakter arasında olmalıdır.")

        # 1. Attempt local model inference if SYNAX_MODEL_PATH is configured
        directory = os.environ.get("SYNAX_MODEL_PATH", "").strip()
        if directory and Path(directory).expanduser().exists():
            if self.model is None:
                try:
                    from synax.llm.runtime import LocalModel
                    self.model = LocalModel(Path(directory).expanduser())
                except Exception:
                    self.model = None

            if self.model is not None:
                try:
                    user: Message = {"role": "user", "content": text_clean}
                    history = self.history[-20:]
                    while (
                        history
                        and len(encode([*history, user], generation=True)) > self.model.spec.context
                    ):
                        history = history[2:]
                    answer = self.model.generate([*history, user])
                    if is_coherent(answer):
                        self.history = [*history, user, {"role": "assistant", "content": answer}]
                        return answer, "scientific_chat" if scientific else "general_chat"
                except Exception:
                    pass

        # 2. Resilient Hybrid Router Fallback (OpenCode Free Models / Built-in Domain Expert)
        router = self._get_router()
        if router is not None:
            ans_text, code = router.query(text_clean)
            if code:
                ans_text = f"{ans_text}\n\n```{code}```"
            user_msg: Message = {"role": "user", "content": text_clean}
            self.history.append(user_msg)
            self.history.append({"role": "assistant", "content": ans_text})
            if len(self.history) > 20:
                self.history = self.history[-20:]
            return ans_text, "scientific_chat" if scientific else "general_chat"

        # 3. Static fallback
        fallback_msg = (
            "Merhaba! SYNAX Nöro-Sembolik Derleyici Asistanı devrede.\n"
            "Becerileri listelemek için `hafızanı göster`, donanım için `durum` yazabilirsiniz."
        )
        return fallback_msg, "general_chat"
