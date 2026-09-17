"""
sentinel/layer0/discovery.py
D1 — Full Surface Enumeration.

Discovers every agent-trust surface in a directory that Sentinel should scan.
Covers the V1 surface map defined in PRD §16.

V1 surfaces (in priority order):
  - CLAUDE.md, AGENTS.md, .cursorrules, .cursor/rules/*.mdc
  - .claude/settings.json (project-local)
  - ~/.claude/settings.json (global — macOS/Linux path)
  - ~/.claude.json (MCP traffic routing, OAuth tokens)
  - .mcp.json, mcp.json
  - .claude/commands/** (slash commands)
  - .github/copilot-instructions.md
  - .amazonq/rules/**
  - SKILL.md, *.skill.md
  - pyproject.toml [tool.claude] — parsed for claude-specific sections
  - package.json — checked for claude field

V1.5 (explicitly excluded for now):
  - .gemini/settings.json (non-Claude hook schema)
  - .vscode/tasks.json (Miasma vector — non-Claude schema)
  - Windows global settings path (different path, V1.5)
  - D4 tarball scanning

Returns a list of Path objects for files that should be scanned.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Iterator

# ── V1 agent-trust surface filenames (exact match, case-insensitive) ──────────
_EXACT_NAMES: frozenset[str] = frozenset({
    "claude.md",
    "agents.md",
    ".cursorrules",
    ".windsurfrules",
    "mcp.json",
    ".mcp.json",
    "mcp-config.json",
    "settings.json",       # .claude/settings.json specifically
    ".claude.json",        # ~/.claude.json — Mitiga Labs vector
    "copilot-instructions.md",
    "skill.md",
})

# Glob patterns for wildcard surface discovery
_GLOB_PATTERNS: list[str] = [
    ".cursor/rules/**/*.mdc",       # Cursor MDC rules (Miasma's Cursor vector)
    ".claude/commands/**/*",        # Claude slash commands (S15 surface)
    ".amazonq/rules/**/*",          # Amazon Q Developer
    "*.skill.md",                   # Agent skills (ClawHavoc surface)
]

# Extensions used as a fallback filter when file is in a relevant directory
_RELEVANT_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".cursorrules", ".json", ".toml", ".yaml", ".yml", ".txt", ".mdc"
})


def _is_relevant_path(path: Path, root: Path) -> bool:
    """True if this path is in a directory that Sentinel treats as a trust surface."""
    try:
        rel = path.relative_to(root)
        parts_lower = [p.lower() for p in rel.parts]
    except ValueError:
        parts_lower = [p.lower() for p in path.parts]

    sensitive_dirs = {".claude", ".cursor", ".amazonq", ".github"}
    return any(part in sensitive_dirs for part in parts_lower)


def discover(root: Path) -> list[Path]:
    """
    D1 — Enumerate all agent-trust surfaces under `root`.

    Skips: node_modules, .git, __pycache__, .venv, dist, build.
    Returns deduplicated, sorted list of absolute Path objects.
    """
    skip_dirs = {
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "target", ".cargo",
    }
    found: set[Path] = set()

    def _walk(directory: Path) -> Iterator[Path]:
        try:
            for child in directory.iterdir():
                if child.is_dir():
                    if child.name in skip_dirs:
                        continue
                    yield from _walk(child)
                elif child.is_file():
                    yield child
        except PermissionError:
            pass

    for path in _walk(root):
        name_lower = path.name.lower()
        # Exact name match
        if name_lower in _EXACT_NAMES:
            found.add(path.resolve())
            continue
        # Relevant directory + relevant extension
        if _is_relevant_path(path, root) and path.suffix.lower() in _RELEVANT_EXTENSIONS:
            found.add(path.resolve())

    # Also apply glob patterns
    for pattern in _GLOB_PATTERNS:
        for match in root.glob(pattern):
            if match.is_file():
                found.add(match.resolve())

    return sorted(found)


def discover_global_surfaces() -> list[Path]:
    """
    D1 — Enumerate global agent-trust surfaces on this machine.

    Global surfaces apply to every Claude Code project on this machine —
    elevated severity when compromised.
    """
    home = Path.home()
    surfaces: list[Path] = []

    # Global Claude Code settings
    global_settings_candidates = [
        home / ".claude" / "settings.json",
        home / ".claude.json",
    ]
    # Windows global path is V1.5 — documented here, not implemented
    if sys.platform.startswith("win"):
        # TODO (V1.5): Windows global path differs — skip for now
        # home / "AppData" / "Roaming" / "Claude" / "settings.json"
        pass

    for candidate in global_settings_candidates:
        if candidate.exists():
            surfaces.append(candidate)

    return surfaces
