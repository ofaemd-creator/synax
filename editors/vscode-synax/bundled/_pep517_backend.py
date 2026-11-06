"""
SYNAX Zero-Dependency PEP 517 & PEP 660 Build Backend (`_pep517_backend.py`)
=============================================================================
Builds standards-compliant PEP 427 wheels (`.whl`), PEP 660 editable wheels,
and PEP 517 source distributions (`.tar.gz`) using ONLY the Python 3 standard
library (`zipfile`, `tarfile`, `hashlib`, `base64`, `csv`, `tomllib`).

Allows `pip install .`, `pip install -e .`, and `python -m build` to succeed
both online (PyPI CI) and 100% offline in air-gapped / sandboxed environments.
=============================================================================
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent


def _load_project_meta() -> Dict[str, Any]:
    toml_path = ROOT / "pyproject.toml"
    if tomllib is not None:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        return data
    return {
        "project": {
            "name": "synax",
            "version": "0.5.0",
            "description": "SYNAX (.sx) — Neuro-Symbolic Kernel Language, Differential Verifier & Adaptive Myelin Compiler",
            "requires-python": ">=3.10",
            "scripts": {"synax": "synax_cli:main", "synaxc": "synaxc:main"},
        },
        "tool": {
            "setuptools": {
                "py-modules": [
                    "synax_ir",
                    "synax_verifier",
                    "synaxc",
                    "synax_cli",
                    "synax_myelin",
                    "synax_security",
                    "synapse_neural_model",
                    "synax_core",
                    "synax_biomedical_stream",
                    "synax_sdk",
                    "synax_web_server",
                ]
            }
        },
    }


def _dist_info_dirname(name: str, version: str) -> str:
    norm = name.replace("-", "_")
    return f"{norm}-{version}.dist-info"


def _render_metadata(cfg: Dict[str, Any]) -> str:
    proj = cfg["project"]
    name = proj["name"]
    version = proj["version"]
    desc = proj.get("description", "")
    req_py = proj.get("requires-python", ">=3.10")
    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
        f"Summary: {desc}",
        "Author: Dr. Ömer Faruk Aydın",
        "Author-email: Dr. Ömer Faruk Aydın <dev@synaxcode.com>",
        "License: Apache-2.0",
        f"Requires-Python: {req_py}",
        "Description-Content-Type: text/markdown",
    ]
    for clf in proj.get("classifiers", []):
        lines.append(f"Classifier: {clf}")
    for label, url in proj.get("urls", {}).items():
        lines.append(f"Project-URL: {label}, {url}")
    for extra, deps in proj.get("optional-dependencies", {}).items():
        lines.append(f"Provides-Extra: {extra}")
        for dep in deps:
            lines.append(f"Requires-Dist: {dep}; extra == '{extra}'")

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else desc
    return "\n".join(lines) + "\n\n" + readme.rstrip() + "\n"


def _render_wheel_tag() -> str:
    return (
        "Wheel-Version: 1.0\n"
        "Generator: synax-pep517 (0.5.0)\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    )


def _render_entry_points(cfg: Dict[str, Any]) -> str:
    scripts = cfg["project"].get("scripts", {})
    if not scripts:
        return ""
    lines = ["[console_scripts]"]
    for cmd, target in scripts.items():
        lines.append(f"{cmd} = {target}")
    return "\n".join(lines) + "\n"


def _record_digest(data: bytes) -> Tuple[str, str]:
    digest = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={b64}", str(len(data))


def _write_dist_info_files(cfg: Dict[str, Any]) -> Tuple[str, Dict[str, bytes]]:
    proj = cfg["project"]
    dist_info = _dist_info_dirname(proj["name"], proj["version"])
    files: Dict[str, bytes] = {
        f"{dist_info}/METADATA": _render_metadata(cfg).encode("utf-8"),
        f"{dist_info}/WHEEL": _render_wheel_tag().encode("utf-8"),
    }
    ep = _render_entry_points(cfg)
    if ep:
        files[f"{dist_info}/entry_points.txt"] = ep.encode("utf-8")
    if (ROOT / "LICENSE").exists():
        files[f"{dist_info}/LICENSE"] = (ROOT / "LICENSE").read_bytes()
    return dist_info, files


def _build_record_bytes(entries: Dict[str, bytes], record_arcname: str) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for arcname in sorted(entries.keys()):
        h, sz = _record_digest(entries[arcname])
        writer.writerow([arcname, h, sz])
    writer.writerow([record_arcname, "", ""])
    return buf.getvalue().encode("utf-8")


# ─────────────────────────────────────────────────────────────────
# PEP 517 & PEP 660 Standard Hooks
# ─────────────────────────────────────────────────────────────────
def get_requires_for_build_wheel(config_settings: Optional[Dict[str, Any]] = None) -> List[str]:
    return []


def get_requires_for_build_editable(config_settings: Optional[Dict[str, Any]] = None) -> List[str]:
    return []


def get_requires_for_build_sdist(config_settings: Optional[Dict[str, Any]] = None) -> List[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: Optional[Dict[str, Any]] = None
) -> str:
    cfg = _load_project_meta()
    dist_info, files = _write_dist_info_files(cfg)
    rec_name = f"{dist_info}/RECORD"
    files[rec_name] = _build_record_bytes(files, rec_name)
    out_root = Path(metadata_directory)
    for rel, raw in files.items():
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    return dist_info


prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel


def build_wheel(
    wheel_directory: str,
    config_settings: Optional[Dict[str, Any]] = None,
    metadata_directory: Optional[str] = None,
) -> str:
    cfg = _load_project_meta()
    proj = cfg["project"]
    norm = proj["name"].replace("-", "_")
    version = proj["version"]
    whl_name = f"{norm}-{version}-py3-none-any.whl"
    whl_path = Path(wheel_directory) / whl_name

    entries: Dict[str, bytes] = {}

    # 1. Root py-modules
    py_mods = cfg.get("tool", {}).get("setuptools", {}).get("py-modules", [])
    for mod in py_mods:
        f = ROOT / f"{mod}.py"
        if f.exists():
            entries[f"{mod}.py"] = f.read_bytes()

    # 2. `src/synax/**` package files
    src_pkg = ROOT / "src" / "synax"
    for py_file in sorted(src_pkg.rglob("*.py")):
        rel = py_file.relative_to(ROOT / "src").as_posix()
        entries[rel] = py_file.read_bytes()

    dist_info, meta_files = _write_dist_info_files(cfg)
    entries.update(meta_files)
    rec_name = f"{dist_info}/RECORD"
    entries[rec_name] = _build_record_bytes(entries, rec_name)

    with zipfile.ZipFile(whl_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname in sorted(entries.keys()):
            zf.writestr(arcname, entries[arcname])

    return whl_name


def build_editable(
    wheel_directory: str,
    config_settings: Optional[Dict[str, Any]] = None,
    metadata_directory: Optional[str] = None,
) -> str:
    cfg = _load_project_meta()
    proj = cfg["project"]
    norm = proj["name"].replace("-", "_")
    version = proj["version"]
    whl_name = f"{norm}-{version}-0.editable-py3-none-any.whl"
    whl_path = Path(wheel_directory) / whl_name

    pth_content = f"{ROOT}\n{ROOT / 'src'}\n".encode("utf-8")
    entries: Dict[str, bytes] = {"_synax_editable.pth": pth_content}

    dist_info, meta_files = _write_dist_info_files(cfg)
    entries.update(meta_files)
    rec_name = f"{dist_info}/RECORD"
    entries[rec_name] = _build_record_bytes(entries, rec_name)

    with zipfile.ZipFile(whl_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname in sorted(entries.keys()):
            zf.writestr(arcname, entries[arcname])

    return whl_name


def build_sdist(
    sdist_directory: str, config_settings: Optional[Dict[str, Any]] = None
) -> str:
    cfg = _load_project_meta()
    proj = cfg["project"]
    norm = proj["name"].replace("-", "_")
    version = proj["version"]
    base_dir = f"{norm}-{version}"
    sdist_name = f"{base_dir}.tar.gz"
    sdist_path = Path(sdist_directory) / sdist_name

    include_globs = [
        "pyproject.toml",
        "_pep517_backend.py",
        "MANIFEST.in",
        "README.md",
        "LICENSE",
        "LICENSING.md",
        "NOTICE",
        "TRADEMARKS.md",
        "MEDICAL_RESEARCH_DISCLAIMER.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "ROADMAP.md",
        "CITATION.cff",
        "synax_myelin_engine.c",
        "synax_myelin_engine.h",
        "synapse_brain.json",
        "*.py",
        "src/synax/**/*.py",
        "include/*.h",
        "include/*.hpp",
        "spec/*",
        "examples/*.sx",
        "tests/*.py",
    ]

    collected: Dict[str, Path] = {}
    for pat in include_globs:
        for p in sorted(ROOT.glob(pat)):
            if p.is_file() and "__pycache__" not in p.parts:
                collected[p.relative_to(ROOT).as_posix()] = p

    pkg_info_bytes = _render_metadata(cfg).encode("utf-8")

    with tarfile.open(sdist_path, "w:gz") as tf:
        ti = tarfile.TarInfo(name=f"{base_dir}/PKG-INFO")
        ti.size = len(pkg_info_bytes)
        tf.addfile(ti, io.BytesIO(pkg_info_bytes))
        for rel, disk_path in sorted(collected.items()):
            tf.add(str(disk_path), arcname=f"{base_dir}/{rel}")

    return sdist_name
