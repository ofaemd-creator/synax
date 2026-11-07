"""SYNAX-owned decoder-only causal transformer; initialized from random weights."""

from __future__ import annotations
from dataclasses import asdict, dataclass

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .tokenizer import VOCAB_SIZE


@dataclass(frozen=True, slots=True)
class ModelSpec:
    context: int = 256
    width: int = 128
    heads: int = 4
    layers: int = 3
    vocab: int = VOCAB_SIZE

    def __post_init__(self) -> None:
        if not (
            32 <= self.context <= 4096
            and 32 <= self.width <= 2048
            and 1 <= self.layers <= 24
            and 1 <= self.heads <= 32
            and self.width % self.heads == 0
            and self.vocab == VOCAB_SIZE
        ):
            raise ValueError("Invalid SynaxLLM architecture specification")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


class Block(nn.Module):
    """Pre-normalized causal attention and feed-forward residual block."""

    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        self.heads = spec.heads
        self.norm_attention = nn.LayerNorm(spec.width)
        self.qkv = nn.Linear(spec.width, 3 * spec.width, bias=False)
        self.projection = nn.Linear(spec.width, spec.width, bias=False)
        self.norm_ffn = nn.LayerNorm(spec.width)
        self.ffn = nn.Sequential(
            nn.Linear(spec.width, 4 * spec.width),
            nn.GELU(),
            nn.Linear(4 * spec.width, spec.width),
        )

    def forward(self, x: Tensor) -> Tensor:
        batch, length, width = x.shape
        q, k, v = self.qkv(self.norm_attention(x)).chunk(3, dim=-1)
        q, k, v = [
            t.view(batch, length, self.heads, width // self.heads).transpose(1, 2)
            for t in (q, k, v)
        ]
        attention = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.projection(
            attention.transpose(1, 2).contiguous().view(batch, length, width)
        )
        return x + self.ffn(self.norm_ffn(x))


class SynaxTransformer(nn.Module):
    """Small scalable decoder; the bootstrap configuration is NOT a capable large model."""

    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        self.spec = spec
        self.embedding = nn.Embedding(spec.vocab, spec.width)
        self.positions = nn.Embedding(spec.context, spec.width)
        self.blocks = nn.Sequential(*(Block(spec) for _ in range(spec.layers)))
        self.norm = nn.LayerNorm(spec.width)
        self.output = nn.Linear(spec.width, spec.vocab, bias=False)
        self.output.weight = self.embedding.weight
        self.apply(self._initialize)

    @staticmethod
    def _initialize(module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, tokens: Tensor) -> Tensor:
        length = tokens.shape[1]
        if length > self.spec.context:
            raise ValueError("Input exceeds model context")
        x = self.embedding(tokens) + self.positions(
            torch.arange(length, device=tokens.device)
        )
        return self.output(self.norm(self.blocks(x)))
