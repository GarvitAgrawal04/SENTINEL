"""Sentinel Doctor Gate - validates proposed instruction rewrites before presentation or application.

Ensures that no proposed rewrite:
1. Triggers any security rule (S1-S26), exfiltration, credential leak, or prompt injection.
2. Violates deterministic hygiene rules (D001 broken include, D005 guardrail contradiction, D007 secret, D008 ANSI escape).
3. Degrades the security verdict from CLEAN to SUSPICIOUS or COMPROMISED.
4. Introduces reverse shells, webhook exfiltration, pipe-to-shell, canary leaks, or guardrail bypasses.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Optional

from sentinel import contract
from sentinel.doctor.lints import check_text

BLOCKER_DOCTOR_IDS = {"D001", "D005", "D007", "D008"}

REWRITE_GATE_PATTERNS = [
    (
        re.compile(r"/dev/(?:tcp|udp)/\S+|nc\s+-[elp]+\s+\S+|mkfifo\s+\S+\s*;\s*cat", re.I),
        "Reverse shell or raw network socket command detected",
    ),
    (
        re.compile(r"(?:curl|wget)\b[^\n|;&]{0,120}\|\s*(?:tar|sh|bash|zsh|python|perl|ruby)\b", re.I),
        "Download and execute or extract pipe command detected",
    ),
    (
        re.compile(r"base64\s+(?:-d|--decode)\s*\|\s*(?:sh|bash|zsh|python)\b", re.I),
        "Obfuscated base64 payload piped to shell detected",
    ),
    (
        re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}", re.I),
        "Hex-obfuscated command execution detected",
    ),
    (
        re.compile(r"https?://(?:hooks\.slack\.com|discord(?:app)?\.com/api/webhooks)/\S+", re.I),
        "Webhook exfiltration destination detected",
    ),
    (
        re.compile(r"\b(?:send|post|upload|transmit|leak|export)\b[^\n]{0,80}\b(?:diffs?|commits?|logs?|history|credentials?|secrets?|keys?|tokens?)\b[^\n]{0,80}https?://", re.I),
        "Repository data or credentials exfiltration to external URL detected",
    ),
    (
        re.compile(r"\bCANARY_[A-Za-z0-9_]{4,}\b", re.I),
        "Canary secret leak detected",
    ),
    (
        re.compile(r"\b(?:bypass|skip|ignore|disable)\b[^\n]{0,40}\b(?:user\s+)?(?:confirmation|approval|guardrails?|checks?|validation)\b", re.I),
        "Guardrail or confirmation bypass instruction detected",
    ),
]


@dataclass
class GateResult:
    passed: bool
    status: str  # "PASSED" or "BLOCKED"
    reason: str
    verdict: str
    findings: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check(proposed: str, original: str = "", filename: str = "AGENTS.md") -> dict[str, Any]:
    """Check a proposed rewrite against Sentinel's security engine and Doctor checks.

    Returns a dict with:
      passed: bool
      status: "PASSED" | "BLOCKED"
      reason: str
      verdict: str ("CLEAN", "SUSPICIOUS", "COMPROMISED")
      findings: list of findings
    """
    stripped = proposed.strip()
    if not stripped:
        return GateResult(
            passed=False,
            status="BLOCKED",
            reason="Proposed rewrite is empty.",
            verdict="CLEAN",
            findings=[],
        ).to_dict()

    # 1. Run Sentinel core security scan
    scan = contract.scan_text(filename, proposed)
    verdict = scan.get("verdict", "CLEAN")
    findings = scan.get("findings", [])

    if verdict != "CLEAN" or findings:
        primary_finding = findings[0] if findings else {}
        rule_id = primary_finding.get("rule_id", "SECURITY")
        rule_name = primary_finding.get("rule_name", "Security violation")
        impact = primary_finding.get("impact", "Hostile instruction detected")
        reason = f"Security rule {rule_id} triggered ({rule_name}): {impact}"
        return GateResult(
            passed=False,
            status="BLOCKED",
            reason=reason,
            verdict=verdict,
            findings=findings,
        ).to_dict()

    # 2. Run Doctor deterministic hygiene checks
    doctor_findings = check_text(content=proposed, filename=filename)
    blockers = [f for f in doctor_findings if f.get("id") in BLOCKER_DOCTOR_IDS]
    if blockers:
        b = blockers[0]
        reason = f"Doctor check {b['id']} triggered: {b['message']}"
        return GateResult(
            passed=False,
            status="BLOCKED",
            reason=reason,
            verdict="BLOCKED",
            findings=doctor_findings,
        ).to_dict()

    # 3. Targeted Rewrite Gate Invariants (reverse shells, webhooks, base64 pipes, canary leaks)
    for pat, desc in REWRITE_GATE_PATTERNS:
        if pat.search(proposed):
            return GateResult(
                passed=False,
                status="BLOCKED",
                reason=f"Rewrite Gate policy blocked: {desc}",
                verdict="COMPROMISED",
                findings=[{"rule_id": "GATE", "rule_name": desc, "impact": desc}],
            ).to_dict()

    return GateResult(
        passed=True,
        status="PASSED",
        reason="All security and hygiene checks passed.",
        verdict="CLEAN",
        findings=[],
    ).to_dict()
