"""Strict JSONL ingestion and assistant-only training targets."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path

import torch
from torch import Tensor

from .tokenizer import BOS, END, ROLES, Message


def load_records(path: Path) -> list[list[Message]]:
    """Parse conversational JSONL; reject missing/unknown roles and empty assistants."""
    records: list[list[Message]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict) or not isinstance(record.get("messages"), list):
            raise ValueError("Each JSONL record must contain a messages array")
        messages: list[Message] = []
        for raw in record["messages"]:
            if (
                not isinstance(raw, dict)
                or not isinstance(raw.get("role"), str)
                or raw.get("role") not in ROLES
                or not isinstance(raw.get("content"), str)
            ):
                raise ValueError("Invalid conversation message")
            if not raw["content"].strip():
                raise ValueError("Empty conversation content")
            messages.append({"role": raw["role"], "content": raw["content"]})
        if (
            not messages
            or messages[-1]["role"] != "assistant"
            or not any(m["role"] == "user" for m in messages)
        ):
            raise ValueError(
                "Training record needs a user turn and a final assistant response"
            )
        records.append(messages)
    if not records:
        raise ValueError("Training dataset is empty")
    return records


def record_hash(messages: list[Message]) -> str:
    return hashlib.sha256(
        json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def tensorize(records: list[list[Message]], context: int) -> tuple[Tensor, Tensor]:
    """Keep each record intact; mask user/system tokens and padding from the loss."""
    inputs, targets = [], []
    for messages in records:
        tokens, labels = [BOS], [-100]
        for message in messages:
            part = [ROLES[message["role"]], *message["content"].encode("utf-8"), END]
            tokens.extend(part)
            labels.extend(
                [-100, *part[1:]]
                if message["role"] == "assistant"
                else [-100] * len(part)
            )
        if len(tokens) > context + 1:
            raise ValueError(
                f"Training record exceeds context ({len(tokens)} > {context + 1}); shorten or increase context"
            )
        padding = context + 1 - len(tokens)
        tokens.extend([END] * padding)
        labels.extend([-100] * padding)
        inputs.append(tokens[:-1])
        targets.append(labels[1:])
    return torch.tensor(inputs, dtype=torch.long), torch.tensor(
        targets, dtype=torch.long
    )
