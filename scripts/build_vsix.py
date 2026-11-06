#!/usr/bin/env python3
"""
SYNAX Zero-Dependency VS Code Extension (.vsix) Packager (`scripts/build_vsix.py`)
==================================================================================
Builds a standards-compliant Open Packaging Conventions (OPC) `.vsix` bundle from
`editors/vscode-synax` using only the Python 3 standard library (`zipfile`, `json`,
`xml.sax.saxutils`). No Node.js / `vsce` npm dependency required!

Installable via:
  - `code --install-extension dist/synax-lang-0.5.0.vsix`
  - VS Code / Antigravity IDE UI -> Extensions -> `...` -> `Install from VSIX...`
==================================================================================
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = ROOT / "editors" / "vscode-synax"
DIST_DIR = ROOT / "dist"


def prepare_bundled_payload() -> None:
    """Pre-bundle the complete SYNAX runtime engine so the VSIX is 100% self-sufficient."""
    bundled_dir = EXT_DIR / "bundled"
    bundled_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy all root Python modules needed by synax chat, CLI, and compiler
    for py in ROOT.glob("*.py"):
        if not py.name.startswith("test_"):
            shutil.copy2(py, bundled_dir / py.name)

    # 2. Copy the whole src/ package
    bundled_src = bundled_dir / "src"
    if bundled_src.exists():
        shutil.rmtree(bundled_src)
    shutil.copytree(ROOT / "src", bundled_src)


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Default Extension="md" ContentType="text/markdown"/>
  <Default Extension="txt" ContentType="text/plain"/>
  <Default Extension="py" ContentType="text/plain"/>
  <Default Extension="sx" ContentType="text/plain"/>
  <Default Extension="code-snippets" ContentType="application/json"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
</Types>
"""


def render_vsixmanifest(pkg: dict) -> str:
    publisher = escape(pkg.get("publisher", "synaxcode"))
    name = escape(pkg["name"])
    version = escape(pkg["version"])
    display_name = escape(pkg.get("displayName", name))
    description = escape(pkg.get("description", ""))
    engine = escape(pkg.get("engines", {}).get("vscode", "^1.80.0"))
    categories = escape(",".join(pkg.get("categories", ["Programming Languages"])))
    tags = escape(",".join(pkg.get("keywords", ["synax", "sx"])))
    repo_url = escape(pkg.get("repository", {}).get("url", "https://github.com/ofaemd-creator/synax"))

    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}"/>
    <DisplayName>{display_name}</DisplayName>
    <Description xml:space="preserve">{description}</Description>
    <Tags>{tags}</Tags>
    <Categories>{categories}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}"/>
      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="{repo_url}"/>
      <Property Id="Microsoft.VisualStudio.Services.Links.Getstarted" Value="{repo_url}"/>
      <Property Id="Microsoft.VisualStudio.Services.Links.GitHub" Value="{repo_url}"/>
    </Properties>
    <License>extension/LICENSE.txt</License>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" Addressable="true"/>
  </Assets>
</PackageManifest>
"""


def build_vsix(out_dir: Path = DIST_DIR) -> Path:
    prepare_bundled_payload()
    pkg = json.loads((EXT_DIR / "package.json").read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    vsix_name = f"{pkg['name']}-{pkg['version']}.vsix"
    vsix_path = out_dir / vsix_name

    with zipfile.ZipFile(vsix_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML.encode("utf-8"))
        zf.writestr("extension.vsixmanifest", render_vsixmanifest(pkg).encode("utf-8"))
        if (ROOT / "LICENSE").exists():
            zf.writestr("extension/LICENSE.txt", (ROOT / "LICENSE").read_bytes())
        for f in sorted(EXT_DIR.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel = f.relative_to(EXT_DIR).as_posix()
                zf.writestr(f"extension/{rel}", f.read_bytes())

    return vsix_path


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DIST_DIR
    vsix = build_vsix(out)
    print(f"Built VSIX package: {vsix} ({vsix.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
