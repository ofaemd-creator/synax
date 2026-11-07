"""Offline inference from explicitly selected SYNAX checkpoints."""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
import os
from pathlib import Path
from threading import Lock

import torch

from .model import ModelSpec, SynaxTransformer
from .tokenizer import END, Message, decode, encode


class ModelUnavailable(RuntimeError):
    """A local model cannot be loaded or used."""


@dataclass(frozen=True, slots=True)
class Generation:
    text: str
    completion_tokens: int
    finish_reason: str


class LocalModel:
    """Owns one model; serializes generation so threads do not share mutable RNG state."""

    def __init__(self, directory: Path) -> None:
        try:
            metadata = json.loads((directory / "config.json").read_text())
            self.spec = ModelSpec(**metadata["architecture"])
            self.name = metadata["name"]
            self.stage = metadata["stage"]
            expected = metadata["training"]["weights_sha256"]
            if (
                hashlib.sha256((directory / "weights.pt").read_bytes()).hexdigest()
                != expected
            ):
                raise ModelUnavailable(
                    "Checkpoint SHA-256 bütünlük kontrolü başarısız."
                )
            self.model = SynaxTransformer(self.spec)
            state = torch.load(
                directory / "weights.pt", map_location="cpu", weights_only=True
            )
            self.model.load_state_dict(state)
            self.model.eval()
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            raise ModelUnavailable(
                "SynaxLLM checkpoint yüklenemedi; eğitim çıktısını kontrol edin."
            ) from error
        self.lock = Lock()
        torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))

    def generate(self, messages: list[Message], max_tokens: int = 128) -> str:
        return self.generate_result(messages, max_tokens).text

    def generate_result(
        self, messages: list[Message], max_tokens: int = 128
    ) -> Generation:
        """Generate greedily on CPU with bounded context and output, without network access."""
        if not 1 <= max_tokens <= 1024:
            raise ModelUnavailable("max_tokens 1–1024 arasında olmalıdır.")
        tokens = encode(messages, generation=True)
        # Preserve complete latest user turn; never silently discard task instructions.
        if len(tokens) > self.spec.context:
            raise ModelUnavailable(
                f"İleti modelin {self.spec.context} token bağlamını aşıyor; daha kısa yazın veya daha büyük model eğitin."
            )
        generated: list[int] = []
        finish = "length"
        with self.lock, torch.inference_mode():
            for _ in range(max_tokens):
                window = tokens[-self.spec.context :]
                logits = self.model(torch.tensor([window], dtype=torch.long))[:, -1, :]
                logits[:, 256:259] = float("-inf")
                logits[:, 260:] = float("-inf")
                token = int(logits.argmax(dim=-1).item())
                if token == END:
                    finish = "stop"
                    break
                generated.append(token)
                tokens.append(token)
        text = decode(generated).strip()
        if not text:
            raise ModelUnavailable(
                "Model anlamlı metin üretmedi. Daha fazla eğitim ve değerlendirme gerekiyor."
            )
        return Generation(text, len(generated) + int(finish == "stop"), finish)
