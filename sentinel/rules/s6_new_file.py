"""
sentinel/rules/s6_new_file.py
S6 — New / modified file in a dependency PR (trigger, feeds Layer 2).
Penalty: −15. Not structurally unambiguous.
ATR: ATR-RUG-001.

Fires when a file appears to be new (no prior version available from
Layer 2) AND has other findings, or when the character-level delta
exceeds threshold values that indicate substantial rewriting.

S6 requires Layer 2 data (prior-version diff). It is invoked by the
API's /scan/package endpoint which fetches prior versions from registries.
It is NOT invoked on /scan/file because that endpoint has no prior-version
concept. The scoring still applies S6's −15 if it fires.
"""
from __future__ import annotations
from typing import Optional
from .base import Finding, RULE_NAMES


def scan(text: str, filename: str, origin: str = "unknown", diff_status: dict[str, str] | None = None) -> list[Finding]:
    """
    S6 - New / modified file in dependency PR.
    """
    findings: list[Finding] = []
    
    # Identify agent-trust surface files
    normalized_lower = filename.replace("\\", "/").lower()
    is_surface = (
        "claude.md" in normalized_lower or
        ".claude" in normalized_lower or
        ".mcp.json" in normalized_lower or
        ".cursor" in normalized_lower or
        ".github/copilot" in normalized_lower or
        "skill.md" in normalized_lower or
        "agents.md" in normalized_lower
    )

    if not is_surface:
        return findings

    # Check if the file was added or modified
    status = "unknown"
    if diff_status:
        # Match using base filenames or normalized paths
        for k, v in diff_status.items():
            if normalized_lower.endswith(k.replace("\\", "/").lower()):
                status = v
                break
                
    if status in {"added", "modified"} or origin in {"postinstall-suspected", "postinstall-confirmed"}:
        findings.append(Finding(
            rule_id="S6",
            rule_name=RULE_NAMES["S6"],
            severity="low",
            filename=filename,
            line=1,
            message=f"Agent-trust surface file was {status} (origin: {origin}).",
            snippet=f"{filename} status: {status} (origin: {origin})",
            reconstruction=(
                "This agent instruction/configuration file was generated or modified in this change. "
                "S6 applies a baseline penalty for the structural vector."
            ),
            atr_id="ATR-RUG-001",
        ))

    return findings
