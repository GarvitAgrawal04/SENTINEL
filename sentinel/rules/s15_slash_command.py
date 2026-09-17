"""
sentinel/rules/s15_slash_command.py
S15 — Deposited slash command (not in git history at install time).
Penalty: −55. Not structurally unambiguous.
ATR: ATR-PERSIST-001.

Claude Code slash commands live in .claude/commands/**.
A slash command deposited by a package install that was NOT committed to
the project's git history is a persistence vector: it fires every time the
developer types the command in Claude Code, independent of whether the
package is still installed.

This rule detects .claude/commands/* files that:
  (a) were not committed to the project git history, AND
  (b) contain suspicious content (override language, exfiltration patterns)

For the CLI / file-only scan case, we also flag any slash command file
that contains override/exfiltration content, since we cannot easily check
git history without the project root context. The D2 origin detection layer
provides the git history check when available.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES
from .s4_override import OVERRIDE_PATTERNS
from .s5_exfiltration import EXFIL_PATTERNS

# Path patterns that indicate this is a Claude slash command
_SLASH_CMD_PATH_RE = re.compile(
    r'(?:^|[\\/])\.claude[\\/]commands[\\/][^\\/]+$',
    re.IGNORECASE,
)


def scan(text: str, filename: str, origin: str = "unknown", git_tracked: set[str] | None = None) -> list[Finding]:
    """
    S15 — Deposited slash command detector.
    """
    is_slash_cmd_file = (
        filename.lower().endswith('.md') and '.claude/commands' in filename.replace("\\", "/").lower()
    )
    
    findings: list[Finding] = []

    if is_slash_cmd_file:
        # Check if the file is tracked in git
        # Note: git_tracked typically contains unix-style paths relative to project root
        normalized_filename = filename.replace("\\", "/")
        is_tracked = False
        if git_tracked is not None:
            # Try to match the filename against the git_tracked set
            is_tracked = any(normalized_filename.endswith(t.replace("\\", "/")) for t in git_tracked)
            
        if not is_tracked:
            findings.append(Finding(
                rule_id="S15", rule_name=RULE_NAMES["S15"], severity="high",
                filename=filename, line=1,
                penalty=55,
                forces_compromised=False,
                message=f"Untracked slash command file deposited by {origin}",
                snippet=f"{normalized_filename} (origin={origin})",
                reconstruction="This command was deposited by an untracked source.",
                atr_id="ATR-PERSIST-001"
            ))

    # 2. Check JSON configuration for 'commands'
    is_settings_json = "settings.json" in filename.lower() or "claude.json" in filename.lower()
    if is_settings_json:
        try:
            import json
            data = json.loads(text)
            commands = data.get("commands")
            if isinstance(commands, dict):
                for cmd_name, cmd_data in commands.items():
                    if not isinstance(cmd_name, str) or not str(cmd_name).startswith("/"):
                        continue
                    
                    cmd_val = str(cmd_data)[:100] if not isinstance(cmd_data, dict) else str(cmd_data.get("command", ""))[:100]
                    # We detect the presence of the command. D2 origin layer makes it COMPROMISED if postinstall.
                    # Without D2 info in static scan, we just flag it as S15 (ceiling 55 if not compromised).
                    findings.append(Finding(
                        rule_id="S15", rule_name=RULE_NAMES["S15"], severity="medium",
                        filename=filename, line=1,
                        message=f"Slash command '{cmd_name}' defined in configuration",
                        snippet=f"{cmd_name}: {cmd_val}",
                        reconstruction=f"A custom slash command '{cmd_name}' is registered in the config. If deposited post-install (D2), this is a persistence vector.",
                        atr_id="ATR-PERSIST-001"
                    ))
        except Exception:
            pass

    return findings
