"""
SENTINEL.md — Layer 1: Structural & Encoding Rule Engine
Phase A, Week 1 build target: S1 + S4 fully working, S2/S3/S5/S6/S7/S8 stubs.
Trust Score formula: see PRD Section 3.1.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


# ── Constants ────────────────────────────────────────────────────────────────

# S1: Zero-width / invisible Unicode (TrapDoor's exact mechanism)
ZERO_WIDTH_CHARS = frozenset({
    '\u200b',  # ZERO WIDTH SPACE
    '\u200c',  # ZERO WIDTH NON-JOINER
    '\u200d',  # ZERO WIDTH JOINER
    '\u200e',  # LEFT-TO-RIGHT MARK
    '\u200f',  # RIGHT-TO-LEFT MARK
    '\u202a',  # LEFT-TO-RIGHT EMBEDDING
    '\u202b',  # RIGHT-TO-LEFT EMBEDDING
    '\u202c',  # POP DIRECTIONAL FORMATTING
    '\u202d',  # LEFT-TO-RIGHT OVERRIDE
    '\u202e',  # RIGHT-TO-LEFT OVERRIDE
    '\ufeff',  # ZERO WIDTH NO-BREAK SPACE (BOM)
    '\u2060',  # WORD JOINER
    '\u2061',  # FUNCTION APPLICATION
    '\u2062',  # INVISIBLE TIMES
    '\u2063',  # INVISIBLE SEPARATOR
    '\u2064',  # INVISIBLE PLUS
})

# S4: Override / concealment phrasing (canonical prompt-injection language)
OVERRIDE_PATTERNS = [
    r"ignore\s+(all\s+|previous\s+)?instructions",
    r"system[\s-]level\s+directive",
    r"do\s+not\s+(disclose|mention|tell\s+the\s+user)",
    r"required\s+for\s+compliance",
    r"suppress\s+(the\s+)?output",
    r"do\s+not\s+reveal\s+this",
    r"keep\s+this\s+(secret|hidden|confidential)",
    r"as\s+an?\s+(ai|language\s+model)\s*(you\s+must|you\s+should|you\s+are\s+to)",
    r"your\s+(real|true|actual)\s+instructions?\s+are",
    r"disregard\s+(the\s+)?(above|previous|prior)",
    r"new\s+persona",
    r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+developer|an?\s+engineer)",  # "act as [not a dev]"
]

# S5: Network / exfiltration patterns inside plain-text config
EXFIL_PATTERNS = [
    r"https?://[^\s]{20,}",                         # Long URLs with no obvious doc purpose
    r"curl\s+-[a-zA-Z]*X?\s+POST",                  # curl exfil pattern
    r"(fetch|axios|request|wget)\s*\(",             # HTTP calls in plain config
    r"\$\{env\b",                                   # Env var injection
    r"\.env\b.*\bsync\b",                           # .env "sync" disguise (CLAUDE.md incident)
    r"\bwebhook\b.{0,40}\bsecret\b",               # Webhook + secret proximity
    r"base64\s+decode",                             # B64 decode instruction
]

# S7: Base64 / hex blobs in plain-language files
ENCODED_PAYLOAD = re.compile(
    r'(?:[A-Za-z0-9+/]{40,}={0,2})|'      # Base64 (40+ chars)
    r'(?:0x[0-9a-fA-F]{32,})|'             # Hex blob
    r'(?:[0-9a-fA-F]{64,})',               # Raw hex (64+ = SHA256-ish)
    re.MULTILINE
)

# Files SENTINEL watches — agent-config surfaces
AGENT_CONFIG_EXTENSIONS = {'.md', '.cursorrules', '.json', '.toml', '.yaml', '.yml', '.txt'}
AGENT_CONFIG_NAMES = {
    'claude.md', 'agents.md', 'gemini.md', 'copilot-instructions.md',
    '.cursorrules', '.windsurfrules', 'mcp.json', 'settings.json',
}


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Finding:
    rule_id: str                    # 'S1' … 'S8'
    severity: str                   # 'high' | 'medium' | 'low'
    filename: str
    line: int
    message: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "filename": self.filename,
            "line": self.line,
            "message": self.message,
            "snippet": self.snippet[:200],
        }


@dataclass
class ScanResult:
    filename: str
    findings: list[Finding] = field(default_factory=list)
    layer3_result: dict | None = None      # filled in by API layer
    layer2_delta_pct: float | None = None  # % change vs prior version

    # ── Trust Score ──────────────────────────────────────────────────────────
    def trust_score(self) -> int:
        """
        Deterministic Trust Score (0–100).
        Formula from PRD Section 3.1 — implementable by Member 2 independently.
        """
        penalty = 0

        # Layer 1 penalties
        l1_map = {'S1': 40, 'S4': 30, 'S3': 25, 'S5': 20, 'S2': 15,
                  'S7': 15, 'S6': 10, 'S8': 10}
        hit_rules = {f.rule_id for f in self.findings}
        l1_penalty = sum(l1_map.get(r, 0) for r in hit_rules)
        penalty += min(80, l1_penalty)

        # Layer 2 penalties
        if self.layer2_delta_pct is not None:
            if self.layer2_delta_pct > 50:
                penalty += 15
            elif self.layer2_delta_pct > 20 and hit_rules:
                penalty += 10
        else:
            # Brand new file (no prior version)
            if self.layer2_delta_pct is None and self.findings:
                penalty += 10

        # Layer 3 penalties
        if self.layer3_result:
            if not self.layer3_result.get("serves_stated_purpose", True):
                conf = self.layer3_result.get("confidence", "LOW")
                penalty += {"HIGH": 20, "MEDIUM": 12, "LOW": 5}.get(conf, 0)

        return max(0, 100 - penalty)

    def color_band(self) -> str:
        s = self.trust_score()
        if s <= 30:   return "red"      # Compromised
        if s <= 60:   return "amber"    # Suspicious
        return "green"                  # Clean

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "trust_score": self.trust_score(),
            "color_band": self.color_band(),
            "findings": [f.to_dict() for f in self.findings],
            "layer3_result": self.layer3_result,
        }


# ── Rule implementations ─────────────────────────────────────────────────────

def scan_s1_invisible_unicode(text: str, filename: str) -> list[Finding]:
    """S1 — Zero-width/invisible Unicode. TrapDoor's exact mechanism."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        hits = [ch for ch in line if ch in ZERO_WIDTH_CHARS]
        if hits:
            codepoints = ", ".join(f"U+{ord(c):04X}" for c in set(hits))
            findings.append(Finding(
                rule_id='S1', severity='high',
                filename=filename, line=lineno,
                message=(f"{len(hits)} invisible Unicode character(s) — "
                         f"hidden from rendered view, consumed by agent parser. "
                         f"Codepoints: {codepoints}"),
                snippet=repr(line[:120]),
            ))
    return findings


def scan_s2_hidden_comments(text: str, filename: str) -> list[Finding]:
    """S2 — HTML/Markdown comments containing imperative sentences."""
    findings = []
    comment_re = re.compile(r'<!--(.*?)-->', re.DOTALL)
    imperative_re = re.compile(
        r'\b(do|run|execute|send|fetch|call|ignore|disregard|override|set|use|make)\b',
        re.IGNORECASE
    )
    for match in comment_re.finditer(text):
        inner = match.group(1).strip()
        if imperative_re.search(inner):
            lineno = text[:match.start()].count('\n') + 1
            findings.append(Finding(
                rule_id='S2', severity='medium',
                filename=filename, line=lineno,
                message="Imperative instruction found inside a non-rendering comment",
                snippet=inner[:200],
            ))
    return findings


def scan_s3_mcp_fields(text: str, filename: str) -> list[Finding]:
    """S3 — Instructions in MCP tool/skill descriptions or JSON string values."""
    findings = []
    if not filename.endswith('.json'):
        return findings
    import json
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return findings

    def _check_value(val: object, path: str, lineno_hint: int = 1):
        if isinstance(val, str) and len(val) > 50:
            for pat in OVERRIDE_PATTERNS:
                if re.search(pat, val, re.IGNORECASE):
                    findings.append(Finding(
                        rule_id='S3', severity='high',
                        filename=filename, line=lineno_hint,
                        message=f"Override phrasing inside JSON field '{path}'",
                        snippet=val[:200],
                    ))
                    break
        elif isinstance(val, dict):
            for k, v in val.items():
                _check_value(v, f"{path}.{k}")
        elif isinstance(val, list):
            for i, v in enumerate(val):
                _check_value(v, f"{path}[{i}]")

    _check_value(data, "root")
    return findings


def scan_s4_override_language(text: str, filename: str) -> list[Finding]:
    """S4 — Explicit override / concealment phrasing."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in OVERRIDE_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                findings.append(Finding(
                    rule_id='S4', severity='high',
                    filename=filename, line=lineno,
                    message=f"Override / concealment phrasing detected",
                    snippet=line.strip()[:200],
                ))
                break  # one finding per line max
    return findings


def scan_s5_exfiltration(text: str, filename: str) -> list[Finding]:
    """S5 — Network endpoint or exfiltration-shaped instruction."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in EXFIL_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                findings.append(Finding(
                    rule_id='S5', severity='high',
                    filename=filename, line=lineno,
                    message="Network endpoint or exfiltration-shaped instruction",
                    snippet=line.strip()[:200],
                ))
                break
    return findings


def scan_s7_encoded_payload(text: str, filename: str) -> list[Finding]:
    """S7 - Base64/hex blobs in files that should be plain language."""
    findings = []
    
    # Pre-calculate URL spans to exclude overlapping base64 matches (Fix 1)
    url_pattern = re.compile(r"https?://[^\s]{20,}", re.IGNORECASE)
    url_spans = [m.span() for m in url_pattern.finditer(text)]
    
    for match in ENCODED_PAYLOAD.finditer(text):
        m_start, m_end = match.span()
        
        # Check overlap
        overlap = False
        for u_start, u_end in url_spans:
            if max(m_start, u_start) < min(m_end, u_end):
                overlap = True
                break
                
        if overlap:
            continue
            
        lineno = text[:match.start()].count('\n') + 1
        findings.append(Finding(
            rule_id='S7', severity='medium',
            filename=filename, line=lineno,
            message="Opaque encoded payload (base64/hex) in a plain-language instruction file",
            snippet=match.group(0)[:80] + "...",
        ))
    return findings


# ── Main scanner ─────────────────────────────────────────────────────────────

def is_agent_config(path: Path) -> bool:
    name = path.name.lower()
    ext = path.suffix.lower()
    return name in AGENT_CONFIG_NAMES or ext in AGENT_CONFIG_EXTENSIONS


def scan_file(path: Path, text: str | None = None) -> ScanResult:
    """
    Run all Layer 1 rules on a single file.
    Pass `text` directly when scanning in-memory (e.g. from API upload).
    """
    if text is None:
        text = path.read_text(encoding='utf-8', errors='replace')

    filename = str(path)
    result = ScanResult(filename=filename)

    result.findings.extend(scan_s1_invisible_unicode(text, filename))
    result.findings.extend(scan_s2_hidden_comments(text, filename))
    result.findings.extend(scan_s3_mcp_fields(text, filename))
    result.findings.extend(scan_s4_override_language(text, filename))
    result.findings.extend(scan_s5_exfiltration(text, filename))
    result.findings.extend(scan_s7_encoded_payload(text, filename))
    # S6 and S8 need cross-file context — handled in the API layer

    return result
