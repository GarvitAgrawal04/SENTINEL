"""Rebuild frontend/sentinel-md.vsix from vscode-extension/ sources."""
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "vscode-extension"
VSIX = ROOT / "frontend" / "sentinel-md.vsix"

def rebuild():
    pkg = json.loads((SRC / "package.json").read_text(encoding="utf-8"))
    version = pkg["version"]

    with zipfile.ZipFile(VSIX, "r") as zin:
        content_types = zin.read("[Content_Types].xml")
        manifest = zin.read("extension.vsixmanifest").decode("utf-8")
        license_txt = zin.read("extension/LICENSE.txt")

    # Update version in manifest
    manifest = re.sub(r'Identity Language="en-US" Id="sentinel-md" Version="[^"]+"',
                      f'Identity Language="en-US" Id="sentinel-md" Version="{version}"', manifest)

    js_bytes = (SRC / "extension.js").read_bytes()
    pkg_bytes = (SRC / "package.json").read_bytes()
    readme_bytes = (SRC / "README.md").read_bytes()

    with zipfile.ZipFile(VSIX, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("extension.vsixmanifest", manifest.encode("utf-8"))
        zout.writestr("[Content_Types].xml", content_types)
        zout.writestr("extension/extension.js", js_bytes)
        zout.writestr("extension/LICENSE.txt", license_txt)
        zout.writestr("extension/package.json", pkg_bytes)
        zout.writestr("extension/readme.md", readme_bytes)

    print(f"Rebuilt {VSIX} with extension version {version}")

if __name__ == "__main__":
    rebuild()
