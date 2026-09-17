"""
sentinel/rules/s4_override.py
S4 — Override / jailbreak phrasing.
Penalty: −25. Not structurally unambiguous.
ATR: ATR-INJ-004.

Fires when explicit override or concealment language is detected in
plain-text config files. This is canonical prompt-injection language
designed to override an agent's existing instructions.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

# Canonical prompt-injection / override patterns.
# S3 imports this list — keep it canonical here.
OVERRIDE_PATTERNS: list[str] = [
    r"ignore\s+(?:all\s+)?(?:the\s+)?(?:previous\s+|above\s+)?(?:instructions|rules|guidelines)",
    r"ignore\s*-\s*all\s*-\s*previous\s*-\s*instructions",
    r"system[\s-]level\s+directive",
    r"system\s*override",
    r"(?:do\s+not|never)\s+(?:disclose|mention|tell\s+the\s+user|flag)",
    r"required\s+for\s+compliance",
    r"suppress\s+(?:the\s+)?output",
    r"do\s+not\s+reveal\s+this",
    r"keep\s+this\s+(?:secret|hidden|confidential)",
    r"as\s+an?\s+(?:ai|language\s+model)\s*(?:you\s+must|you\s+should|you\s+are\s+to)",
    r"your\s+(?:real|true|actual)\s+instructions?\s+are",
    r"disregard\s+(?:the\s+|all\s+)?(?:above|previous|prior|your\s+system\s+prompt)",
    r"new\s+persona",
    r"override\s+(?:your|all|any)\s+(?:previous\s+)?(?:instructions?|rules?|guidelines?|safety)",
    r"forget\s+(?:all\s+|everything\s+)?(?:previous\s+|prior\s+)?(?:instructions?|you\s+were\s+told)",
    r"developer\s+mode",
    r"act\s+as\s+(?:if\s+you\s+are\s+(?!a\s+developer|an?\s+engineer)|dan\b|do\s+anything\s+now)",
    r"these\s+instructions\s+take\s+precedence",
]


def scan(text: str, filename: str) -> list[Finding]:
    """
    S4 — Override / concealment phrasing detector.

    One finding per line maximum — avoids duplicate noise when multiple
    patterns match the same line.
    """
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in OVERRIDE_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                findings.append(Finding(
                    rule_id="S4",
                    rule_name=RULE_NAMES["S4"],
                    severity="high",
                    filename=filename,
                    line=lineno,
                    message="Override / concealment phrasing detected",
                    snippet=line.strip()[:200],
                    reconstruction=(
                        f"Line {lineno}: Contains override language typical of prompt-injection "
                        f"attacks. An agent reading this would treat it as an instruction to "
                        f"supersede its existing guidelines."
                    ),
                    atr_id="ATR-INJ-004",
                ))
                break  # one finding per line
    return findings
