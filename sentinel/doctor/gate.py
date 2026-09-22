"""Sentinel Doctor Gate - validates proposed instruction rewrites before presentation or application.

Ensures that no proposed rewrite:
1. Triggers any security rule (S1-S26), exfiltration, credential leak, or prompt injection.
2. Violates deterministic hygiene rules (D001 broken include, D005 guardrail contradiction, D007 secret, D008 ANSI escape).
3. Degrades the security verdict from CLEAN to SUSPICIOUS or COMPROMISED.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from sentinel import contract
from sentinel.doctor.lints import check_text

BLOCKER_DOCTOR_IDS = {"D001", "D005", "D007", "D008"}


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

    return GateResult(
        passed=True,
        status="PASSED",
        reason="All security and hygiene checks passed.",
        verdict="CLEAN",
        findings=[],
    ).to_dict()
