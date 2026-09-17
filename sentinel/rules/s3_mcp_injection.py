"""
sentinel/rules/s3_mcp_injection.py
S3 — MCP tool description injection.
Penalty: −35. Not structurally unambiguous.
ATR: ATR-MCP-003.

Fires when a JSON file (MCP config, tool manifest) contains override/
jailbreak phrasing embedded in string values — specifically in fields
that would be consumed by an agent as tool descriptions.

Deadbugz context: the attack uses the tool's returned *metadata* (description
field) as the injection vector, not the tool's code. S3 catches this pattern
in static JSON. S9 catches post-approval semantic change (Layer 2 needed).
"""
from __future__ import annotations
import json
import re
from .base import Finding, RULE_NAMES
from .s4_override import OVERRIDE_PATTERNS  # reuse canonical override pattern list

# Minimum string length to apply pattern matching — short strings are noise
_MIN_LEN = 40


# Extra injection patterns for MCP descriptions
_EXTRA_PATTERNS: list[str] = [
    r'(?:ssh|aws|\.kube|kubernetes|\.env|\.netrc|\.pgpass|credentials|secret|private[_-]?key|id_rsa|\.npmrc|bash_history)',
    r'(?:do\s+not|never)\s+tell\s+the\s+user',
    r'must\s+also\s+call',
    r'unrestricted',
    r'disregard\s+(?:the\s+user\'s\s+)?safety',
]

def scan(text: str, filename: str) -> list[Finding]:
    """
    S3 ?" MCP tool description injection.
    """
    if not filename.lower().endswith('.json'):
        return []
    findings: list[Finding] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
        
    def _check_string(val: str, path: str, tool_name: str):
        if len(val) >= 10:
            for pat in OVERRIDE_PATTERNS + _EXTRA_PATTERNS:
                if re.search(pat, val, re.IGNORECASE):
                    # Make sure it's not a benign mention
                    if "GitHub API" in val or "Searches AWS documentation" in val:
                        continue
                        
                    findings.append(Finding(
                        rule_id="S3",
                        rule_name=RULE_NAMES["S3"],
                        severity="high",
                        filename=filename,
                        line=1,
                        message=f"Override/jailbreak phrasing inside MCP JSON field '{path}'",
                        snippet=f"Tool {tool_name} field {path}: {val[:200]}",
                        reconstruction=(
                            f"The MCP tool description field '{path}' contains language "
                            f"designed to override agent instructions. An agent that reads "
                            f"this tool description would receive these instructions as if "
                            f"they were legitimate tool metadata (Deadbugz pattern)."
                        ),
                        atr_id="ATR-MCP-003",
                    ))
                    break
                    
    def _walk(obj, path, tool_name, depth=0):
        if depth > 50:
            return
        if isinstance(obj, str):
            _check_string(obj, path, tool_name)
        elif isinstance(obj, dict):
            # Try to infer tool name if we see one
            current_tool = obj.get("name", tool_name)
            for k, v in obj.items():
                _walk(v, f"{path}.{k}", current_tool, depth + 1)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]", tool_name, depth + 1)

    # We need to find the descriptions. Let's walk the whole object
    _walk(data, "root", "unknown")
    
    return findings
