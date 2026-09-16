"""
sentinel/layer2.py
===================
Layer 2 — cross-version diff fetching. Real HTTP calls to npm,
PyPI, and GitHub to retrieve agent-config files from a package or
repo, for diffing against a scanned version.

Verified: instrumented test confirmed real HTTP calls to
registry.npmjs.org (fetch_npm_prior_files) and the live npm CDN
tarball URL. Do not modify without re-verifying against the real
registries — these functions never raise; they return {} on any
failure so callers can treat "nothing found" and "network error"
the same way (fail open to "no prior data", not fail closed to
an exception).
"""
import io
import json
import tarfile
import urllib.request
import urllib.error
from pathlib import PurePosixPath

from .rules import AGENT_CONFIG_NAMES

_USER_AGENT = "SENTINEL-md/0.1 (+https://github.com/sentinel-md)"


def _get_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _download(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except Exception:
        return None


def _extract_agent_configs_from_tarball(data: bytes) -> dict[str, str]:
    """Scan a .tar.gz's members for agent-config filenames, return {basename: text}."""
    found: dict[str, str] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                name = PurePosixPath(member.name).name
                if name.lower() in {n.lower() for n in AGENT_CONFIG_NAMES}:
                    f = tar.extractfile(member)
                    if f:
                        try:
                            found[name] = f.read().decode("utf-8", errors="replace")
                        except Exception:
                            continue
    except Exception:
        return {}
    return found


# ---------------------------------------------------------------------------
# npm
# ---------------------------------------------------------------------------

async def fetch_npm_prior_files(package_name: str) -> dict[str, str]:
    """Fetch agent-config files from the version BEFORE latest on npm."""
    meta = _get_json(f"https://registry.npmjs.org/{package_name}")
    if not meta or "versions" not in meta:
        return {}
    versions = list(meta["versions"].keys())
    if len(versions) < 2:
        return {}
    prior_version = versions[-2]
    tarball_url = meta["versions"][prior_version].get("dist", {}).get("tarball")
    if not tarball_url:
        return {}
    data = _download(tarball_url)
    if not data:
        return {}
    return _extract_agent_configs_from_tarball(data)


async def fetch_npm_current_files(package_name: str) -> dict[str, str]:
    """Fetch agent-config files from the LATEST published version on npm."""
    meta = _get_json(f"https://registry.npmjs.org/{package_name}")
    if not meta:
        return {}
    latest = meta.get("dist-tags", {}).get("latest")
    if not latest or latest not in meta.get("versions", {}):
        return {}
    tarball_url = meta["versions"][latest].get("dist", {}).get("tarball")
    if not tarball_url:
        return {}
    data = _download(tarball_url)
    if not data:
        return {}
    return _extract_agent_configs_from_tarball(data)


# ---------------------------------------------------------------------------
# PyPI
# ---------------------------------------------------------------------------

async def fetch_pypi_prior_files(package_name: str) -> dict[str, str]:
    meta = _get_json(f"https://pypi.org/pypi/{package_name}/json")
    if not meta:
        return {}
    releases = meta.get("releases", {})
    versions = [v for v in releases.keys() if releases[v]]
    if len(versions) < 2:
        return {}
    prior_version = versions[-2]
    sdist_url = next(
        (f["url"] for f in releases[prior_version] if f.get("packagetype") == "sdist"),
        None,
    )
    if not sdist_url:
        return {}
    data = _download(sdist_url)
    if not data:
        return {}
    return _extract_agent_configs_from_tarball(data)


async def fetch_pypi_current_files(package_name: str) -> dict[str, str]:
    meta = _get_json(f"https://pypi.org/pypi/{package_name}/json")
    if not meta:
        return {}
    latest = meta.get("info", {}).get("version")
    if not latest:
        return {}
    urls = meta.get("urls", [])
    sdist_url = next(
        (f["url"] for f in urls if f.get("packagetype") == "sdist"), None
    )
    if not sdist_url:
        return {}
    data = _download(sdist_url)
    if not data:
        return {}
    return _extract_agent_configs_from_tarball(data)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

async def fetch_github_agent_files(owner_repo: str) -> dict[str, str]:
    """Fetch agent-config files from a GitHub repo's HEAD (root only)."""
    found: dict[str, str] = {}
    for name in AGENT_CONFIG_NAMES:
        url = f"https://raw.githubusercontent.com/{owner_repo}/HEAD/{name}"
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    found[name] = resp.read().decode("utf-8", errors="replace")
        except Exception:
            continue
    return found


async def get_prior_files(ecosystem: str, name: str, version: str | None = None) -> dict[str, str]:
    """Dispatcher used by api.py's /scan/package endpoint."""
    if ecosystem == "npm":
        return await fetch_npm_prior_files(name)
    if ecosystem == "pypi":
        return await fetch_pypi_prior_files(name)
    if ecosystem == "github":
        return await fetch_github_agent_files(name)
    return {}


def compute_delta_pct(current_text: str, prior_text: str) -> float:
    """Character-length percent difference between two versions of a file."""
    if not prior_text:
        return 100.0
    return abs(len(current_text) - len(prior_text)) / max(len(prior_text), 1) * 100.0
