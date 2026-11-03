"""
SYNAX Release & Self-Update Manager (`src/synax/updater.py`)
=============================================================================
Checks official GitHub Releases (`ofaemd-creator/synax`) for newer SemVer tags,
verifies SHA-256 digests (`SHA256SUMS.txt`) before any artifact extraction,
and supports `synax update --check` and `synax update`.
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

GITHUB_REPO = "ofaemd-creator/synax"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_semver(version_str: str) -> Tuple[int, int, int]:
    clean = version_str.strip().lstrip("vV").split("-", 1)[0]
    parts = clean.split(".")
    nums = []
    for i in range(3):
        try:
            nums.append(int(parts[i]))
        except (IndexError, ValueError):
            nums.append(0)
    return (nums[0], nums[1], nums[2])


@dataclass(frozen=True)
class UpdateCheckResult:
    current_version: str
    latest_version: str
    update_available: bool
    release_url: str
    asset_url: Optional[str] = None
    checksums_url: Optional[str] = None
    offline_or_unreleased: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "release_url": self.release_url,
            "asset_url": self.asset_url,
            "offline_or_unreleased": self.offline_or_unreleased,
            "message": self.message,
        }


def platform_asset_name() -> str:
    sys_name = platform.system().lower()
    mach = platform.machine().lower()
    os_tag = "macos" if sys_name == "darwin" else ("windows" if sys_name == "windows" else "linux")
    arch_tag = "arm64" if mach in ("arm64", "aarch64") else "x86_64"
    ext = "zip" if os_tag == "windows" else "tar.gz"
    return f"synax-{os_tag}-{arch_tag}.{ext}"


def check_for_updates(current_version: str = "0.5.0", timeout_sec: float = 5.0) -> UpdateCheckResult:
    """Query GitHub Releases API for newer SYNAX versions."""
    req = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"synax-cli/{current_version}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return UpdateCheckResult(
                current_version=current_version,
                latest_version=current_version,
                update_available=False,
                release_url=f"https://github.com/{GITHUB_REPO}/releases",
                offline_or_unreleased=True,
                message="Henüz etiketlenmiş bir GitHub Release paketi yayımlanmamış (yerel sürüm güncel).",
            )
        return UpdateCheckResult(
            current_version=current_version,
            latest_version=current_version,
            update_available=False,
            release_url=f"https://github.com/{GITHUB_REPO}/releases",
            offline_or_unreleased=True,
            message=f"GitHub API HTTP {exc.code}",
        )
    except Exception as exc:
        return UpdateCheckResult(
            current_version=current_version,
            latest_version=current_version,
            update_available=False,
            release_url=f"https://github.com/{GITHUB_REPO}/releases",
            offline_or_unreleased=True,
            message=f"Çevrimdışı veya ağ erişimi yok ({type(exc).__name__}).",
        )

    tag = str(payload.get("tag_name") or current_version)
    html_url = str(payload.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases")
    newer = _parse_semver(tag) > _parse_semver(current_version)

    target_asset = platform_asset_name()
    asset_url: Optional[str] = None
    sums_url: Optional[str] = None
    for asset in payload.get("assets", []):
        name = asset.get("name", "")
        dl_url = asset.get("browser_download_url")
        if name == target_asset:
            asset_url = dl_url
        elif name == "SHA256SUMS.txt":
            sums_url = dl_url

    msg = (
        f"Yeni sürüm mevcut: {tag} (mevcut: v{current_version})"
        if newer
        else f"SYNAX güncel (v{current_version})."
    )
    return UpdateCheckResult(
        current_version=current_version,
        latest_version=tag.lstrip("vV"),
        update_available=newer,
        release_url=html_url,
        asset_url=asset_url,
        checksums_url=sums_url,
        offline_or_unreleased=False,
        message=msg,
    )


def verify_file_sha256(file_path: Path, expected_hex: str) -> bool:
    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return digest.lower() == expected_hex.strip().lower()


def perform_pip_upgrade() -> Tuple[bool, str]:
    """Upgrade `synax` package via `pip install --upgrade synax`."""
    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "synax"],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return True, res.stdout.strip()
    return False, res.stderr.strip() or res.stdout.strip()
