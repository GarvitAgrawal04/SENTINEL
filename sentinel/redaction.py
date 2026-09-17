import re

_SECRET_RE = re.compile(
    r'(sk-[a-zA-Z0-9_-]{10,}|Bearer\s+[a-zA-Z0-9_\-\.]{10,}|ghp_[a-zA-Z0-9]{36})',
    re.IGNORECASE
)

def redact_string(text: str) -> str:
    if not isinstance(text, str):
        return text
    return _SECRET_RE.sub("[REDACTED SECRET]", text)

def redact_findings(findings: list) -> None:
    for f in findings:
        f.message = redact_string(f.message)
        f.snippet = redact_string(f.snippet)
        f.reconstruction = redact_string(f.reconstruction)
        
def redact_scan_result(result) -> None:
    redact_findings(result.findings)
    if hasattr(result, "guide") and result.guide:
        for g in result.guide.guidance_items:
            g.finding_message = redact_string(g.finding_message)
            g.evidence_snippet = redact_string(g.evidence_snippet)
            g.remediation = redact_string(g.remediation)
