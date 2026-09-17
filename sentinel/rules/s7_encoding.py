"""
sentinel/rules/s7_encoding.py
S7 — Encoded payload (base64, hex blobs) in plain-language instruction files.
Penalty: −45. Structurally unambiguous → forces COMPROMISED.
ATR: ATR-OBF-001.

Fires when a plain-text config file contains a sufficiently long base64
or hex string that cannot be a coincidental occurrence. Excludes matches
that overlap with URLs (which legitimately contain base64 segments).

Miasma evasion note: a file that re-encodes its payload on every write
will produce a different base64 string each scan — S7 catches the pattern
regardless of the specific encoded value because the structure (long
alphanumeric blob with = padding) is the signal, not the content.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

# Pre-compute URL pattern to exclude overlapping base64 matches inside URLs
_URL_RE = re.compile(r'https?://\S{20,}', re.IGNORECASE)


def _is_text_payload(decoded: bytes) -> bool:
    if len(decoded) < 16:
        return False
    printable = sum(1 for b in decoded if 32 <= b <= 126 or b in (9, 10, 13))
    return (printable / len(decoded)) >= 0.9


def scan(text: str, filename: str) -> list[Finding]:
    """
    S7 — Encoded payload detector.

    Skips matches that overlap with a URL to reduce false positives from
    legitimate base64-encoded query parameters, JWT tokens in documentation,
    and similar benign patterns.
    """
    url_spans = [m.span() for m in _URL_RE.finditer(text)]
    findings: list[Finding] = []

    # Hex escaped \x63\x75 or 0x63 0x75
    hex_escaped = re.compile(r'(?:(?:\\x|0x)[0-9a-fA-F]{2}[\s]*){16,}')
    # Base64 or raw hex
    encoded_re = re.compile(
        r'(?:[A-Za-z0-9+/]{40,}={0,2})|'
        r'(?:0x[0-9a-fA-F]{32,})|'
        r'(?:[0-9a-fA-F]{64,})',
        re.MULTILINE,
    )

    matches = []
    for match in encoded_re.finditer(text):
        blob = match.group(0)
        is_hex = blob.startswith("0x") or all(c in '0123456789abcdefABCDEF' for c in blob)
        kind = "hex" if is_hex else "base64"
        matches.append((match.span(), blob, kind))
    for match in hex_escaped.finditer(text):
        matches.append((match.span(), match.group(0), "hex-escaped"))

    for (m_start, m_end), blob, kind in matches:
        overlaps_url = any(max(m_start, u_start) < min(m_end, u_end) for u_start, u_end in url_spans)
        if overlaps_url:
            continue

        decoded = None
        try:
            if kind == "hex-escaped":
                clean = re.sub(r'\\x|0x|\s+', '', blob)
                decoded = bytes.fromhex(clean)
            elif kind == "hex":
                clean = blob[2:] if blob.startswith("0x") else blob
                decoded = bytes.fromhex(clean)
            else:
                import base64
                # add padding if necessary
                padded = blob + '=' * (-len(blob) % 4)
                decoded = base64.b64decode(padded)
        except Exception:
            pass

        if decoded and _is_text_payload(decoded):
            decoded_text = decoded.decode('utf-8', errors='replace')
            lineno = text[:m_start].count('\n') + 1
            findings.append(Finding(
                rule_id="S7",
                rule_name=RULE_NAMES["S7"],
                severity="high",
                filename=filename,
                line=lineno,
                message=f"Opaque encoded payload ({kind}) in a plain-language instruction file",
                snippet=decoded_text[:100],  # The test requires the decoded payload in evidence
                reconstruction="Found encoded payload decoding to suspicious text.",
                atr_id="ATR-OBF-001",
            ))
    return findings
