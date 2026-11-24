#!/usr/bin/env python3
"""
SYNAX-Core Continuous Distillation & Local Transformer Trainer (`scripts/train_synax_core_from_cloud.py`)
===========================================================================================================
Pulls newly distilled, 0-ULP verified Q&A pairs from `chat.synaxcode.com/api.php?action=core_corpus_export_jsonl`
using your local Sovereign Founder credentials (`~/.synax/sovereign_credentials.json`), splits train/validation
without overlap, and runs a real PyTorch `SynaxTransformer` training cycle saving a versioned checkpoint under
`~/.synax/core_checkpoints/`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

from synax.llm.model import ModelSpec
from synax.llm.training import TrainingRun, train


def _totp(secret_b32: str) -> str:
    key = base64.b32decode(secret_b32)
    h = hmac.new(key, struct.pack(">Q", int(time.time()) // 30), hashlib.sha1).digest()
    o = h[19] & 0xF
    return str((struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF) % 1000000).zfill(6)


def _post(url: str, body: dict, token: str = "") -> dict:
    headers = {"Content-Type": "application/json", "User-Agent": "SYNAX-Core-Trainer/9.0"}
    if token:
        headers["X-Synax-Sovereign-Token"] = token
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    cred_path = Path.home() / ".synax" / "sovereign_credentials.json"
    cred = json.loads(cred_path.read_text())
    auth = _post(
        "https://chat.synaxcode.com/api.php?action=verify_sovereign",
        {"action": "verify_sovereign", "sovereign_passkey": cred["passkey"], "totp_code": _totp(cred["totp_secret_base32"])},
    )
    tok = auth["sovereign_token"]
    exp = _post("https://chat.synaxcode.com/api.php?action=core_corpus_export_jsonl", {"action": "core_corpus_export_jsonl"}, tok)
    raw_lines = [ln for ln in (exp.get("jsonl") or "").splitlines() if ln.strip()]

    # Seed baseline sovereign samples if cloud corpus has < 4 samples yet
    seed_samples = [
        {"prompt": "SYNAX-Core nedir?", "completion": "SYNAX-Core, Dr. Omer Faruk Aydin tarafindan gelistirilen 0-ULP dogrulamali sinirsel-sembolik cekirdek dil modelidir."},
        {"prompt": "Lyapunov V_{k+1} < V_k ne saglar?", "completion": "Biyomedikal EKG ve IBP sensorlerinde bazal kaymayi monotonik olarak sifira yakinsatarak sifir-sapma kalibrasyonu saglar."},
        {"prompt": "PRISMA 2020 sistematik derleme adimlari nelerdir?", "completion": "PICO tanimi, 2025-2026 guncel PubMed/EuropePMC/CrossRef taramasi, cift kor eleme, RoB-2 yanlilik analizi ve DerSimonian-Laird meta-analizi."},
        {"prompt": "0-ULP IEEE-754 kaniti nedir?", "completion": "Aralik soyut yorumlama ile sifira bolme, tasma ve NaN/Inf hatalarinin matematiksel olarak imkansiz oldugunu ispatlar."},
    ]
    records = [json.loads(ln) for ln in raw_lines] + seed_samples
    # Deduplicate by prompt
    seen, unique_recs = set(), []
    for r in records:
        k = (r.get("prompt", "").strip().lower(), r.get("completion", "").strip().lower())
        if k not in seen and r.get("prompt") and r.get("completion"):
            seen.add(k)
            unique_recs.append({"text": f"USER: {r['prompt']}\nSYNAX-CORE: {r['completion']}"})

    ts = time.strftime("%Y%m%d_%H%M%S")
    work = Path.home() / ".synax" / "core_checkpoints" / f"run_{ts}"
    data_dir = work / "datasets"
    data_dir.mkdir(parents=True, exist_ok=True)
    split = max(1, int(len(unique_recs) * 0.75))
    train_file = data_dir / "train.jsonl"
    val_file = data_dir / "val.jsonl"
    train_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in unique_recs[:split]) + "\n")
    val_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in unique_recs[split:]) + "\n")

    spec = ModelSpec(context=256, width=128, heads=4, layers=3)
    report = train(TrainingRun(data=train_file, validation=val_file, output=work / "checkpoint", steps=40, seed=42, device="cpu"), spec)
    print("SYNAX-CORE TRAINING COMPLETE:", json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
