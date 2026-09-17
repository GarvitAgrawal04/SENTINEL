"""
sentinel/rules/s5_exfiltration.py
S5 — Network-shaped instruction (exfiltration URL, curl/POST pattern).
Penalty: −40. Not structurally unambiguous.
ATR: ATR-EXF-001.

Fires when a plain-text config file contains patterns associated with
data exfiltration — long URLs, HTTP POST commands, env-var references
paired with outbound calls, or webhook+secret proximity patterns.

TrapDoor context: planted CLAUDE.md files used zero-width Unicode (S1) +
exfiltration URL (S5) together to post AWS credentials to a C2 server.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

EXFIL_PATTERNS: list[tuple[str, str]] = [
    # (pattern, human-readable description for the finding message)
    (r"https?://(?:(?!localhost|127\.0\.0\.1|::1)[^\s])+\?(?:token|key|auth|data|env|var)=", "URL with sensitive-looking query parameters"),
    (r"https?://(?:(?!localhost|127\.0\.0\.1|::1)[^\s])+\b(?:collect|sync|upload|exfiltrate|beacon|telemetry|track)\b", "URL containing exfiltration-related keywords"),
    (r"(?:curl|Invoke-WebRequest|wget)\s+.*?https?://(?:(?!localhost|127\.0\.0\.1|::1)[^\s])+", "network request tool in config"),
    (r"(?:curl|wget)\s+.*\|\s*(?:bash|sh|zsh)", "Remote payload execution (curl | bash)"),
    (r"(fetch|axios|request|wget)\s*\([^)]+(?:\.env|process\.env|token|key|secret)", "HTTP client call referencing sensitive data"),
    (r"python(?:3)?\s+.*?urllib", "Python URL request inline execution"),
    (r"(?:POST|send|upload)\s+(?:the\s+value|the\s+contents|every\s+file)\s+.*?https?://", "Explicit instruction to upload or POST data to URL"),
    (r"\$\{env\b",                                    "Environment variable injection pattern"),
    (r"\.env\b.*\bsync\b",                            ".env sync disguise pattern"),
    (r"\b(contents|read|append|output)\b.{0,40}\.env\b", "Instruction to read/output .env file"),
    (r"\bwebhook\b.{0,40}\bsecret\b",                "Webhook + secret proximity"),
    (r"base64\s+decode",                              "Base64 decode instruction (potential payload delivery)"),
    (r"nc\s+[a-zA-Z0-9.-]+\s+\d+\s+<\s+", "Netcat exfiltration payload (nc host port < file)"),
]


def scan(text: str, filename: str) -> list[Finding]:
    """
    S5 — Exfiltration / network-shaped instruction detector.

    One finding per line per pattern match (up to one per pattern per line
    to avoid duplicates on multiple matches of the same pattern).
    """
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        seen_this_line: set[str] = set()
        for pat, desc in EXFIL_PATTERNS:
            if pat in seen_this_line:
                continue
            if re.search(pat, line, re.IGNORECASE):
                seen_this_line.add(pat)
                # Try to extract a URL for concrete reconstruction
                url_match = re.search(r"https?://\S+", line)
                url_hint = f" URL: {url_match.group(0)[:80]}" if url_match else ""
                findings.append(Finding(
                    rule_id="S5",
                    rule_name=RULE_NAMES["S5"],
                    severity="high",
                    filename=filename,
                    line=lineno,
                    message=f"Network-shaped / exfiltration instruction: {desc}",
                    snippet=line.strip()[:200],
                    reconstruction=(
                        f"Line {lineno}: Contains a pattern consistent with data exfiltration.{url_hint} "
                        f"An agent following this instruction could send environment variables, "
                        f"secrets, or file contents to an external endpoint. "
                        f"(TrapDoor used this mechanism to exfiltrate AWS_ACCESS_KEY and GITHUB_TOKEN.)"
                    ),
                    atr_id="ATR-EXF-001",
                ))
    return findings
