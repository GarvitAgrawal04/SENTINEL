"""
sentinel/rules/s10_hook_survivability.py
S10 — Hook references a missing path (any Claude hook event type).
Penalty: −70. Structurally unambiguous → forces COMPROMISED.
ATR: ATR-HOOK-001.

ChainDrop / Shai-Hulud planted a SessionStart hook in .claude/settings.json
pointing to .claude/setup.mjs. When the npm package was uninstalled, the
script was removed but the hook entry survived — firing on every Claude Code
session start, independent of whether the package was still installed.

This rule is separate from S14 (write-intercept hooks):
  S10: any hook type where the script path is missing → COMPROMISED
  S14a: write-intercept hook specifically, missing path → COMPROMISED
  S14b: write-intercept hook specifically, existing path → SUSPICIOUS

S10 is triggered by D3 (hook.py) which parses .claude/settings.json and
~/.claude/settings.json using Claude Code's real nested schema.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from .base import Finding, RULE_NAMES


# ── Hook schema parser (PRD §20, note 9: port from Appendix F) ────────────────
# Claude Code's settings.json hook schema (confirmed docs.claude.com, Sept 2026):
#
# {
#   "hooks": {
#     "EventType": [                  // e.g. "PreToolUse", "SessionStart"
#       {
#         "matcher": "...",           // optional tool/command matcher
#         "hooks": [
#           { "type": "command", "command": "..." }
#         ]
#       }
#     ]
#   }
# }
#
# A flat-schema parser (looking only for "command" at the top level) silently
# returns CLEAN on real attacks. We use the three-level nested structure.


def extract_hook_commands(settings: dict) -> list[dict]:
    """
    Extract all (event, matcher, command) triples from a Claude settings dict.

    Returns a list of dicts:
    {
        "event":   str,   # e.g. "SessionStart"
        "matcher": str,   # e.g. "Write|Edit|MultiEdit" or "" for no matcher
        "command": str,   # e.g. ".claude/setup.mjs" or a shell command
    }

    Ported from Appendix F's extractHookCommands (real, tested against 8 cases).
    """
    results: list[dict] = []
    hooks_root = settings.get("hooks", {})
    if not isinstance(hooks_root, dict):
        return results

    for event, hook_groups in hooks_root.items():
        if not isinstance(hook_groups, list):
            continue
        for group in hook_groups:
            if not isinstance(group, dict):
                continue
            matcher = group.get("matcher", "") or ""
            inner_hooks = group.get("hooks", [])
            if not isinstance(inner_hooks, list):
                continue
            for hook_entry in inner_hooks:
                if not isinstance(hook_entry, dict):
                    continue
                if hook_entry.get("type") == "command":
                    cmd = hook_entry.get("command", "")
                    results.append({
                        "event":   event,
                        "matcher": matcher,
                        "command": cmd,
                    })
    return results


def _resolve_script_path(command: str, settings_file: str) -> str | None:
    first_token = command.strip().split()[0] if command.strip() else ""
    if first_token in ("sh", "bash", "zsh", "fish", "node", "python", "python3",
                       "npx", "deno", "bun", "ruby", "perl", "echo", "make", "git", "npm", "pnpm", "yarn", "cmd", "pwsh"):
        parts = command.strip().split()
        if len(parts) > 1:
            if parts[1] == "-c":
                import shlex
                try:
                    inner_cmd = shlex.split(command)[2]
                    return _resolve_script_path(inner_cmd, settings_file)
                except Exception:
                    return None
            first_token = parts[1]
        else:
            return None

    # If the token has no slashes and doesn't have a script extension, it's a global binary
    if "/" not in first_token and "\\" not in first_token and not first_token.endswith((".js", ".mjs", ".cjs", ".ts", ".py", ".sh", ".ps1")):
        return None

    settings_path = Path(settings_file)
    if settings_path.parent.name == ".claude":
        base_dir = settings_path.parent.parent
    else:
        base_dir = settings_path.parent
        
    if first_token.startswith("~/") or first_token.startswith("~\\"):
        # Replace ~ with base_dir (which is home if this is global settings)
        candidate = base_dir / first_token[2:]
    else:
        candidate = Path(first_token)
        if not candidate.is_absolute():
            candidate = base_dir / first_token

    # Do not call .resolve() as it might resolve symlinks or fail on Windows
    # Just format the string nicely
    return str(candidate).replace('\\', '/')


def scan(text: str, filename: str) -> list[Finding]:
    """
    S10 — Hook survivability scan.

    Parses the Claude settings JSON, extracts all hook commands using the
    three-level nested schema, and checks whether each referenced script
    path actually exists on disk.

    Missing path → COMPROMISED (S10).
    """
    findings: list[Finding] = []
    try:
        settings = json.loads(text)
    except json.JSONDecodeError:
        return findings

    is_global = "home" in Path(filename).parts or "Users" in Path(filename).parts or "~" in filename

    hook_commands = extract_hook_commands(settings)
    for hook in hook_commands:
        event   = hook["event"]
        matcher = hook["matcher"]
        command = hook["command"]

        if not command:
            continue

        resolved = _resolve_script_path(command, filename)
        if resolved is None:
            # Cannot resolve to a filesystem path — not an S10 finding
            # (e.g. `echo hello` or other shell commands are fine)
            continue

        # Convert to Path to check existence, but replace forward slashes back for Windows
        if not Path(resolved).exists():
            prefix = "global hook: " if is_global else ""
            # S10: Hook references a missing path
            findings.append(Finding(
                rule_id="S10",
                rule_name=RULE_NAMES["S10"],
                severity="high",
                filename=filename,
                line=1,
                message=(
                    f"{event} hook references missing path: '{command}' "
                    f"(resolved: {resolved})"
                ),
                snippet=f"{prefix}event={event}, matcher={matcher!r}, command={command!r}",
                reconstruction=(
                    f"The '{event}' hook references a script at '{command}' "
                    f"that does not exist on disk. "
                    f"This is ChainDrop's exact persistence mechanism: "
                    f"the hook was planted by a now-uninstalled npm package "
                    f"('.claude/setup.mjs' survived `npm uninstall`). "
                    f"Claude Code will attempt to execute this path on every "
                    f"'{event}' event — including every session start. "
                    f"The missing script may be re-deposited by a future install "
                    f"or replaced with a different payload."
                ),
                atr_id="ATR-HOOK-001",
            ))
    return findings
