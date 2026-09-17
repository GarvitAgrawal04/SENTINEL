"""
sentinel/layer0/hooks.py
D3 — Hook Survivability Scan (project-local AND global).

THE MOST IMPORTANT MENTOR-ROUND COMPONENT — PRD §13.3.

Parses .claude/settings.json AND ~/.claude/settings.json using Claude Code's
real nested hook schema (three-level, not flat — flat parsers silently return
CLEAN on real attacks per Appendix F).

Behavior per PRD §13.3:
  - Missing hook path → S10 fires → COMPROMISED
  - PreToolUse + write-family matcher + existing script → S14b fires → SUSPICIOUS
  - Global scope findings report which state the project is in:
    * inheriting a compromised global hook, or
    * shielded by a project-local override

Global/project merge semantics (PRD §16 note, Claude Code docs):
  Arrays (hook lists for a given event) are replaced wholesale when a
  more-specific scope defines the same key. A project with its own
  SessionStart hooks silently replaces a compromised global one for that
  event. A project with no hooks of its own inherits the global array
  unmodified.

Returns structured HookScanResult with per-file findings.
"""
from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sentinel.rules.s10_hook_survivability import extract_hook_commands, scan as s10_scan
from sentinel.rules.s14_write_intercept import scan as s14_scan
from sentinel.rules.base import Finding


@dataclass
class HookScanResult:
    """Structured result of a D3 hook survivability scan."""
    project_settings_path: Optional[Path] = None
    global_settings_path: Optional[Path] = None
    project_findings: list[Finding] = field(default_factory=list)
    global_findings: list[Finding] = field(default_factory=list)
    effective_state: str = "no-hooks-found"
    # One of: "no-hooks-found" | "clean" | "compromised" | "suspicious" |
    #         "global-compromised-shielded" | "global-compromised-inherited"

    @property
    def all_findings(self) -> list[Finding]:
        return self.project_findings + self.global_findings

    def describe_global_state(self) -> str:
        """
        Plain-English description of the effective hook state for the formatter.
        Used by the CLI and API output to explain the global/project relationship.
        """
        if not self.global_settings_path:
            return "No global Claude settings found."
        if not self.global_findings:
            return f"Global settings ({self.global_settings_path}) — no hook issues found."

        if self.project_settings_path:
            # Check if project-local hooks override the global ones
            state = self.effective_state
            if state == "global-compromised-shielded":
                return (
                    f"⚠ Global settings ({self.global_settings_path}) have hook issues, "
                    f"but the project-local settings ({self.project_settings_path}) "
                    f"define their own hooks for the same event — "
                    f"the global compromised hooks are SHIELDED for this project."
                )
            else:
                return (
                    f"🚨 Global settings ({self.global_settings_path}) have hook issues "
                    f"and the project does NOT override them — "
                    f"INHERITED by this project and every other project on this machine."
                )
        return (
            f"🚨 Global settings ({self.global_settings_path}) have hook issues — "
            f"these apply to every Claude Code project on this machine."
        )


def _load_settings(settings_path: Path) -> Optional[dict]:
    """Load and parse a Claude settings JSON file. Returns None on failure."""
    try:
        text = settings_path.read_text(encoding="utf-8", errors="replace")
        return json.loads(text)
    except (OSError, json.JSONDecodeError):
        return None


def _project_overrides_event(project_settings: dict, event: str) -> bool:
    """
    Returns True if the project-local settings define their own hooks for
    a given event type, which would shield a compromised global hook.
    """
    hooks_root = project_settings.get("hooks", {})
    if not isinstance(hooks_root, dict):
        return False
    return event in hooks_root and bool(hooks_root[event])


def scan_hooks(
    project_root: Path,
    project_settings_path: Optional[Path] = None,
) -> HookScanResult:
    """
    D3 — Full hook survivability scan.

    Scans both project-local and global Claude settings for hook issues.
    Reports the effective state the project is in, accounting for global
    inheritance and project-local shielding.

    Parameters
    ----------
    project_root:
        The root directory of the project being scanned.
    project_settings_path:
        Optional explicit path to .claude/settings.json.
        Defaults to project_root / ".claude" / "settings.json".
    """
    result = HookScanResult()

    # ── Project-local settings ────────────────────────────────────────────────
    if project_settings_path is None:
        project_settings_path = project_root / ".claude" / "settings.json"

    if project_settings_path.exists():
        result.project_settings_path = project_settings_path
        text = project_settings_path.read_text(encoding="utf-8", errors="replace")
        result.project_findings.extend(s10_scan(text, str(project_settings_path)))
        result.project_findings.extend(s14_scan(text, str(project_settings_path)))

    # ── Global settings ───────────────────────────────────────────────────────
    home = Path.home()
    # V1: macOS/Linux path only. Windows is V1.5.
    if sys.platform.startswith("win"):
        # Document as V1.5 limitation rather than silently skipping
        global_path = None
    else:
        global_path = home / ".claude" / "settings.json"

    if global_path and global_path.exists():
        result.global_settings_path = global_path
        text = global_path.read_text(encoding="utf-8", errors="replace")
        result.global_findings.extend(s10_scan(text, str(global_path)))
        result.global_findings.extend(s14_scan(text, str(global_path)))

    # ── Determine effective state ─────────────────────────────────────────────
    project_settings = None
    if result.project_settings_path and result.project_settings_path.exists():
        project_settings = _load_settings(result.project_settings_path)

    has_project_issues = bool(result.project_findings)
    has_global_issues  = bool(result.global_findings)

    if not has_project_issues and not has_global_issues:
        result.effective_state = "clean" if (
            result.project_settings_path or result.global_settings_path
        ) else "no-hooks-found"
    elif has_project_issues:
        # Determine worst verdict in project findings
        if any(f.forces_compromised for f in result.project_findings):
            result.effective_state = "compromised"
        else:
            result.effective_state = "suspicious"
    elif has_global_issues:
        # Check if the project shields the compromised global hooks
        if project_settings:
            # Find all events with global issues
            global_settings = _load_settings(global_path) if global_path and global_path.exists() else {}
            global_hook_events = set()
            if global_settings:
                for f in result.global_findings:
                    # Infer the event from the finding snippet
                    if "event=" in f.snippet:
                        for part in f.snippet.split(","):
                            if "event=" in part:
                                evt = part.strip().replace("event=", "").strip("'\"")
                                global_hook_events.add(evt)

            if global_hook_events and all(
                _project_overrides_event(project_settings, evt)
                for evt in global_hook_events
            ):
                result.effective_state = "global-compromised-shielded"
            else:
                result.effective_state = "global-compromised-inherited"
        else:
            result.effective_state = "global-compromised-inherited"

    return result
