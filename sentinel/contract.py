"""The JSON shape the frontend, the VS Code extension and the old Action already consume.

v1 promised: "Add fields additively; never remove or rename existing keys." This keeps that promise on top of the
v5 engine, so nothing downstream has to change on demo week.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from . import core
from .render import TITLE


def _severity(f: dict) -> str:
    return "high" if f["force"] or f["penalty"] >= 40 else "medium" if f["ceiling"] or f["penalty"] >= 25 else "low"


def _sentence_case(title: str) -> str:
    out = title.capitalize()
    for word in ("MCP", "API", "AI", "URL"):
        out = re.sub(rf"\b{word.lower()}\b", word, out, flags=re.I)
    return out


def _line_of(text: str | None, evidence: str) -> int:
    """Which line should a client underline? 1-based; 0 only when there is genuinely nothing to point at."""
    if not text:
        return 0
    lines = text.splitlines()
    for m in list(re.finditer(r'"([^"]{12,})"', evidence)) + list(re.finditer(r"`([^`]{6,})`", evidence)):
        needle = " ".join(m.group(1).split())[:40]
        for i, line in enumerate(lines, 1):
            if needle in " ".join(line.split()):
                return i
    at = re.search(r"offsets \[(\d+)", evidence)                       # hidden characters: the engine reports offsets
    if at:
        return text.count("\n", 0, int(at.group(1))) + 1
    if "hidden text" in evidence:                                       # a finding inside decoded hidden text
        bad = core.invisible_chars(text)
        if bad:
            return text.count("\n", 0, bad[0][0]) + 1
    return 0


def legacy_result(filename: str, report: dict, text: str | None = None) -> dict:
    """Collapse a v5 report into one v1-shaped result."""
    findings, scores, breakdown = [], [], []
    for name, v in report["files"].items():
        scores.append(v["score"])
        breakdown.append(f"{name}: {v['breakdown']}")
        for f in v["findings"]:
            findings.append({
                "rule_id": f["rule"], "rule_name": _sentence_case(TITLE.get(f["rule"], f["rule"])), "severity": _severity(f),
                "filename": filename if len(report["files"]) == 1 else name, "line": _line_of(text, f["evidence"]),
                "message": f["evidence"], "snippet": f["evidence"][:240], "penalty": f["penalty"],
                "ceiling": 79 if f["ceiling"] else None, "forces_compromised": f["force"],
                "reconstruction": f["impact"], "atr_id": None,
                "impact": f["impact"], "fix": f["fix"],                          # additive, v5
            })
    verdict = report["verdict"]
    return {"filename": filename, "trust_score": min(scores) if scores else 100,
            "color_band": {"CLEAN": "green", "SUSPICIOUS": "amber", "COMPROMISED": "red"}[verdict], "verdict": verdict,
            "findings": findings, "layer3_result": None, "origin": "unknown",
            "engine": "v5", "formula_version": report["formula_version"], "breakdown": breakdown,   # additive, v5
            "guide": {"steps": list(dict.fromkeys(f["fix"] for f in findings))}}


def _place(filename: str) -> str:
    """Where would this uploaded file live in a repository? An unknown name is treated as an instruction file."""
    name = Path(filename.replace("\\", "/")).name
    low = name.lower()
    if low in ("settings.json", "settings.local.json"):
        return ".gemini/settings.json" if "gemini" in filename.lower() else ".claude/" + low
    if low == "tasks.json":
        return ".vscode/tasks.json"
    if low.endswith(".json"):                       # mcp.json, claude.json, any other agent/MCP config
        return ".mcp.json"
    if low.endswith(".mdc"):
        return ".cursor/rules/" + name
    if low in (".cursorrules", "agents.md", "gemini.md", "claude.md"):
        return {".cursorrules": ".cursorrules", "agents.md": "AGENTS.md", "gemini.md": "GEMINI.md", "claude.md": "CLAUDE.md"}[low]
    return "CLAUDE.md"


def scan_text(filename: str, text: str) -> dict:
    """One uploaded file, no repository around it (web demo, VS Code on an arbitrary buffer)."""
    with tempfile.TemporaryDirectory(prefix="sentinel-") as tmp:
        root = Path(tmp)
        target = root / _place(filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        report = core.scan_repo(root, repo_context=False)
    return legacy_result(filename, report, text)


def _place_loose(filename: str, taken: set[str]) -> str | None:
    """Several loose files picked in a file dialog have no folders, so `settings.json` would sit at the root, where no
    agent reads it, and the scan would say CLEAN about a hook that pipes curl into sh. Put each file where its tool
    would look for it. Unknown text files are treated as instructions, each in its own slot."""
    low = filename.lower()
    known = low in ("settings.json", "settings.local.json", "tasks.json", ".cursorrules", "agents.md", "gemini.md", "claude.md",
                    "copilot-instructions.md") or low.endswith((".json", ".mdc"))
    if low == "copilot-instructions.md":
        options = [".github/copilot-instructions.md"]
    elif known:
        first = _place(filename)
        options = [first] + {".claude/settings.json": [".gemini/settings.json"], ".mcp.json": [".cursor/mcp.json", ".vscode/mcp.json"]}.get(first, [])
    else:
        stem = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in filename)[:60] or "file"
        options = [f"uploaded/{stem}/SKILL.md"]
    return next((o for o in options if o not in taken), None)


def scan_files(files: dict[str, str]) -> dict:
    """Several uploaded files. With folders in the names it is a repository: full context, S10 / S17b included.
    Without any folder it is a handful of loose files: each is placed where its tool would read it, and rules that need
    the rest of the repository (is the hook's script missing?) are switched off, exactly as for a single file."""
    names = {k: k.replace("\\", "/").lstrip("/") for k in files}
    loose = bool(files) and not any("/" in v for v in names.values())
    shown: dict[str, str] = {}                     # path inside the sandbox -> the name the person uploaded
    skipped: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sentinel-") as tmp:
        root = Path(tmp).resolve()
        for original, text in files.items():
            rel = _place_loose(names[original], set(shown)) if loose else names[original]
            if rel is None:
                skipped.append(original)
                continue
            target = (root / rel).resolve()
            if root not in target.parents:                                # no path traversal out of the sandbox dir
                skipped.append(original)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            shown[target.relative_to(root).as_posix()] = original
        report = core.scan_repo(root, repo_context=not loose)
    per_file = []
    for placed, v in report["files"].items():
        name = shown.get(placed, placed)
        per_file.append(legacy_result(name, {**report, "files": {name: v}, "verdict": v["verdict"]}, files.get(name)))
    return {"verdict": report["verdict"], "files": per_file, "report": report,
            "treated_as": {orig: placed for placed, orig in shown.items() if orig != placed} if loose else {}, "skipped": skipped}
