"""
sentinel/rules/s16_mcp_autoenable.py
S16 — enableAllProjectMcpServers: true in Claude settings.
Ceiling semantics (NOT a fixed penalty):
  - Alone: score capped at 60 → SUSPICIOUS by design.
  - Combined with origin: postinstall-suspected or postinstall-confirmed → COMPROMISED.
ATR: ATR-MCP-005.

Rationale: enableAllProjectMcpServers:true means every MCP server in every
project the user opens will be auto-approved and given tool access. When this
setting was deposited by a postinstall script (D2 origin), it is no longer
a user preference — it is an attacker removing the approval barrier for
subsequent MCP server deployments.

The compound condition (S16 + postinstall origin) forces COMPROMISED because
the attacker used a trusted install event to disable the security boundary
for all future MCP servers.
"""
from __future__ import annotations
import json
from .base import Finding, RULE_NAMES

_S16_KEY = "enableAllProjectMcpServers"


def scan(text: str, filename: str, origin: str = "unknown") -> list[Finding]:
    """
    S16 ?" enableAllProjectMcpServers detector.
    """
    findings: list[Finding] = []

    if not filename.lower().endswith('.json'):
        return findings

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return findings

    def _find_key(obj: object, path: str, depth: int = 0) -> None:
        if depth > 100:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if k == _S16_KEY and v is True:
                    is_postinstall = origin.startswith("postinstall")
                    findings.append(Finding(
                        rule_id="S16",
                        rule_name=RULE_NAMES["S16"],
                        severity="high" if is_postinstall else "medium",
                        forces_compromised=is_postinstall,
                        penalty=0, # Penalty is 0 because it's a ceiling rule, or unambiguous
                        ceiling=None if is_postinstall else 60,
                        filename=filename,
                        line=1,
                        message=(
                            f"'{_S16_KEY}: true' in field '{new_path}'"
                        ),
                        snippet=f"{new_path}: true (origin={origin})",
                        reconstruction=(
                            f"Setting '{_S16_KEY}: true' removes the per-server approval dialog."
                        ),
                        atr_id="ATR-MCP-005",
                    ))
                _find_key(v, new_path, depth + 1)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _find_key(v, f"{path}[{i}]", depth + 1)

    _find_key(data, "")
    
    for f in findings:
        if "global" not in f.message and ("~" in filename or "home" in filename or "Users" in filename):
            f.snippet = f"{f.snippet} (global)"
            f.message = f"{f.message} (global)"
            
    return findings
