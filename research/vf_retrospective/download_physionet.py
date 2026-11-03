#!/usr/bin/env python3
"""
Download PhysioNet CUDB 1.0.0 and VFDB 1.0.0 (Open Data Commons Attribution License v1.0)
into `~/.cache/synax/physionet/` and record a SHA-256 manifest for reproducibility.

Data are NOT redistributed in this repository. Please cite:
  - Nolle FM et al. CREI-GARD... (CUDB), Computers in Cardiology 1986.
  - Greenwald SD. MIT-BIH Malignant Ventricular Arrhythmia Database (VFDB), 1986.
  - Goldberger AL et al. PhysioBank, PhysioToolkit, and PhysioNet. Circulation 2000;101(23):e215-e220.
"""

import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

CACHE_ROOT = Path.home() / ".cache" / "synax" / "physionet"
DATABASES = {
    "cudb": "https://physionet.org/files/cudb/1.0.0",
    "vfdb": "https://physionet.org/files/vfdb/1.0.0",
}


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "SYNAX-Research/0.5"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _get(task):
    base, rec, ext, out_dir = task
    target = out_dir / f"{rec}.{ext}"
    if not (target.exists() and target.stat().st_size > 0):
        target.write_bytes(_fetch(f"{base}/{rec}.{ext}"))
    data = target.read_bytes()
    return f"{rec}.{ext}", len(data), hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = {}
    for db, base in DATABASES.items():
        d = CACHE_ROOT / db
        d.mkdir(parents=True, exist_ok=True)
        rec_file = d / "RECORDS"
        if not rec_file.exists():
            rec_file.write_bytes(_fetch(f"{base}/RECORDS"))
        recs = [r.strip() for r in rec_file.read_text().splitlines() if r.strip()]
        tasks = [(base, r, ext, d) for r in recs for ext in ("hea", "dat", "atr")]
        files = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for name, size, sha in pool.map(_get, tasks):
                files[name] = {"bytes": size, "sha256": sha}
        manifest[db] = {"base_url": base, "records": recs, "files": files}
        print(f"[{db}] {len(recs)} records, {len(files)} files OK")
    (CACHE_ROOT / "physionet_sha256_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {CACHE_ROOT / 'physionet_sha256_manifest.json'}")


if __name__ == "__main__":
    main()
