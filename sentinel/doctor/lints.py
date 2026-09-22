"""Sentinel Doctor - Deterministic instruction hygiene checks (D001–D008).

D001: broken @include (auto-fix: remove)
D002: backticked path that does not exist (flag)
D003: named script/command not defined in package.json/Makefile/pyproject (flag)
D004: duplicate rule, normalised (keep first, auto-fix: remove)
D005: rule contradicts a guardrail in the same graph (flag)
D006: file over the token budget (default 1500; suggest sections to cut)
D007: secret-shaped value in an agent file (flag; NEVER send to a model)
D008: ANSI/terminal escape in the text (auto-fix: strip)

These are hygiene diagnostics, not security vulnerabilities. They do not affect
security scoring or verdicts. Checks firing on >5% of healthy repos are classified
as OBSERVATIONS rather than WARNINGS.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from sentinel.doctor.graph import resolve_import_path, extract_imports, IMPORT_RE, estimate_tokens

DEFAULT_TOKEN_BUDGET = 1500

PATH_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".toml",
    ".yaml", ".yml", ".sh", ".bash", ".rs", ".go", ".html", ".css",
    ".sql", ".env", ".lock", ".txt", ".cfg", ".ini", ".c", ".cpp", ".h"
)

ANSI_ESCAPE_RE = re.compile(
    r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1b\\))'
)

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r'\b(AKIA[0-9A-Z]{16})\b')),
    ("GitHub token", re.compile(r'\b(gh[pousr]_[0-9a-zA-Z]{36,})\b')),
    ("API key", re.compile(r'\b(sk-(?:ant-)?[a-zA-Z0-9_-]{20,})\b')),
    ("Slack token", re.compile(r'\b(xox[baprs]-[0-9a-zA-Z]{10,})\b')),
    ("Private key", re.compile(r'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----')),
    ("Hardcoded credential assignment", re.compile(
        r'\b(?:api[_-]?key|secret|token|password|auth_token)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.+=/]{24,})["\']',
        re.I
    )),
]

PLACEHOLDER_SUBSTRINGS = (
    "placeholder", "example", "dummy", "redacted", "your-", "your_",
    "<token>", "<key>", "...", "xxx", "test-token", "changeme", "000000",
)

# Checks identified as having >5% prevalence across public repositories become observations
HIGH_PREVALENCE_CHECKS: set[str] = {"D002", "D003", "D004", "D006"}


def set_high_prevalence_checks(check_ids: set[str]) -> None:
    """Configure which checks are treated as observations due to >5% baseline rate."""
    global HIGH_PREVALENCE_CHECKS
    HIGH_PREVALENCE_CHECKS = set(check_ids)


def extract_backticked_paths(text: str) -> list[str]:
    """Find backticked strings that look like file or directory paths."""
    candidates = re.findall(r'`([^`\n]+)`', text)
    paths: list[str] = []
    for cand in candidates:
        cand = cand.strip()
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
        if " " in cand and not cand.startswith("./"):
            continue
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
    cleaned = re.sub(r'^\s*(?:[-*+]|\d+\.)\s+', '', text).strip()
    cleaned = cleaned.lower().rstrip(".;,!?")
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def parse_markdown_sections(lines: list[str]) -> list[dict[str, Any]]:
    """Partition markdown lines into sections with token estimates."""
    sections: list[dict[str, Any]] = []
    current_title = "(intro)"
    current_start = 1
    current_lines: list[str] = []

    for idx, line in enumerate(lines, start=1):
        m = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if m:
            if current_lines:
                sec_text = "\n".join(current_lines)
                sections.append({
                    "title": current_title,
                    "start_line": current_start,
                    "tokens": estimate_tokens(sec_text),
                })
            current_title = m.group(2).strip()
            current_start = idx
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines)
        sections.append({
            "title": current_title,
            "start_line": current_start,
            "tokens": estimate_tokens(sec_text),
        })

    return sections


def check_file(
    file_path: Path,
    root: Path | None = None,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    graph_context_text: str | None = None,
    content: str | None = None,
) -> list[dict[str, Any]]:
    """Run deterministic checks D001–D008 on an agent instruction file.

    Returns a list of finding dicts: {id, line, message, fix, kind}.
    """
    if root is None:
        root = file_path.parent if file_path.parent != Path("") else Path(".")

    if content is None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

    lines = content.splitlines()
    findings: list[dict[str, Any]] = []

    # Combined text for graph guardrail comparison (context files or self)
    all_context_text = f"{content}\n{graph_context_text or ''}"

    manifest_scripts = get_manifest_scripts(root)
    seen_rules: dict[str, int] = {}

    # Extract guardrails in the context (negative prohibitions)
    guardrails: list[tuple[str, str]] = []  # (normalized_action, original_phrase)
    for g_line in all_context_text.splitlines():
        # Match "never <action>", "do not <action>", "must not <action>"
        gm = re.search(r'\b(?:never|do not|don\'t|must not|prohibit(?:ed)?|disallow(?:ed)?)\s+([a-zA-Z0-9_\-\s]{4,60})', g_line, re.I)
        if gm:
            # Strip trailing conditional/adverbial phrases like "under any circumstances", "unless", "without"
            raw_action = re.split(r'\b(?:under\s+any|without|when|unless|if|in\s+case|except)\b', gm.group(1), flags=re.I)[0]
            action = normalize_rule(raw_action)
            if len(action) >= 6:
                guardrails.append((action, gm.group(0).strip()))

    # Per-line checks
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
                    "kind": "observation" if "D001" in HIGH_PREVALENCE_CHECKS else "warning",
                })

        # -------------------------------------------------------------
        # D002: backticked path that does not exist (flag)
        # -------------------------------------------------------------
        if not IMPORT_RE.search(line):
            b_paths = extract_backticked_paths(line)
            for p_str in b_paths:
                cand1 = file_path.parent / p_str
                cand2 = root / p_str
                if not cand1.exists() and not cand2.exists():
                    findings.append({
                        "id": "D002",
                        "line": idx,
                        "message": f"Referenced path '{p_str}' does not exist on disk",
                        "fix": None,
                        "kind": "observation" if "D002" in HIGH_PREVALENCE_CHECKS else "warning",
                    })

        # -------------------------------------------------------------
        # D003: named script/command not defined in manifests (flag)
        # -------------------------------------------------------------
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
                    "kind": "observation" if "D003" in HIGH_PREVALENCE_CHECKS else "warning",
                })

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
                    "kind": "observation" if "D003" in HIGH_PREVALENCE_CHECKS else "warning",
                })

        poetry_match = re.search(r'\bpoetry\s+run\s+([a-zA-Z0-9_.-]+)', line)
        if poetry_match and (root / "pyproject.toml").is_file():
            script_name = poetry_match.group(1)
            defined = manifest_scripts["pyproject.toml"]
            if defined and script_name not in defined:
                findings.append({
                    "id": "D003",
                    "line": idx,
                    "message": f"Command references undefined poetry script '{script_name}' (not in pyproject.toml)",
                    "fix": None,
                    "kind": "observation" if "D003" in HIGH_PREVALENCE_CHECKS else "warning",
                })

        # -------------------------------------------------------------
        # D004: duplicate rule, normalised (keep first, auto-fix: remove)
        # -------------------------------------------------------------
        is_bullet = bool(re.match(r'^\s*(?:[-*+]|\d+\.)\s+', line))
        if is_bullet or (not line_stripped.startswith("#") and not line_stripped.startswith("```")):
            norm = normalize_rule(line)
            if len(norm) >= 6:
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
                        "kind": "observation" if "D004" in HIGH_PREVALENCE_CHECKS else "warning",
                    })
                else:
                    seen_rules[norm] = idx

        # -------------------------------------------------------------
        # D005: rule contradicts a guardrail in the same graph (flag)
        # -------------------------------------------------------------
        # Check if line commands an action that a guardrail forbids or disables rules
        lower_line = line.lower()
        if re.search(r'\b(?:rules? in [^\n]+ do not apply|ignore safety rules?|bypass (?:guardrails?|checks?))\b', lower_line):
            findings.append({
                "id": "D005",
                "line": idx,
                "message": f"Rule explicitly disables or bypasses guardrails: '{line_stripped}'",
                "fix": None,
                "kind": "observation" if "D005" in HIGH_PREVALENCE_CHECKS else "warning",
            })
        else:
            # Check if affirmative command directly violates an existing guardrail
            is_negative = bool(re.search(r'\b(?:never|do not|don\'t|must not|prohibit|disallow)\b', lower_line))
            if not is_negative:
                for norm_action, g_orig in guardrails:
                    # If this line instructs doing the guarded action
                    if norm_action in lower_line and len(norm_action) >= 8:
                        findings.append({
                            "id": "D005",
                            "line": idx,
                            "message": f"Rule contradicts guardrail '{g_orig}': '{line_stripped}'",
                            "fix": None,
                            "kind": "observation" if "D005" in HIGH_PREVALENCE_CHECKS else "warning",
                        })
                        break

        # -------------------------------------------------------------
        # D007: secret-shaped value in agent file (flag)
        # -------------------------------------------------------------
        for secret_name, pat in SECRET_PATTERNS:
            sm = pat.search(line)
            if sm:
                matched_val = sm.group(1) if sm.groups() else sm.group(0)
                # Check for harmless placeholder substrings
                low_val = matched_val.lower()
                if not any(ph in low_val for ph in PLACEHOLDER_SUBSTRINGS):
                    masked = matched_val[:4] + "…" + matched_val[-4:] if len(matched_val) > 8 else "…"
                    findings.append({
                        "id": "D007",
                        "line": idx,
                        "message": f"Secret-shaped value ({secret_name}) found: '{masked}'. Never expose credentials to models.",
                        "fix": None,
                        "kind": "observation" if "D007" in HIGH_PREVALENCE_CHECKS else "warning",
                    })
                    break

        # -------------------------------------------------------------
        # D008: ANSI/terminal escape in text (auto-fix: strip)
        # -------------------------------------------------------------
        if ANSI_ESCAPE_RE.search(line):
            cleaned_line = ANSI_ESCAPE_RE.sub("", line)
            findings.append({
                "id": "D008",
                "line": idx,
                "message": "ANSI/terminal escape code detected in text (context-protector)",
                "fix": {
                    "description": "Strip ANSI escape characters",
                    "replacement": cleaned_line,
                },
                "kind": "observation" if "D008" in HIGH_PREVALENCE_CHECKS else "warning",
            })

    # -----------------------------------------------------------------
    # D006: file over token budget (default 1500; suggest sections to cut)
    # -----------------------------------------------------------------
    total_file_tokens = estimate_tokens(content)
    if total_file_tokens > token_budget:
        sections = parse_markdown_sections(lines)
        # Rank sections by size excluding very short ones
        sections.sort(key=lambda s: s["tokens"], reverse=True)
        top_cut_suggestions = [
            f"'{s['title']}' (~{s['tokens']} tokens, line {s['start_line']})"
            for s in sections[:3] if s["tokens"] > 100
        ]
        sugg_str = "; ".join(top_cut_suggestions) if top_cut_suggestions else "trim large prose blocks"
        findings.append({
            "id": "D006",
            "line": 1,
            "message": f"File exceeds token budget ({total_file_tokens} > {token_budget} tokens; ~{total_file_tokens - token_budget} over). Suggested sections to cut: {sugg_str}",
            "fix": None,
            "kind": "observation" if "D006" in HIGH_PREVALENCE_CHECKS else "warning",
        })

    # Sort findings by line number
    findings.sort(key=lambda f: f["line"])
    return findings


def apply_fixes(content: str, findings: list[dict[str, Any]]) -> tuple[str, int]:
    """Apply safe auto-fixes to content in-place.

    Returns:
        (updated_content, number_of_fixes_applied)
    """
    fixable = [f for f in findings if f.get("fix") is not None and f["fix"].get("replacement") is not None]
    if not fixable:
        return content, 0

    fixable.sort(key=lambda x: x["line"], reverse=True)
    lines = content.splitlines(keepends=True)
    fixed_count = 0

    for f in fixable:
        line_idx = f["line"] - 1
        if 0 <= line_idx < len(lines):
            repl = f["fix"]["replacement"]
            if repl == "":
                del lines[line_idx]
                fixed_count += 1
            else:
                lines[line_idx] = repl if repl.endswith("\n") else repl + "\n"
                fixed_count += 1

    return "".join(lines), fixed_count


def check_text(
    content: str,
    filename: str = "AGENTS.md",
    root: Path | None = None,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    graph_context_text: str | None = None,
) -> list[dict[str, Any]]:
    """Run deterministic checks D001–D008 directly on string content."""
    return check_file(
        file_path=Path(filename),
        root=root or Path("."),
        token_budget=token_budget,
        graph_context_text=graph_context_text,
        content=content,
    )
