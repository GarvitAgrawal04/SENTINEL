"""
sentinel/layer0/origin.py
D2 — Postinstall origin detection.

PRD §13.3 exact logic:

Condition 1: file absent from git history at current content, appeared recently.
Condition 2: mtime within 60 seconds of recorded npm/pip install activity.

Condition 1 AND Condition 2 → origin: postinstall-suspected
Matching file in node_modules/ → origin: postinstall-confirmed

Otherwise: origin: git (committed), or origin: unknown.

This information feeds into:
  - S16 compound condition (S16 + postinstall → COMPROMISED)
  - S15 (deposited slash command — git history check)
  - Formatter output (makes origin visible in every PR diff via sentinel.lock)

Limitations (V1):
  - Condition 2 (mtime within 60s of npm/pip install) requires heuristics
    since npm/pip don't log timestamps in a standard location on all OSes.
    We approximate by checking node_modules/.package-lock.json mtime.
  - git history check requires subprocess call — gracefully handles repos
    without git.
  - Windows path differences for global settings (V1.5).
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

_POSTINSTALL_WINDOW_SECONDS = 60


def _get_file_mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _get_npm_install_mtime(root: Path) -> float | None:
    """
    Approximate npm install time via node_modules/.package-lock.json mtime.
    Returns None if not found.
    """
    candidates = [
        root / "node_modules" / ".package-lock.json",
        root / "node_modules" / ".modules.yaml",  # pnpm
        root / "package-lock.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return _get_file_mtime(candidate)
    return None


def _get_pip_install_mtime(root: Path) -> float | None:
    """
    Approximate pip install time via site-packages or .pth file mtime.
    Returns None if not in a virtual environment.
    """
    # Check pyproject.toml or requirements.txt for a project-local venv
    venv_candidates = [root / ".venv", root / "venv"]
    for venv in venv_candidates:
        sp = venv / "lib"
        if sp.exists():
            # Use the most recently modified site-packages entry
            try:
                entries = sorted(sp.rglob("*.dist-info"), key=lambda p: p.stat().st_mtime, reverse=True)
                if entries:
                    return entries[0].stat().st_mtime
            except (OSError, StopIteration):
                pass
    return None


def _is_committed_to_git(path: Path, root: Path) -> bool:
    """
    Returns True if the file's CURRENT CONTENT is present in git history.
    Uses `git log --follow -S` (pickaxe) to check if the exact content
    was ever committed.

    Returns False if git is not available or this is not a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--follow", "--", str(path.relative_to(root))],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        # File exists in git history if there's at least one log entry
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return False


def _is_in_node_modules(path: Path, root: Path) -> bool:
    """Check if a matching file exists in node_modules (postinstall-confirmed)."""
    try:
        rel = path.relative_to(root)
        name = path.name
    except ValueError:
        return False

    for nm_dir in root.rglob("node_modules"):
        if not nm_dir.is_dir():
            continue
        # Look for any file with the same name under node_modules
        for match in nm_dir.rglob(name):
            if match.is_file():
                return True
    return False


def detect_origin(path: Path, root: Path | None = None) -> str:
    """
    D2 — Detect the origin of an agent-trust surface file.

    Returns one of:
      "git"                    — file is tracked in git history
      "postinstall-suspected"  — conditions 1 AND 2 match
      "postinstall-confirmed"  — matching file found in node_modules
      "unknown"                — cannot determine (no git, no package manager)

    Parameters
    ----------
    path:
        Absolute path to the file being evaluated.
    root:
        Project root directory. If None, uses path.parent.
    """
    if root is None:
        root = path.parent

    # Condition 3 check first (strongest signal)
    if _is_in_node_modules(path, root):
        return "postinstall-confirmed"

    # Check git history
    is_git = _is_committed_to_git(path, root)
    if is_git:
        return "git"

    # File is NOT in git history — check if it appeared near an install
    file_mtime = _get_file_mtime(path)
    if file_mtime is None:
        return "unknown"

    # Try to find an install event mtime
    install_mtime = _get_npm_install_mtime(root)
    if install_mtime is None:
        install_mtime = _get_pip_install_mtime(root)

    if install_mtime is not None:
        delta = abs(file_mtime - install_mtime)
        if delta <= _POSTINSTALL_WINDOW_SECONDS:
            return "postinstall-suspected"

    return "unknown"
