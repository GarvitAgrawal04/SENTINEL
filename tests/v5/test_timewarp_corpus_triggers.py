"""Tests for corpus trigger fixtures and twins (Day 4 T6-T10).

Verifies that:
1. All 10 attack trigger fixtures extract the intended conditional triggers.
2. All 10 benign twin fixtures extract identical conditional triggers.
3. Benign twins stay clean of malicious exfiltration findings.
"""

from pathlib import Path

from sentinel import contract
from sentinel.timewarp import triggers

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "timewarp_triggers"

PAIRS = [
    ("attack_01_rel_two_weeks.md", "twin_01_rel_two_weeks.md", "relative_date"),
    ("attack_02_post_launch.md", "twin_02_post_launch.md", "milestone"),
    ("attack_03_third_session.md", "twin_03_third_session.md", "session_ordinal"),
    ("attack_04_session_ge_5.md", "twin_04_session_ge_5.md", "session_numeric"),
    ("attack_05_weekend.md", "twin_05_weekend.md", "calendar_weekend"),
    ("attack_06_month_end.md", "twin_06_month_end.md", "calendar_month_end"),
    ("attack_07_branch_release.md", "twin_07_branch_release.md", "branch"),
    ("attack_08_branch_prod.md", "twin_08_branch_prod.md", "branch"),
    ("attack_09_env_ci.md", "twin_09_env_ci.md", "env_ci"),
    ("attack_10_after_oct_2026.md", "twin_10_after_oct_2026.md", "calendar_future_date"),
]


def test_fixture_files_exist():
    """Verify all 20 fixture files exist in FIXTURE_DIR."""
    for atk, twin, _ in PAIRS:
        assert (FIXTURE_DIR / atk).is_file(), f"Missing {atk}"
        assert (FIXTURE_DIR / twin).is_file(), f"Missing {twin}"


def test_trigger_extraction_parity():
    """Verify trigger extraction extracts the expected kind and matches scenario moments."""
    for atk_name, twin_name, expected_kind in PAIRS:
        atk_text = (FIXTURE_DIR / atk_name).read_text(encoding="utf-8")
        twin_text = (FIXTURE_DIR / twin_name).read_text(encoding="utf-8")

        atk_triggers = triggers.extract_triggers(atk_text)
        twin_triggers = triggers.extract_triggers(twin_text)

        assert len(atk_triggers) >= 1, f"No triggers extracted from {atk_name}"
        assert len(twin_triggers) >= 1, f"No triggers extracted from {twin_name}"

        atk_kinds = [t.kind for t in atk_triggers]
        twin_kinds = [t.kind for t in twin_triggers]

        assert expected_kind in atk_kinds, f"Expected {expected_kind} in {atk_name}, got {atk_kinds}"
        assert expected_kind in twin_kinds, f"Expected {expected_kind} in {twin_name}, got {twin_kinds}"

        atk_plan = triggers.plan_scenarios(atk_text)
        twin_plan = triggers.plan_scenarios(twin_text)

        # Scenarios planned should have identical moments
        atk_moments = [(s.session, s.branch, s.clock) for s in atk_plan]
        twin_moments = [(s.session, s.branch, s.clock) for s in twin_plan]
        assert atk_moments == twin_moments, f"Scenario mismatch between {atk_name} and {twin_name}"


def test_benign_twins_not_compromised():
    """Verify that all benign twins do not trigger COMPROMISED verdicts in scanner."""
    for _, twin_name, _ in PAIRS:
        twin_file = FIXTURE_DIR / twin_name
        twin_text = twin_file.read_text(encoding="utf-8")
        res = contract.scan_text(twin_name, twin_text)
        # Benign twins must not be COMPROMISED
        assert res["verdict"] != "COMPROMISED", (
            f"Benign twin {twin_name} was falsely flagged as COMPROMISED: {res['findings']}"
        )
