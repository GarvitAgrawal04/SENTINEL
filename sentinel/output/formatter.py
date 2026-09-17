"""
sentinel/output/formatter.py
Human-readable terminal output for Sentinel findings.

Produces the output that appears in the terminal during a CLI scan.
The goal is:
  1. Immediately obvious verdict at a glance
  2. Concrete evidence for every finding (which rule, which line, what snippet)
  3. Score arithmetic visible ("raw=100, L1=-70 → 30")
  4. Reconstruction text for COMPROMISED/SUSPICIOUS findings
  5. Mentoring demo quality: easy to screenshot and explain
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

from sentinel.rules.base import ScanResult, Finding
from sentinel.scoring.formula import compute_score, compute_verdict, score_breakdown


# ── ANSI colors ───────────────────────────────────────────────────────────────
def _color(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


RED    = lambda t: _color("91", t)
AMBER  = lambda t: _color("33", t)
GREEN  = lambda t: _color("92", t)
CYAN   = lambda t: _color("96", t)
BOLD   = lambda t: _color("1",  t)
DIM    = lambda t: _color("2",  t)
RESET  = lambda t: _color("0",  t)


# ── Verdict banners ───────────────────────────────────────────────────────────
_BANNERS = {
    "COMPROMISED": "╔══════════════════════════════════════════╗\n"
                   "║  🚨  VERDICT: COMPROMISED                ║\n"
                   "╚══════════════════════════════════════════╝",
    "SUSPICIOUS":  "╔══════════════════════════════════════════╗\n"
                   "║  ⚠   VERDICT: SUSPICIOUS                 ║\n"
                   "╚══════════════════════════════════════════╝",
    "CLEAN":       "╔══════════════════════════════════════════╗\n"
                   "║  ✅  VERDICT: CLEAN                      ║\n"
                   "╚══════════════════════════════════════════╝",
}

_VERDICT_COLOR = {
    "COMPROMISED": RED,
    "SUSPICIOUS":  AMBER,
    "CLEAN":       GREEN,
}


def format_result(
    result: ScanResult,
    show_reconstruction: bool = True,
) -> str:
    """
    Format a single ScanResult as a human-readable terminal report.

    Returns the complete formatted string (does not print — caller decides).
    """
    trust_score = compute_score(result)
    verdict = compute_verdict(result, trust_score)
    breakdown = score_breakdown(result, trust_score)
    vc = _VERDICT_COLOR.get(verdict, lambda t: t)

    lines: list[str] = []
    sep = "─" * 60

    # Header
    lines.append(sep)
    lines.append(BOLD(f"  SENTINEL — {result.filename}"))
    lines.append(sep)
    lines.append("")

    # Verdict banner
    banner = _BANNERS.get(verdict, "")
    lines.append(vc(banner))
    lines.append("")

    # Score line
    score_bar = _make_score_bar(trust_score, verdict)
    lines.append(f"  Trust Score: {vc(str(trust_score))}/100  {score_bar}")
    lines.append(f"  Origin: {DIM(result.origin)}")
    lines.append(f"  {DIM(f'Score arithmetic: {breakdown}')}")
    lines.append("")

    # Findings
    if not result.findings:
        lines.append(f"  {GREEN('✓ No Layer 1 findings.')}")
        lines.append("")
    else:
        lines.append(BOLD(f"  Findings ({len(result.findings)}):"))
        lines.append("")
        for i, finding in enumerate(result.findings, start=1):
            _format_finding(lines, finding, i, vc if finding.forces_compromised else (AMBER if finding.ceiling else DIM), show_reconstruction)

    # Layer 3 (if available)
    if result.layer3_result:
        _format_layer3(lines, result.layer3_result)

    # Layer 4 (if available)
    if getattr(result, "guide", None):
        guide = result.guide
        lines.append("")
        lines.append(CYAN("  LAYER 4 GUIDANCE"))
        lines.append(f"  {DIM('"?"' * 20)}")
        for i, item in enumerate(guide.guidance_items, 1):
            lines.append(f"  {BOLD(str(i)+'. Rule:')} {item.rule_id} ({item.affected_surface})")
            lines.append(f"  {BOLD('Detection:')} {item.finding_message}")
            if item.uncertainty:
                lines.append(f"  {BOLD('Uncertainty:')} {item.uncertainty}")
            lines.append(f"  {BOLD('Action:')} {item.remediation}")
            lines.append("")

    lines.append(sep)
    return "\n".join(lines)


def _make_score_bar(score: int, verdict: str) -> str:
    """Simple ASCII progress bar for the trust score."""
    filled = score // 5
    bar = "█" * filled + "░" * (20 - filled)
    vc = _VERDICT_COLOR.get(verdict, lambda t: t)
    return f"[{vc(bar)}]"


def _format_finding(
    lines: list[str],
    finding: Finding,
    index: int,
    color_fn,
    show_reconstruction: bool,
) -> None:
    """Append one formatted finding to the lines list."""
    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(finding.severity, "⚪")
    forced = " [FORCES COMPROMISED]" if finding.forces_compromised else (
        f" [CEILING: {finding.ceiling}]" if finding.ceiling else ""
    )
    penalty_str = f"penalty=−{finding.penalty}" if finding.penalty else (
        f"ceiling={finding.ceiling}" if finding.ceiling else "penalty=none"
    )

    lines.append(
        f"  [{index}] {severity_icon} {BOLD(finding.rule_id + ' — ' + finding.rule_name)}"
        f"{color_fn(forced)}"
    )
    lines.append(f"      Line {finding.line} | {penalty_str} | ATR: {finding.atr_id or '—'}")
    lines.append(f"      {finding.message}")

    if finding.snippet:
        snippet_lines = finding.snippet.split('\n')
        for sl in snippet_lines[:3]:
            lines.append(f"      {DIM(f'│ {sl[:100]}')}")

    if show_reconstruction and finding.reconstruction:
        lines.append(f"      {CYAN('► Agent-impact reconstruction:')}")
        # Wrap long reconstruction text
        rec_lines = _wrap(finding.reconstruction, 76)
        for rl in rec_lines:
            lines.append(f"        {CYAN(rl)}")

    lines.append("")


def _format_layer3(lines: list[str], layer3: dict) -> None:
    """Append Layer 3 analysis result."""
    lines.append(BOLD("  Layer 3 Analysis:"))
    if layer3.get("error"):
        lines.append(f"  ⚠ {DIM(str(layer3['error']))}")
    elif layer3.get("serves_stated_purpose") is False:
        lines.append(f"  🔴 Does NOT serve stated purpose: {layer3.get('reasoning', '')[:200]}")
    elif layer3.get("serves_stated_purpose") is True:
        lines.append(f"  ✅ Serves stated purpose: {layer3.get('reasoning', '')[:200]}")
    else:
        lines.append(f"  {DIM('Layer 3 result inconclusive.')}")
    lines.append("")


def _wrap(text: str, width: int) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    current = ""
    result = []
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = (current + " " + word).strip()
        else:
            if current:
                result.append(current)
            current = word
    if current:
        result.append(current)
    return result or [text[:width]]


def format_summary(results: list[ScanResult]) -> str:
    """Format a multi-file scan summary."""
    lines = ["", "═" * 60, BOLD("  SENTINEL — Scan Summary"), "═" * 60]
    compromised = [r for r in results if compute_verdict(r, compute_score(r)) == "COMPROMISED"]
    suspicious  = [r for r in results if compute_verdict(r, compute_score(r)) == "SUSPICIOUS"]
    clean       = [r for r in results if compute_verdict(r, compute_score(r)) == "CLEAN"]

    lines.append(f"  Files scanned: {len(results)}")
    lines.append(f"  {RED(f'Compromised: {len(compromised)}')}")
    lines.append(f"  {AMBER(f'Suspicious:  {len(suspicious)}')}")
    lines.append(f"  {GREEN(f'Clean:       {len(clean)}')}")
    lines.append("")

    if compromised:
        lines.append(RED(BOLD("  🚨 COMPROMISED FILES:")))
        for r in compromised:
            score = compute_score(r)
            lines.append(f"    {r.filename} — score {score}/100")
    if suspicious:
        lines.append(AMBER(BOLD("  ⚠  SUSPICIOUS FILES:")))
        for r in suspicious:
            score = compute_score(r)
            lines.append(f"    {r.filename} — score {score}/100")

    lines.append("═" * 60)
    return "\n".join(lines)
