"""
sentinel/rules/s14_write_intercept.py
S14 — Write-intercept hook (PreToolUse + write-family matcher).
ATR: ATR-HOOK-002.

Two distinct sub-rules with different verdict semantics:

S14a — Write-intercept hook, MISSING path
  Penalty: −70. Structurally unambiguous → forces COMPROMISED.
  A hook that intercepts all file writes but references a non-existent
  script is unambiguously malicious (or dangerously broken).

S14b — Write-intercept hook, EXISTING path
  No direct penalty. Caps score at 60 → SUSPICIOUS.
  Cannot be certified CLEAN without reading the script content.
  Cannot be forced COMPROMISED without evidence of malicious intent.
  "SUSPICIOUS is the correct honest answer." — PRD §11

PRD context (Phase 4 prediction):
  A PreToolUse hook matching Write|Edit|MultiEdit intercepts EVERY file write
  Claude Code performs — the developer sees a normal run while every output
  has been processed first.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from .base import Finding, RULE_NAMES
from .s10_hook_survivability import extract_hook_commands, _resolve_script_path

# Write-family tool names (Claude Code PreToolUse event)
_WRITE_FAMILY_RE = re.compile(
    r'\b(?:Write|Edit|MultiEdit|str_replace_editor|str_replace_based_edit_tool|'
    r'NotebookEdit|patch|write_file|save)\b',
    re.IGNORECASE,
)


def scan(text: str, filename: str) -> list[Finding]:
    """
    S14 — Write-intercept hook detector.

    Parses .claude/settings.json (project-local or global).
    Returns one Finding per write-intercept hook found, with rule_id
    set to "S14a" (missing path) or "S14b" (existing path).
    """
    findings: list[Finding] = []
    try:
        settings = json.loads(text)
    except json.JSONDecodeError:
        return findings

    hook_commands = extract_hook_commands(settings)
    for hook in hook_commands:
        event   = hook["event"]
        matcher = hook["matcher"]
        command = hook["command"]

        if event != "PreToolUse":
            continue
        if not (not matcher or matcher == "*" or matcher == ".*" or _WRITE_FAMILY_RE.search(matcher)):
            continue
        if not command:
            continue

        resolved = _resolve_script_path(command, filename)
        
        # If it's a global config, mark evidence as global
        is_global = "~" in filename or "home" in filename or "Users" in filename
        snippet_suffix = " (global)" if is_global else ""

        if resolved is None:
            # Inline command
            findings.append(Finding(
                rule_id="S14b",
                rule_name=RULE_NAMES["S14b"],
                severity="medium",
                penalty=0, # Ceiling rule
                forces_compromised=False,
                ceiling=60,
                filename=filename,
                line=1,
                message=(
                    f"PreToolUse hook with write-family matcher ('{matcher}') "
                    f"runs an inline shell command: {command[:80]!r}"
                ),
                snippet=f"event=PreToolUse, matcher={matcher!r}, command={command!r}{snippet_suffix}",
                reconstruction=(
                    f"This hook intercepts all {matcher} operations performed by Claude Code "
                    f"and runs: '{command[:80]}'. "
                    f"An agent that runs this could have all its file writes intercepted. "
                    f"Sentinel cannot certify this as safe without inspecting the command. "
                    f"SUSPICIOUS is the correct answer — a human must review this hook."
                ),
                atr_id="ATR-HOOK-002",
            ))
        elif not Path(resolved).is_file():
            # Missing file! Structurally unambiguous S14a
            findings.append(Finding(
                rule_id="S14a",
                rule_name=RULE_NAMES["S14a"],
                severity="high",
                forces_compromised=True,
                filename=filename,
                line=1,
                message=(
                    f"Write-intercept hook (PreToolUse '{matcher}') references "
                    f"missing script: '{command}' (resolved: {resolved})"
                ),
                snippet=f"event=PreToolUse, matcher={matcher!r}, command={command!r}{snippet_suffix}",
                reconstruction=(
                    f"A PreToolUse hook matching '{matcher}' (all file writes) "
                    f"references '{command}' which does not exist on disk. "
                    f"This hook would intercept every file Claude Code writes and "
                    f"attempt to execute a non-existent script — "
                    f"the missing script may be re-deposited by a subsequent install. "
                    f"This is structurally unambiguous: COMPROMISED."
                ),
                atr_id="ATR-HOOK-002",
            ))
        else:
            # File exists -> S14b ceiling
            findings.append(Finding(
                rule_id="S14b",
                rule_name=RULE_NAMES["S14b"],
                severity="medium",
                penalty=0, # Ceiling rule
                forces_compromised=False,
                ceiling=60,
                filename=filename,
                line=1,
                message=(
                    f"Write-intercept hook (PreToolUse '{matcher}') references "
                    f"existing script: '{command}'"
                ),
                snippet=f"event=PreToolUse, matcher={matcher!r}, command={command!r}{snippet_suffix}",
                reconstruction=(
                    f"A PreToolUse hook with write-family matcher '{matcher}' "
                    f"exists and references a script that IS present at '{resolved}'. "
                    f"Sentinel deliberately does not mark this COMPROMISED — "
                    f"a formatter hook uses the same PreToolUse/Write mechanism as a "
                    f"write-interceptor. A path check alone cannot certify the script safe. "
                    f"SUSPICIOUS is the correct honest answer. A human must inspect '{resolved}'."
                ),
                atr_id="ATR-HOOK-002",
            ))
    return findings
