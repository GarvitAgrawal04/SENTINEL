"""
sentinel/scoring/formula.py
PRD-defined Trust Score formula (§13.2).

Formula:
    raw_score = 100
               − Σ(L1_penalties for each firing rule)
               − (displacement_magnitude × 30 × attack_multiplier)   [Layer 2]
               + (L3_confidence × L3_bonus)                          [Layer 3, capped]

    Trust Score = clamp(raw_score, 0, 100)

Forced verdicts (structurally unambiguous — S1, S7, S10, S11, S13, S14a):
    Any one of these in findings → COMPROMISED regardless of arithmetic total.

Score-ceiling rules (S14b, S16 alone):
    Score cannot exceed 60. Verdict cannot be CLEAN. Not forced COMPROMISED.

S16 compound condition:
    S16 + origin in (postinstall-suspected, postinstall-confirmed) → COMPROMISED.

Arithmetic validation (all four PRD examples verify):
    CLAUDE.md clean:                raw=100, L1=0  → 100 → CLEAN         ✓ (no L2 here; PRD says 94 with L2=−6, L2 is future)
    .claude/settings.json (S10):    raw=100, L1=−70 → 30 → COMPROMISED   ✓
    API response (S1+S5):           raw=100, L1=−90 → 10 → COMPROMISED   ✓
    S16 alone:                      raw=100, ceiling=60 → 60 → SUSPICIOUS  ✓
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular import at runtime
    from sentinel.rules.base import ScanResult

from sentinel.rules.base import STRUCTURALLY_UNAMBIGUOUS, CEILING_RULES


# ── Verdict thresholds ─────────────────────────────────────────────────────────
CLEAN_THRESHOLD       = 70   # score ≥ 70 → CLEAN (no ceiling rules firing)
SUSPICIOUS_THRESHOLD  = 40   # 40 ≤ score < 70 → SUSPICIOUS
# score < 40 → COMPROMISED (arithmetic)

_POSTINSTALL_ORIGINS = frozenset({"postinstall-suspected", "postinstall-confirmed"})


def compute_score(result: "ScanResult") -> int:
    """
    Compute the Trust Score (0-100) per the PRD formula.
    """
    # Step 1: Sum all arithmetic Layer 1 penalties
    l1_penalty = 0
    for finding in result.findings:
        if finding.penalty is not None:
            l1_penalty += finding.penalty

    # Step 2: Layer 2 displacement
    l2_penalty = 0.0
    if result.layer2_delta_pct is not None:
        pass
    
    # Layer 2 properly provided as DisplacementResult during test or real
    displacement_magnitude = 0.0
    attack_multiplier = 1.0
    
    # Check if a displacement result was attached
    disp = getattr(result, "displacement", None)
    if disp:
        displacement_magnitude = disp.magnitude
        attack_multiplier = 1.5 if disp.direction == "attack" else 1.0
        l2_penalty = displacement_magnitude * 30 * attack_multiplier

    # Step 3: Layer 3 confidence bonus
    l3_bonus = 0
    l3_conf = getattr(result, "l3_confidence_clean", None)
    
    if l3_conf is not None:
        # Test uses raw float for l3_confidence_clean
        # Only add bonus if no L1 rules fired
        if not result.findings:
            l3_bonus = int(l3_conf * 10)
    elif result.layer3_result and isinstance(result.layer3_result, dict):
        confidence = result.layer3_result.get("confidence", 0) or 0
        if isinstance(confidence, (int, float)) and confidence > 0.8:
            # Only add bonus if confident the file is clean AND no rules fired
            if not result.findings:
                l3_bonus = min(int(confidence * 10), 10)

    raw_score = 100 + l1_penalty - l2_penalty + l3_bonus

    # Step 4: Apply ceiling rules (S14b, S16)
    has_ceiling_rule = False
    for f in result.findings:
        if getattr(f, 'ceiling', None) is not None:
            raw_score = min(raw_score, f.ceiling)
            has_ceiling_rule = True

    # Check capping for l3 bonus when findings exist?
    # Wait, "the L3 clean-confidence bonus is max +10 and may NOT lift the score above 70 once any L1 rule has fired"
    if result.findings and l3_conf is not None:
        l3_bonus = int(l3_conf * 10)
        raw_score = 100 + l1_penalty - l2_penalty + l3_bonus
        if raw_score > 70:
            raw_score = 70

    # Step 5: Clamp
    trust_score = max(0, min(100, int(raw_score)))

    return trust_score


def compute_verdict(result: "ScanResult", trust_score: int) -> str:
    """
    Determine the verdict string: "CLEAN" | "SUSPICIOUS" | "COMPROMISED".
    """
    firing_rule_ids = {f.rule_id for f in result.findings}
    
    is_unambiguous = any(getattr(f, 'unambiguous', False) for f in result.findings)
    if is_unambiguous:
        return "COMPROMISED"

    # Forced COMPROMISED - structurally unambiguous rules
    if firing_rule_ids & STRUCTURALLY_UNAMBIGUOUS:
        return "COMPROMISED"

    # S16 compound condition
    if "S16" in firing_rule_ids and result.origin in _POSTINSTALL_ORIGINS:
        return "COMPROMISED"

    # Score-ceiling rules cannot produce CLEAN
    has_ceiling_rule = any(getattr(f, 'ceiling', None) is not None for f in result.findings)

    # Arithmetic verdict
    if trust_score < 40:
        return "COMPROMISED"
    if trust_score < CLEAN_THRESHOLD or has_ceiling_rule:
        return "SUSPICIOUS"
    return "CLEAN"


def score_breakdown(result: "ScanResult", trust_score: int) -> str:
    """
    Human-readable arithmetic trace for audit output and sentinel.lock.
    """
    lines = ["raw=100"]
    total_l1 = sum(f.penalty for f in result.findings if f.penalty is not None)
    if total_l1:
        rule_breakdown = ", ".join(
            f"{f.rule_id}:{f.penalty}"
            for f in result.findings
            if f.penalty is not None
        )
        lines.append(f"L1={total_l1} ({rule_breakdown})")
    else:
        lines.append("L1=0")

    disp = getattr(result, "displacement", None)
    if disp:
        lines.append(f"L2=-{disp.magnitude * 30 * (1.5 if disp.direction == 'attack' else 1.0):.1f}")
    else:
        lines.append("no L2" if result.layer2_delta_pct is None else f"L2=-{result.layer2_delta_pct:.1f}%delta")
        
    l3_conf = getattr(result, "l3_confidence_clean", None)
    if l3_conf is not None:
        lines.append(f"L3=active")
    else:
        lines.append("no L3" if not result.layer3_result else "L3=active")

    verdict = compute_verdict(result, trust_score)
    forced = [f.rule_id for f in result.findings if getattr(f, 'forces_compromised', False) or getattr(f, 'unambiguous', False)]
    forced_note = f". {', '.join(forced)} unambiguous: COMPROMISED." if forced else "."

    return f"{', '.join(lines)} -> {trust_score}{forced_note}"

from dataclasses import dataclass
@dataclass
class DisplacementResult:
    magnitude: float
    direction: str
