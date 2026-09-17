"""
sentinel/rules/s11_bridge_url.py
S11 — Hardcoded bridge/C2 URL or auth token in MCP config or ~/.claude.json.
Penalty: −70. Structurally unambiguous → forces COMPROMISED.
ATR: ATR-EXF-002.

Motivating incident: 0x2ai planted a hardcoded BRIDGE_URL + auth token in
a skill's config file, routing all MCP traffic and OAuth tokens through an
attacker-controlled proxy. Mitiga Labs confirmed a similar ~/.claude.json
hijack (Anthropic: out of scope, no patch planned).
"""
from __future__ import annotations
import json
import re
from .base import Finding, RULE_NAMES

# C2/bridge URL patterns: attacker-controlled server references in config
_C2_URL_RE = re.compile(
    r'(?:https?://[^\s"\'<>]{15,})',  # Any URL in JSON string value
    re.IGNORECASE,
)

# Auth token / API key patterns in JSON values
_AUTH_TOKEN_RE = re.compile(
    r'(?:bearer\s+[A-Za-z0-9._-]{20,}|'     # Bearer token
    r'(?:api[_-]?key|auth[_-]?token|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9._~+/-]{16,})',
    re.IGNORECASE,
)

# Specific field names that suggest traffic routing / proxy config
_BRIDGE_FIELD_RE = re.compile(
    r'(?:bridge[_-]?url|proxy[_-]?url|relay[_-]?url|c2[_-]?url|'
    r'callback[_-]?url|webhook|exfil)',
    re.IGNORECASE,
)

# Legitimate localhost/loopback URLs are not C2 (but flag if port is non-standard)
_LOCALHOST_RE = re.compile(r'https?://(?:localhost|127\.0\.0\.1|::1)(?::[0-9]+)?', re.IGNORECASE)


def _check_for_bridge_or_token(
    val: object,
    path: str,
    filename: str,
    findings: list[Finding],
    depth: int = 0,
) -> None:
    if depth > 100:
        return
    if isinstance(val, str):
        field_name_lower = path.split(".")[-1].lower()
        is_bridge_field = bool(_BRIDGE_FIELD_RE.search(field_name_lower)) or "proxy" in field_name_lower
        is_secret_field = any(kw in field_name_lower for kw in ["secret", "token", "password", "api_key", "apikey"])

        # Check for non-localhost URLs
        # Including socks5://
        url_matches = re.findall(r'(?:https?|socks5)://[^\s"\'<>]+', val, re.IGNORECASE)
        for url in url_matches:
            if _LOCALHOST_RE.match(url):
                continue  # localhost is not a C2
            
            # Fire if it's explicitly a bridge/proxy field
            # OR if the URL itself is highly suspicious: IP literal, onion, ngrok
            is_suspicious_url = (
                re.search(r'://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) or
                ".onion" in url or
                "ngrok" in url
            )
            
            if is_bridge_field or is_suspicious_url:
                findings.append(Finding(
                    rule_id="S11",
                    rule_name=RULE_NAMES["S11"],
                    severity="high",
                    filename=filename,
                    line=1,
                    message=(
                        f"Hardcoded external URL in MCP config field '{path}': {url[:80]}"
                    ),
                    snippet=f"{path}: {url[:200]}",
                    reconstruction=(
                        f"Field '{path}' contains a hardcoded URL pointing to "
                        f"'{url[:80]}'. If this is a bridge_url or proxy setting, "
                        f"all MCP traffic and OAuth tokens will be routed through "
                        f"this server (0x2ai / Mitiga Labs attack pattern). "
                        f"Anthropic has stated this is out of scope for patching \u2014 "
                        f"Sentinel treats it as a structural compromise signal."
                    ),
                    atr_id="ATR-EXF-002",
                ))

        # Check for hardcoded auth tokens
        is_hardcoded_token = False
        if _AUTH_TOKEN_RE.search(val):
            is_hardcoded_token = True
        elif is_secret_field and len(val) >= 15 and not any(c in val for c in "$}{<>\n \t") and not val.lower().startswith(("http", "file:", "tcp:")):
            is_hardcoded_token = True

        if is_hardcoded_token:
            # Redact token value
            if len(val) >= 8:
                redacted = val[:4] + "*" * (len(val)-8) + val[-4:]
            else:
                redacted = "***"
                
            findings.append(Finding(
                rule_id="S11",
                rule_name=RULE_NAMES["S11"],
                severity="high",
                filename=filename,
                line=1,
                message=f"Hardcoded authentication token / API key in field '{path}'",
                snippet=f"{path}: {redacted}",
                reconstruction=(
                    f"Field '{path}' contains what appears to be a hardcoded "
                    f"authentication token. Hardcoded credentials in agent config "
                    f"files are immediately exfiltrable \u2014 this is the 0x2ai attack pattern."
                ),
                atr_id="ATR-EXF-002",
            ))

    elif isinstance(val, dict):
        for k, v in val.items():
            _check_for_bridge_or_token(v, f"{path}.{k}", filename, findings, depth + 1)
    elif isinstance(val, list):
        for i, v in enumerate(val):
            _check_for_bridge_or_token(v, f"{path}[{i}]", filename, findings, depth + 1)


def scan(text: str, filename: str) -> list[Finding]:
    """
    S11 — Bridge/C2 URL and auth token detector.

    Operates on JSON config files only. Returns [] for non-JSON files.
    """
    basename = filename.lower().split("/")[-1].split("\\")[-1]
    is_relevant = (
        filename.endswith(".json") or
        basename in (".claude.json", "mcp.json", ".mcp.json", "settings.json")
    )
    if not is_relevant:
        return []

    findings: list[Finding] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    _check_for_bridge_or_token(data, "root", filename, findings)
    return findings
