"""Machine-level agent configuration discovery and scanning with consent gating.

Discovers user-level agent configs (~/.claude, ~/.cursor, VS Code user settings, ~/.gemini)
and inspects them using Sentinel's security engine without executing anything.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import contract, core


@dataclass
class MachineTarget:
    tool: str
    kind: str
    path: Path
    description: str


def get_user_settings_paths(home: Path, env: dict[str, str] | None = None) -> list[Path]:
    """Return platform-specific user settings file candidates for VS Code and Cursor."""
    env = os.environ if env is None else env
    candidates: list[Path] = []

    # Windows APPDATA paths
    appdata = env.get("APPDATA")
    if appdata:
        appdata_p = Path(appdata)
    else:
        appdata_p = home / "AppData" / "Roaming"

    candidates.extend([
        appdata_p / "Code" / "User" / "settings.json",
        appdata_p / "Code" / "User" / "tasks.json",
        appdata_p / "Cursor" / "User" / "settings.json",
    ])

    # macOS Application Support paths
    candidates.extend([
        home / "Library" / "Application Support" / "Code" / "User" / "settings.json",
        home / "Library" / "Application Support" / "Code" / "User" / "tasks.json",
        home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
    ])

    # Linux / XDG config paths
    xdg_config = env.get("XDG_CONFIG_HOME")
    config_home = Path(xdg_config) if xdg_config else (home / ".config")
    candidates.extend([
        config_home / "Code" / "User" / "settings.json",
        config_home / "Code" / "User" / "tasks.json",
        config_home / "Cursor" / "User" / "settings.json",
    ])

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[Path] = []
    for c in candidates:
        norm = str(c.resolve()) if c.exists() else str(c)
        if norm not in seen:
            seen.add(norm)
            result.append(c)
    return result


def discover_machine_targets(home: Path | None = None, env: dict[str, str] | None = None) -> list[MachineTarget]:
    """Discover user-level agent configs across ~/.claude, ~/.cursor, VS Code user settings, and ~/.gemini."""
    h = (home or Path.home()).resolve()
    targets: list[MachineTarget] = []

    # 1. Claude Code (~/.claude)
    claude_dir = h / ".claude"
    if claude_dir.is_dir():
        for sname in ("settings.json", "settings.local.json"):
            sp = claude_dir / sname
            if sp.is_file():
                targets.append(MachineTarget("claude", "settings", sp, f"Claude user config ({sname})"))
        cmd_file = claude_dir / "CLAUDE.md"
        if cmd_file.is_file():
            targets.append(MachineTarget("claude", "instructions", cmd_file, "Claude global instructions (CLAUDE.md)"))
        rules_dir = claude_dir / "rules"
        if rules_dir.is_dir():
            for rp in sorted(rules_dir.glob("*.md")):
                if rp.is_file():
                    targets.append(MachineTarget("claude", "rules", rp, f"Claude user rule ({rp.name})"))

    # 2. Cursor (~/.cursor and ~/.cursorrules)
    cursorrules = h / ".cursorrules"
    if cursorrules.is_file():
        targets.append(MachineTarget("cursor", "instructions", cursorrules, "Cursor global rules (.cursorrules)"))
    cursor_dir = h / ".cursor"
    if cursor_dir.is_dir():
        rules_dir = cursor_dir / "rules"
        if rules_dir.is_dir():
            for rp in sorted(rules_dir.glob("*.mdc")):
                if rp.is_file():
                    targets.append(MachineTarget("cursor", "rules", rp, f"Cursor rule ({rp.name})"))

    # 3. VS Code / Cursor User settings
    for usp in get_user_settings_paths(h, env):
        if usp.is_file():
            tool = "cursor" if "Cursor" in str(usp) else "vscode"
            kind = "tasks" if usp.name == "tasks.json" else "settings"
            targets.append(MachineTarget(tool, kind, usp, f"{tool.upper()} user {kind}"))

    # 4. Gemini CLI (~/.gemini)
    gemini_dir = h / ".gemini"
    if gemini_dir.is_dir():
        s = gemini_dir / "settings.json"
        if s.is_file():
            targets.append(MachineTarget("gemini", "settings", s, "Gemini user settings"))
        gmd = gemini_dir / "GEMINI.md"
        if gmd.is_file():
            targets.append(MachineTarget("gemini", "instructions", gmd, "Gemini user instructions (GEMINI.md)"))

    return targets


def prompt_consent(interactive: bool | None = None, auto_yes: bool = False,
                   in_stream: Any = None, out_stream: Any = None) -> bool:
    """Check user consent before reading external configuration surfaces outside the repository."""
    if auto_yes:
        return True

    in_s = in_stream or sys.stdin
    out_s = out_stream or sys.stderr

    if interactive is None:
        try:
            interactive = hasattr(in_s, "isatty") and in_s.isatty()
        except Exception:
            interactive = False

    if not interactive:
        out_s.write(
            "sentinel: scan --machine requires user consent to inspect configurations outside the repository.\n"
            "Pass --yes or run in an interactive terminal to proceed.\n"
        )
        out_s.flush()
        return False

    out_s.write(
        "\nSentinel: Machine-level scan will inspect user AI agent configurations outside the repository:\n"
        "  - ~/.claude      (Claude Code global settings, hooks, and instructions)\n"
        "  - ~/.cursor      (Cursor global rules and .cursorrules)\n"
        "  - VS Code / Cursor user settings (folderOpen tasks, global agent settings)\n"
        "  - ~/.gemini      (Gemini CLI global settings and instructions)\n"
        "\nThese configurations govern AI agents across every workspace on this machine.\n"
        "Proceed with machine scan? [y/N]: "
    )
    out_s.flush()

    try:
        line = in_s.readline().strip().lower()
        return line in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def scan_machine(targets: list[MachineTarget], semantic: bool = False) -> dict[str, Any]:
    """Scan all discovered user-level machine configurations using Sentinel's security engine.

    SECURITY INVARIANT: This function only performs static inspection (read_text / JSON parse).
    It strictly never executes, imports, or spawns any discovered script or hook.
    """
    files: dict[str, dict[str, Any]] = {}

    for t in targets:
        path_str = str(t.path)
        try:
            content = t.path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            continue

        # For settings JSON or tasks JSON, use scan_repo style autoexec discovery on its parent or inspect file
        if t.kind in ("settings", "tasks"):
            settings = core.load_json(t.path)
            findings: list[core.Finding] = []

            # Check hooks in settings
            if isinstance(settings, dict):
                for event, matcher, cmd in core.iter_hook_commands(settings):
                    where = f"{t.tool}:{event}" + (f"[{matcher}]" if matcher else "")
                    findings.append(core.Finding(
                        "S17a", path_str, 25, ceiling=True,
                        evidence=f"machine-level auto-run: {where} -> {cmd} in {path_str}",
                        impact=f"A user-level hook in {t.tool} runs '{cmd}' across all projects on this machine.",
                        fix=f"Review the global hook in {path_str} and remove it if unrecognized."
                    ))

                # Check tasks.json runOn: folderOpen
                if t.kind == "tasks":
                    for task in settings.get("tasks") or []:
                        if isinstance(task, dict) and (task.get("runOptions") or {}).get("runOn") == "folderOpen":
                            cmd = " ".join([str(task.get("command", ""))] + [str(a) for a in task.get("args") or []]).strip()
                            findings.append(core.Finding(
                                "S17a", path_str, 25, ceiling=True,
                                evidence=f"machine-level folderOpen task: {cmd} in {path_str}",
                                impact=f"A user-level VS Code task executes '{cmd}' whenever any folder is opened on this machine.",
                                fix=f"Remove folderOpen runOptions from {path_str}."
                            ))

            file_score = core.score_file(findings)
            files[path_str] = {
                "score": file_score["score"],
                "verdict": file_score["verdict"],
                "breakdown": file_score["breakdown"],
                "findings": [f.__dict__ for f in findings],
                "description": t.description,
            }

        else:
            # Instruction text surfaces (CLAUDE.md, .cursorrules, .mdc, GEMINI.md)
            res = contract.scan_text(t.path.name, content)
            findings_dicts = []
            for f in res.get("findings", []):
                findings_dicts.append({
                    "rule": f["rule_id"],
                    "file": path_str,
                    "penalty": f["penalty"],
                    "force": f["forces_compromised"],
                    "ceiling": bool(f.get("ceiling")),
                    "evidence": f["message"],
                    "impact": f["impact"],
                    "fix": f["fix"],
                    "line": f.get("line", 1),
                })
            files[path_str] = {
                "score": res["trust_score"],
                "verdict": res["verdict"],
                "breakdown": f"score {res['trust_score']}",
                "findings": findings_dicts,
                "description": t.description,
            }

    scores = [v["score"] for v in files.values()] if files else [100]
    worst_score = min(scores) if scores else 100

    order = {"COMPROMISED": 2, "SUSPICIOUS": 1, "CLEAN": 0}
    verdicts = [v["verdict"] for v in files.values()] if files else ["CLEAN"]
    worst_verdict = max(verdicts, key=lambda v: order.get(v, 0))

    return {
        "verdict": worst_verdict,
        "trust_score": worst_score,
        "files": files,
        "machine_scan": True,
        "targets_discovered": len(targets),
    }
