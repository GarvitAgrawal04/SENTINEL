"""Sentinel Doctor - Deterministic instruction hygiene checks (D001–D004).

D001: broken @include (auto-fix: remove)
D002: backticked path that does not exist (flag)
D003: named script/command not defined in package.json/Makefile/pyproject (flag)
D004: duplicate rule, normalised (keep first, auto-fix: remove)

These are hygiene diagnostics, not security vulnerabilities. They do not affect
security scoring or verdicts.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from sentinel.doctor.graph import resolve_import_path, extract_imports, IMPORT_RE

# Extensions commonly associated with repo paths
PATH_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".toml",
    ".yaml", ".yml", ".sh", ".bash", ".rs", ".go", ".html", ".css",
    ".sql", ".env", ".lock", ".txt", ".cfg", ".ini", ".c", ".cpp", ".h"
)


def extract_backticked_paths(text: str) -> list[str]:
    """Find backticked strings that look like file or directory paths."""
    candidates = re.findall(r'`([^`\n]+)`', text)
    paths: list[str] = []
    for cand in candidates:
        cand = cand.strip()
        # Exclude URLs, options/flags, and shell pipelines
        if (
            cand.startswith("-")
            or "://" in cand
            or "|" in cand
            or "<" in cand
            or ">" in cand
            or "{" in cand
            or "*" in cand
            or "?" in cand
            or "$" in cand
        ):
            continue
        # Exclude multi-word commands (like `npm install foo`)
        if " " in cand and not cand.startswith("./"):
            continue
        # Must contain path separators or a recognizable file extension
        has_sep = "/" in cand or "\\" in cand
        has_ext = any(cand.lower().endswith(ext) for ext in PATH_EXTENSIONS)
        if (has_sep or has_ext) and len(cand) > 2:
            paths.append(cand)
    return paths


def get_manifest_scripts(root: Path) -> dict[str, set[str]]:
    """Parse defined scripts/targets from package.json, Makefile, and pyproject.toml."""
    defined: dict[str, set[str]] = {
        "package.json": set(),
        "Makefile": set(),
        "pyproject.toml": set(),
    }

    # 1. package.json
    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
            scripts = data.get("scripts", {})
            if isinstance(scripts, dict):
                defined["package.json"] = set(scripts.keys())
        except Exception:
            pass

    # 2. Makefile
    makefile = root / "Makefile"
    if makefile.is_file():
        try:
            text = makefile.read_text(encoding="utf-8", errors="replace")
            # Find targets like `test:`, `build-all:`, ignoring variables or .PHONY
            targets = set(re.findall(r'^[ \t]*([a-zA-Z0-9_.-]+)\s*:', text, re.MULTILINE))
            targets.discard(".PHONY")
            targets.discard(".DEFAULT_GOAL")
            defined["Makefile"] = targets
        except Exception:
            pass

    # 3. pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            # Match keys in [project.scripts] or [tool.poetry.scripts]
            in_scripts_section = False
            scripts = set()
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    in_scripts_section = ("scripts" in line)
                elif in_scripts_section and "=" in line:
                    k = line.split("=", 1)[0].strip().strip('"\'')
                    if k:
                        scripts.add(k)
            defined["pyproject.toml"] = scripts
        except Exception:
            pass

    return defined


def normalize_rule(text: str) -> str:
    """Normalize a rule string to detect duplicates across variations."""
    # Strip markdown bullets or numbers
    cleaned = re.sub(r'^\s*(?:[-*+]|\d+\.)\s+', '', text).strip()
    # Lowercase and remove trailing punctuation
    cleaned = cleaned.lower().rstrip(".;,!?")
    # Collapse multiple whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def check_file(file_path: Path, root: Path | None = None) -> list[dict[str, Any]]:
    """Run deterministic checks D001–D004 on an agent file.

    Returns a list of finding dicts: {id, line, message, fix}.
    """
    if root is None:
        root = file_path.parent

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = content.splitlines()
    findings: list[dict[str, Any]] = []

    # Cache manifest scripts for D003
    manifest_scripts = get_manifest_scripts(root)

    # Tracking for D004 duplicate rules
    seen_rules: dict[str, int] = {}

    for idx, line in enumerate(lines, start=1):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # -------------------------------------------------------------
        # D001: broken @include / @import (auto-fix: remove)
        # -------------------------------------------------------------
        raw_imports = extract_imports(line)
        for imp in raw_imports:
            resolved = resolve_import_path(imp, file_path, root)
            if not resolved.exists():
                findings.append({
                    "id": "D001",
                    "line": idx,
                    "message": f"Broken @include / @import: '{imp}' does not exist on disk",
                    "fix": {
                        "description": f"Remove broken include '{imp}'",
                        "replacement": "",
                    },
                })

        # -------------------------------------------------------------
        # D002: backticked path that does not exist (flag)
        # -------------------------------------------------------------
        # Skip import lines to avoid double-flagging with D001
        if not IMPORT_RE.search(line):
            b_paths = extract_backticked_paths(line)
            for p_str in b_paths:
                # Check existence relative to file.parent and root
                cand1 = file_path.parent / p_str
                cand2 = root / p_str
                if not cand1.exists() and not cand2.exists():
                    findings.append({
                        "id": "D002",
                        "line": idx,
                        "message": f"Referenced path '{p_str}' does not exist on disk",
                        "fix": None,
                    })

        # -------------------------------------------------------------
        # D003: named script/command not defined in manifests (flag)
        # -------------------------------------------------------------
        # Match `npm run <name>`, `yarn <name>`, `pnpm run <name>`, `bun run <name>`
        npm_match = re.search(r'\b(?:npm\s+run|pnpm\s+run|yarn|bun\s+run)\s+([a-zA-Z0-9_:-]+)', line)
        if npm_match and (root / "package.json").is_file():
            script_name = npm_match.group(1)
            defined = manifest_scripts["package.json"]
            if script_name not in defined:
                findings.append({
                    "id": "D003",
                    "line": idx,
                    "message": f"Command references undefined npm script '{script_name}' (not in package.json)",
                    "fix": None,
                })

        # Match `make <target>`
        make_match = re.search(r'\bmake\s+([a-zA-Z0-9_.-]+)', line)
        if make_match and (root / "Makefile").is_file():
            target_name = make_match.group(1)
            defined = manifest_scripts["Makefile"]
            if target_name not in defined:
                findings.append({
                    "id": "D003",
                    "line": idx,
                    "message": f"Command references undefined Makefile target '{target_name}' (not in Makefile)",
                    "fix": None,
                })

        # Match `poetry run <script>`
        poetry_match = re.search(r'\bpoetry\s+run\s+([a-zA-Z0-9_.-]+)', line)
        if poetry_match and (root / "pyproject.toml").is_file():
            script_name = poetry_match.group(1)
            defined = manifest_scripts["pyproject.toml"]
            # If pyproject.toml defines scripts, check membership
            if defined and script_name not in defined:
                findings.append({
                    "id": "D003",
                    "line": idx,
                    "message": f"Command references undefined poetry script '{script_name}' (not in pyproject.toml)",
                    "fix": None,
                })

        # -------------------------------------------------------------
        # D004: duplicate rule, normalised (keep first, auto-fix: remove)
        # -------------------------------------------------------------
        # Check rule bullets or standalone rule lines (exclude headers or code blocks)
        is_bullet = bool(re.match(r'^\s*(?:[-*+]|\d+\.)\s+', line))
        if is_bullet or (not line_stripped.startswith("#") and not line_stripped.startswith("```")):
            norm = normalize_rule(line)
            if len(norm) >= 6:  # ignore trivial lines like "ok", "run"
                if norm in seen_rules:
                    first_line = seen_rules[norm]
                    findings.append({
                        "id": "D004",
                        "line": idx,
                        "message": f"Duplicate rule: '{line_stripped}' (first defined on line {first_line})",
                        "fix": {
                            "description": "Remove duplicate rule line",
                            "replacement": "",
                        },
                    })
                else:
                    seen_rules[norm] = idx

    return findings


def apply_fixes(content: str, findings: list[dict[str, Any]]) -> tuple[str, int]:
    """Apply safe auto-fixes to content in-place.

    Returns:
        (updated_content, number_of_fixes_applied)
    """
    fixable = [f for f in findings if f.get("fix") is not None and f["fix"].get("replacement") is not None]
    if not fixable:
        return content, 0

    # Sort descending by line number to maintain index alignment
    fixable.sort(key=lambda x: x["line"], reverse=True)

    lines = content.splitlines(keepends=True)
    fixed_count = 0

    for f in fixable:
        line_idx = f["line"] - 1
        if 0 <= line_idx < len(lines):
            repl = f["fix"]["replacement"]
            if repl == "":
                # Delete the line
                del lines[line_idx]
                fixed_count += 1
            else:
                lines[line_idx] = repl if repl.endswith("\n") else repl + "\n"
                fixed_count += 1

    return "".join(lines), fixed_count
