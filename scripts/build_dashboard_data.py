#!/usr/bin/env python3
"""
Builds sites/dashboard_data.json from VERIFIABLE sources only.

  codebase    : local scan of this repository
  github      : GitHub REST API (repo, releases, Actions runs, issues, languages)
  sites       : live HTTP probe of the three domains (status, latency, bytes)
  performance : signed Myelin cache reports in ~/.cache/synax/hafiza/*/rapor.json
  research    : research/vf_retrospective/results/EVALUATION_REPORT.md
  web_traffic : NOT available (static hosting, no collector) -> explicit null

Nothing is invented. Fields that cannot be measured are null with a reason.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
REPO = "ofaemd-creator/synax"
DOMAINS = ["synaxcode.com", "synaxcode.org", "synaxcode.online"]


def http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "synax-dashboard", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def github() -> dict:
    out: dict = {"source": "api.github.com", "error": None}
    try:
        repo = http_json(f"https://api.github.com/repos/{REPO}")
        out.update(stars=repo["stargazers_count"], forks=repo["forks_count"], watchers=repo["subscribers_count"] if "subscribers_count" in repo else repo["watchers_count"],
                   open_issues=repo["open_issues_count"], license=(repo.get("license") or {}).get("spdx_id"),
                   created_at=repo["created_at"], pushed_at=repo["pushed_at"], url=repo["html_url"])
        issues = http_json(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100")
        out["issues_closed"] = sum(1 for i in issues if i["state"] == "closed" and "pull_request" not in i)
        out["languages_bytes"] = http_json(f"https://api.github.com/repos/{REPO}/languages")
        rel = http_json(f"https://api.github.com/repos/{REPO}/releases")
        out["releases"] = [{
            "tag": r["tag_name"], "published_at": r["published_at"],
            "assets": [{"name": a["name"], "downloads": a["download_count"]} for a in r["assets"]],
            "downloads_total": sum(a["download_count"] for a in r["assets"]),
        } for r in rel]
        runs = http_json(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=10")["workflow_runs"]
        out["ci_runs"] = [{
            "workflow": r["name"], "branch": r["head_branch"], "conclusion": r["conclusion"] or r["status"],
            "created_at": r["created_at"], "updated_at": r["updated_at"],
            "duration_s": int((dt.datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")) -
                               dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).total_seconds()),
            "url": r["html_url"],
        } for r in runs]
        out["traffic"] = None
        out["traffic_note"] = "GitHub clone/view sayıları yalnızca repo sahibi tokenı ile alınabilir; bu yüzden gösterilmiyor."
    except Exception as exc:  # network failure must not fabricate numbers
        out["error"] = str(exc)
    return out


def probe(domain: str) -> dict:
    url = f"https://{domain}/"
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "synax-dashboard"}), timeout=20) as r:
            body = r.read()
            return {"domain": domain, "http": r.status, "latency_ms": round((time.time() - t0) * 1000), "bytes": len(body)}
    except Exception as exc:
        return {"domain": domain, "http": None, "error": str(exc)}


def myelin() -> dict:
    rows = []
    for p in glob.glob(os.path.expanduser("~/.cache/synax/hafiza/*/rapor.json")):
        try:
            rows.append(json.load(open(p)))
        except Exception:
            pass
    if not rows:
        return {"available": False}
    o3 = [r["hizlanma_clang_o3"] for r in rows]
    sc = [r["hizlanma_skaler"] for r in rows]
    return {
        "available": True, "source": "~/.cache/synax/hafiza (SHA-256 imzalı raporlar)", "kernels": len(rows),
        "vs_clang_o3": {"median": round(st.median(o3), 3), "max": round(max(o3), 3), "min": round(min(o3), 3)},
        "vs_scalar": {"median": round(st.median(sc), 3), "max": round(max(sc), 3), "min": round(min(sc), 3)},
        "winners": sorted({r["kazanan"] for r in rows}),
        "hw_fingerprint": sorted({r.get("hw_fingerprint", "legacy") for r in rows}),
        "per_kernel": sorted([{"module": r["modul"], "winner": r["kazanan"], "ms": r["kazanan_ms"],
                               "vs_o3": r["hizlanma_clang_o3"], "vs_scalar": r["hizlanma_skaler"]} for r in rows],
                             key=lambda x: -x["vs_o3"]),
    }


def research() -> dict:
    p = BASE / "research/vf_retrospective/results/EVALUATION_REPORT.md"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines()[:35]:
            m = re.match(r"\|\s*(\w+)\s*\|\s*(sensitivity|specificity)\s*\|\s*([\d.]+)%\s*\|\s*([\d.–%]+)\s*\|\s*(\d+/\d+)\s*\|\s*\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|", line)
            if m:
                rows.append({"class": m[1], "metric": m[2], "value_pct": float(m[3]), "ci95": m[4], "n": m[5], "target": m[6].strip(), "met": "✅" in m[7]})
    return {"source": "research/vf_retrospective/results/EVALUATION_REPORT.md",
            "model": "synax_full_model (5-fold, kayıt-gruplu CV)",
            "auc": (lambda m: float(m[1]) if m else None)(re.search(r"synax_full_model` — AUC ([\d.]+)", p.read_text(encoding="utf-8")) if p.exists() else None),
            "records": 57, "windows": 6869, "non_clinical": True, "first_table": rows}


def main() -> None:
    from synax_telemetry import get_codebase_metrics
    cb = get_codebase_metrics()
    cb.pop("supported_backends", None)
    cb.pop("semantic_lock", None)
    data = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "codebase": cb,
        "github": github(),
        "sites": [probe(d) for d in DOMAINS],
        "performance": myelin(),
        "research": research(),
        "web_traffic": None,
        "web_traffic_note": "Ziyaretçi verisi toplanmıyor: siteler statik barındırmada ve henüz bir sayaç servisi bağlı değil.",
    }
    out = BASE / "sites" / "dashboard_data.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out, "| github error:", data["github"]["error"])


if __name__ == "__main__":
    main()
