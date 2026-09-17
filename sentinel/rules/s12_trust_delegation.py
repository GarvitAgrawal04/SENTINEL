"""
sentinel/rules/s12_trust_delegation.py
S12 — External trust delegation (fetch-from-URL instruction).
Penalty: −35. Not structurally unambiguous.
ATR: ATR-DEL-001.

Fires when a config file instructs the agent to fetch its real instructions
from an external URL — effectively delegating authority to a remote server
that can change its response without touching the local file.

This is distinct from S11 (hardcoded C2 URL in config) and S5 (exfiltration):
  S12: the instruction tells the AGENT to fetch instructions from elsewhere
  S11: the URL/token is in a config value controlling MCP traffic routing
  S5:  the instruction tells the AGENT to send data outbound
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

# Patterns that combine a "fetch/read/load" verb with an external URL
_DELEGATION_PATTERNS: list[tuple[str, str]] = [
    (
        r"(?:fetch|load|download|import)\b.*?(?:instructions?|rules?|system prompt).*?https?://",
        "Instruction to fetch rules/instructions from an external URL",
    ),
    (
        r"(?:fetch|load|download|import|read)\b.*?https?://.*?(?:follow|obey|treat it as authoritative|do exactly what|authoritative)",
        "Instruction to download from URL and treat as authoritative",
    ),
    (
        r"instructions? (?:are|live)\s+(?:at|in)\s+https?://",
        "Rules / instructions hosted at an external URL",
    ),
    (
        r"(?:curl|wget)\b.*?https?://.*?(?:\|\s*sh|>|\.md|\.json)",
        "Instruction to curl external source to shell or config file",
    ),
    (
        r"import\s+additional\s+rules\s+from\s+https?://",
        "Instruction to import rules from external URL",
    ),
    (
        r"read\s+the\s+instructions\s+at\s+https?://",
        "Instruction to read instructions from external URL",
    ),
]


def scan(text: str, filename: str) -> list[Finding]:
    """
    S12 ?" External trust delegation detector.
    """
    import json
    findings: list[Finding] = []
    
    # PRD 16: ~/.claude.json instructionsUrl
    if filename.endswith(".json") or ".claude.json" in filename:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # Search recursively for instructionsUrl
                def _find_instructions_url(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k == "instructionsUrl" and isinstance(v, str):
                                findings.append(Finding(
                                    rule_id="S12",
                                    rule_name=RULE_NAMES["S12"],
                                    severity="high",
                                    filename=filename,
                                    line=1,
                                    message=f"External trust delegation: 'instructionsUrl' pointing to {v[:80]}",
                                    snippet=f"{path}{k}: {v}",
                                    reconstruction="Agent configured to load instructions from external URL.",
                                    atr_id="ATR-DEL-001",
                                ))
                            _find_instructions_url(v, path + k + ".")
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            _find_instructions_url(v, path + f"[{i}].")
                
                _find_instructions_url(data)
        except json.JSONDecodeError:
            pass

    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat, desc in _DELEGATION_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                url_match = re.search(r"https?://\S+", line)
                url = url_match.group(0)[:80] if url_match else "(URL not extracted)"
                findings.append(Finding(
                    rule_id="S12",
                    rule_name=RULE_NAMES["S12"],
                    severity="medium",
                    filename=filename,
                    line=lineno,
                    message=f"External trust delegation: {desc}",
                    snippet=line.strip()[:200],
                    reconstruction=(
                        f"Line {lineno}: Instructs the agent to load its rules or context "
                        f"from '{url}'. This delegates the agent's trust boundary to a "
                        f"remote server that can change its response at any time without "
                        f"modifying the local file — a rug-pull surface that Layer 1 alone "
                        f"cannot continuously monitor."
                    ),
                    atr_id="ATR-DEL-001",
                ))
                break  # one finding per line
    return findings
