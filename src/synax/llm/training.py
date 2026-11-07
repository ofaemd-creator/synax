"""Reproducible, from-scratch training with separate held-out evaluation."""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.nn import functional as F

from .data import load_records, record_hash, tensorize
from .model import ModelSpec, SynaxTransformer


@dataclass(frozen=True, slots=True)
class TrainingRun:
    data: Path
    validation: Path
    output: Path
    steps: int = 200
    seed: int = 42
    device: str = "cpu"


def train(run: TrainingRun, spec: ModelSpec) -> dict[str, float | int | str]:
    """Train owned weights; refuse dataset overlap and overwrite of existing checkpoints."""
    if not 1 <= run.steps <= 1000000:
        raise ValueError("steps must be in 1..1000000")
    if run.output.exists():
        raise ValueError("Output directory already exists; choose a new run directory")
    train_records, val_records = load_records(run.data), load_records(run.validation)
    if {record_hash(r) for r in train_records} & {record_hash(r) for r in val_records}:
        raise ValueError("Training and validation records overlap")
    torch.manual_seed(run.seed)
    torch.set_num_threads(2)
    device = torch.device(run.device)
    model = SynaxTransformer(spec).to(device)
    x, y = (t.to(device) for t in tensorize(train_records, spec.context))
    vx, vy = (t.to(device) for t in tensorize(val_records, spec.context))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)

    def loss_on(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return F.cross_entropy(
            model(a).reshape(-1, spec.vocab), b.reshape(-1), ignore_index=-100
        )

    model.eval()
    with torch.no_grad():
        initial_train = float(loss_on(x, y).item())
        initial_val = float(loss_on(vx, vy).item())
    model.train()
    for _ in range(run.steps):
        indices = torch.randint(len(x), (min(8, len(x)),), device=device)
        loss = loss_on(x[indices], y[indices])
        if not torch.isfinite(loss):
            raise ValueError("Non-finite training loss; checkpoint not saved")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        final_train = float(loss_on(x, y).item())
        final_val = float(loss_on(vx, vy).item())
    run.output.mkdir(parents=True)
    torch.save(
        {k: v.cpu() for k, v in model.state_dict().items()}, run.output / "weights.pt"
    )
    report = {
        "parameters": sum(p.numel() for p in model.parameters()),
        "steps": run.steps,
        "seed": run.seed,
        "device": run.device,
        "train_records": len(train_records),
        "validation_records": len(val_records),
        "initial_train_loss": initial_train,
        "final_train_loss": final_train,
        "initial_validation_loss": initial_val,
        "final_validation_loss": final_val,
        "dataset_sha256": hashlib.sha256(run.data.read_bytes()).hexdigest(),
        "validation_sha256": hashlib.sha256(run.validation.read_bytes()).hexdigest(),
        "weights_sha256": hashlib.sha256(
            (run.output / "weights.pt").read_bytes()
        ).hexdigest(),
    }
    (run.output / "config.json").write_text(
        json.dumps(
            {
                "name": "SynaxLLM",
                "stage": "experimental-bootstrap",
                "architecture": spec.to_dict(),
                "tokenizer": "utf8-byte-v1",
                "training": report,
            },
            indent=2,
        )
        + "\n"
    )
    return report
