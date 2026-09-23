"""Tests for packaging, PyPI metadata, wheel contents, entry points, and SBOM."""
from __future__ import annotations

import json
import tomllib
import zipfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
DIST = ROOT / "dist"


@pytest.fixture(scope="module")
def pyproject_data():
    assert PYPROJECT.is_file()
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pyproject_pep621_metadata(pyproject_data):
    project = pyproject_data.get("project", {})

    assert project.get("name") == "sentinel-md"
    assert project.get("license") == {"text": "Apache-2.0"}
    assert project.get("requires-python") == ">=3.10"
    assert len(project.get("authors", [])) >= 2

    # Scripts / entry points
    scripts = project.get("scripts", {})
    assert scripts.get("sentinel") == "sentinel.cli:main"

    # Classifiers
    classifiers = project.get("classifiers", [])
    assert any("Topic :: Security" in c for c in classifiers)
    assert any("License :: OSI Approved :: Apache Software License" in c for c in classifiers)
    assert any("Programming Language :: Python :: 3" in c for c in classifiers)

    # Keywords
    keywords = project.get("keywords", [])
    assert "ai-agent" in keywords or "security" in keywords

    # URLs
    urls = project.get("urls", {})
    assert "Homepage" in urls
    assert "Repository" in urls
    assert "Documentation" in urls
    assert "Issues" in urls
    assert "Changelog" in urls


def test_wheel_contains_all_modules_and_entry_point():
    wheels = list(DIST.glob("sentinel_md-*.whl"))
    assert wheels, f"No wheel found in {DIST}. Run `python -m build` first."
    wheel_path = wheels[0]

    with zipfile.ZipFile(wheel_path) as z:
        names = set(z.namelist())

        # Core modules
        assert "sentinel/__init__.py" in names
        assert "sentinel/cli.py" in names
        assert "sentinel/core.py" in names
        assert "sentinel/sarif.py" in names
        assert "sentinel/machine.py" in names
        assert "sentinel/doctor/sarif.py" in names
        assert "sentinel/timewarp/runner.py" in names

        # Entry points
        ep_files = [n for n in names if n.endswith("entry_points.txt")]
        assert ep_files, "Missing entry_points.txt in wheel metadata"
        ep_content = z.read(ep_files[0]).decode("utf-8")
        assert "sentinel = sentinel.cli:main" in ep_content


def test_cyclonedx_sbom_structure():
    sbom_path = DIST / "sentinel-md.sbom.json"
    assert sbom_path.is_file(), f"Missing SBOM at {sbom_path}"
    data = json.loads(sbom_path.read_text(encoding="utf-8"))

    assert data.get("bomFormat") == "CycloneDX"
    assert data.get("specVersion") == "1.5"
    metadata = data.get("metadata", {})
    assert metadata.get("component", {}).get("name") == "sentinel-md"
    assert len(data.get("components", [])) >= 3
    assert len(data.get("dependencies", [])) >= 1


def test_extension_package_json_openvsx_ready():
    pkg_path = ROOT / "vscode-extension" / "package.json"
    assert pkg_path.is_file()
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))

    assert pkg.get("name") == "sentinel-md"
    assert pkg.get("publisher") == "sentinel"
    assert pkg.get("license") == "Apache-2.0"
    assert "Linters" in pkg.get("categories", [])
    assert pkg.get("repository", {}).get("url")
    assert pkg.get("keywords")
