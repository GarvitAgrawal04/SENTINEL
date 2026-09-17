"""
Trust Score formula, exercised with Layer-1 findings (PRD 13.2).

    raw   = 100 − Σ(L1 penalties) − (displacement_mag × 30 × attack_mult) + (L3_conf × 10)
    Trust = clamp(raw, 0, 100)

Rules the arithmetic must obey:
  * attack_mult = 1.5 when displacement.direction == "attack", else 1.0
  * the L3 clean-confidence bonus is ≤ +10 and may NOT lift the score above 70 once any
    L1 rule has fired
  * a structurally-unambiguous finding forces verdict COMPROMISED regardless of the number
  * a `ceiling` caps the score (S14b / S16-alone → 60) but does NOT force COMPROMISED
  * clamp keeps the result inside [0, 100]

Findings here are synthesised with the `mk_finding` fixture so the formula is tested in
isolation from the detectors. Penalties are stored negative on the Finding, exactly as the
rules emit them.

The four worked examples from PRD 13.2 are reproduced verbatim. Their SCORES are pinned
here; the numeric verdict *thresholds* (is 94 CLEAN or SUSPICIOUS?) are deliberately left
to a skipped test — see tests/README.md, "decisions the PRD leaves open".
"""
import pytest

from sentinel.scoring.formula import DisplacementResult

CLEAN = "CLEAN"
SUSPICIOUS = "SUSPICIOUS"
COMPROMISED = "COMPROMISED"


# --- the four PRD 13.2 worked examples (scores) ------------------------------
def test_example1_clean_with_small_displacement(score):
    """Clean CLAUDE.md, benign 0.20 displacement → 100 − 6 = 94."""
    r = score([], DisplacementResult(magnitude=0.20, direction="benign"))
    assert r.score == 94
    assert r.verdict != COMPROMISED  # nothing fired; can't be COMPROMISED


def test_example2_s10_no_baseline(score, mk_finding):
    """S10 alone, no Layer-2 signal → 100 − 70 = 30, forced COMPROMISED."""
    r = score([mk_finding("S10", -70, unambiguous=True)])
    assert r.score == 30
    assert r.verdict == COMPROMISED


def test_example3_s1_plus_s5(score, mk_finding):
    """Invisible Unicode + exfil URL → 100 − 90 = 10, forced COMPROMISED."""
    r = score([mk_finding("S1", -50, unambiguous=True), mk_finding("S5", -40)])
    assert r.score == 10
    assert r.verdict == COMPROMISED


def test_example4_s16_alone_ceiling(score, mk_finding):
    """enableAllProjectMcpServers alone → ceiling 60 → SUSPICIOUS."""
    r = score([mk_finding("S16", 0, ceiling=60)])
    assert r.score == 60
    assert r.verdict == SUSPICIOUS


# --- clamping ----------------------------------------------------------------
def test_clamp_low_never_below_zero(score, mk_finding):
    """S10 + S11 + S14a = −210 → clamps to 0, not −110."""
    findings = [mk_finding("S10", -70, unambiguous=True),
                mk_finding("S11", -70, unambiguous=True),
                mk_finding("S14a", -70, unambiguous=True)]
    r = score(findings)
    assert r.score == 0
    assert r.verdict == COMPROMISED


def test_clamp_high_never_above_hundred(score):
    """No findings + full clean confidence → 100 + 10 = 110 → clamps to 100."""
    r = score([], None, 1.0)
    assert r.score == 100


# --- displacement multiplier -------------------------------------------------
def test_displacement_benign_multiplier(score):
    """0.4 × 30 × 1.0 = 12 → 88."""
    r = score([], DisplacementResult(magnitude=0.4, direction="benign"))
    assert r.score == 88


def test_displacement_attack_multiplier(score):
    """Movement toward the attack cluster weights 1.5×: 0.4 × 30 × 1.5 = 18 → 82."""
    r = score([], DisplacementResult(magnitude=0.4, direction="attack"))
    assert r.score == 82


# --- L3 clean-confidence bonus ----------------------------------------------
def test_l3_bonus_capped_at_70_when_l1_fired(score, mk_finding):
    """One −35 finding → raw 65; +10 L3 would give 75 but the cap holds it at 70."""
    r = score([mk_finding("S3", -35)], None, 1.0)
    assert r.score == 70


def test_l3_bonus_applies_when_nothing_fired(score):
    """No L1 findings → the +10 bonus is allowed (here 90 + 10 via displacement offset)."""
    r = score([], DisplacementResult(magnitude=0.4, direction="benign"), 1.0)
    # 100 − 12 + 10 = 98
    assert r.score == 98


# --- unambiguous overrides the arithmetic ------------------------------------
def test_unambiguous_forces_compromised_at_high_score(score, mk_finding):
    """Even a tiny penalty, if the finding is unambiguous, forces COMPROMISED."""
    r = score([mk_finding("S1", -5, unambiguous=True)])
    assert r.score == 95            # arithmetic alone would read CLEAN
    assert r.verdict == COMPROMISED  # ...but structural certainty overrides it


# --- ceiling caps but does not condemn ---------------------------------------
def test_ceiling_caps_score_below_arithmetic(score, mk_finding):
    """S14b (ceiling 60) alongside S4 (−25): raw 75, ceiling wins → 60."""
    r = score([mk_finding("S14b", 0, ceiling=60), mk_finding("S4", -25)])
    assert r.score == 60


def test_ceiling_does_not_force_compromised(score, mk_finding):
    """A ceiling means 'not CLEAN', never 'COMPROMISED'."""
    r = score([mk_finding("S16", 0, ceiling=60)])
    assert r.verdict != COMPROMISED


def test_lower_arithmetic_wins_over_ceiling(score, mk_finding):
    """If penalties already drive below the ceiling, the ceiling is a no-op."""
    r = score([mk_finding("S14b", 0, ceiling=60), mk_finding("S5", -40),
               mk_finding("S2", -35)])
    assert r.score == 25  # 100 − 75, well under the 60 ceiling


# --- auditable breakdown -----------------------------------------------------
def test_breakdown_is_auditable(score, mk_finding):
    r = score([mk_finding("S1", -50, unambiguous=True), mk_finding("S5", -40)])
    b = r.breakdown.replace(" ", "")
    assert "raw=100" in b
    assert "L1=" in b
    assert "S1" in r.breakdown and "S5" in r.breakdown


def test_clean_breakdown_matches_prd_shape(score):
    r = score([], DisplacementResult(magnitude=0.20, direction="benign"))
    b = r.breakdown.replace(" ", "")
    assert "raw=100" in b
    assert "L1=0" in b


# --- deliberately unpinned ---------------------------------------------------
@pytest.mark.skip(reason="PRD 13.2 never states the CLEAN/SUSPICIOUS/COMPROMISED numeric "
                         "boundaries; pin these once the team decides (see README).")
def test_verdict_thresholds_TODO(score):
    assert score([]).verdict == CLEAN                      # 100 → CLEAN
    assert score([], DisplacementResult(0.20, "benign")).verdict == CLEAN   # 94 → CLEAN?
    # ...and the exact SUSPICIOUS / COMPROMISED boundaries.
