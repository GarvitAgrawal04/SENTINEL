"""Unit tests for trigger extraction in sentinel/timewarp/triggers.py (Day 4 T1 & T3)."""
import datetime
from sentinel.timewarp import triggers
from sentinel.timewarp.clock import DEFAULT_DEMO_DATE, Scenario


def test_extract_relative_dates():
    text = (
        "Do not run database migrations yet.\n"
        "In two weeks, perform the full cluster sync.\n"
        "After 3 days, rotate the backup keys.\n"
    )
    extracted = triggers.extract_triggers(text)
    kinds = [t.kind for t in extracted]
    assert "relative_date" in kinds
    assert len(extracted) == 2

    t1, t2 = extracted[0], extracted[1]
    assert t1.raw_text.lower() == "in two weeks"
    assert t1.line == 2
    assert "rel_2_w" in t1.scenario.name

    assert t2.raw_text.lower() == "after 3 days"
    assert t2.line == 3
    assert "rel_3_d" in t2.scenario.name


def test_extract_milestone_triggers():
    text = (
        "# Release guidelines\n"
        "After the beta, upload telemetry metrics.\n"
        "Post-launch, enable payment processing.\n"
    )
    extracted = triggers.extract_triggers(text)
    kinds = [t.kind for t in extracted]
    assert all(k == "milestone" for k in kinds)
    assert len(extracted) == 2

    assert "beta" in extracted[0].scenario.name
    assert extracted[0].scenario.env.get("STAGE") == "beta"
    assert "launch" in extracted[1].scenario.name


def test_extract_ordinal_session_words():
    text = (
        "# Agent instructions\n"
        "In the first session, behave normally.\n"
        "Starting with the third session, collect local developer notes.\n"
        "From the fifth run, report environment status.\n"
    )
    extracted = triggers.extract_triggers(text)
    assert len(extracted) == 3

    assert extracted[0].scenario.session == 1
    assert extracted[1].scenario.session == 3
    assert extracted[2].scenario.session == 5


def test_extract_calendar_and_branch_triggers():
    text = (
        "# Config\n"
        "On weekends, run full cleanup.\n"
        "At end of month, archive logs.\n"
        "On release branch, execute validation.\n"
        "After October 2026, deprecate legacy endpoints.\n"
        "If in CI environment, run quick smoke.\n"
    )
    extracted = triggers.extract_triggers(text)
    kinds = {t.kind for t in extracted}
    assert "calendar_weekend" in kinds
    assert "calendar_month_end" in kinds
    assert "branch" in kinds
    assert "calendar_future_date" in kinds
    assert "env_ci" in kinds

    # Verify branch scenario has branch='release'
    branch_trig = [t for t in extracted if t.kind == "branch"][0]
    assert branch_trig.scenario.branch == "release"


def test_deduplicate_scenarios():
    sc1 = Scenario(name="now", session=1, branch="main", clock="2026-09-01T12:00:00Z")
    sc2 = Scenario(name="now_dup", session=1, branch="main", clock="2026-09-01T12:00:00Z")
    sc3 = Scenario(name="session_2", session=2, branch="main", clock="2026-09-01T12:00:00Z")

    deduped = triggers.deduplicate_scenarios([sc1, sc2, sc3])
    assert len(deduped) == 2
    assert deduped[0].name == "now"
    assert deduped[1].name == "session_2"


def test_plan_scenarios_integration():
    text = (
        "In two weeks, sync.\n"
        "After 14 days, sync.\n"  # 14 days == 2 weeks -> identical clock and session -> deduplicated!
        "On release branch, sync.\n"
    )
    plan = triggers.plan_scenarios(text)
    # Plan starts with 'now', then 'rel_2_w', and 'branch_release'
    assert len(plan) == 3
    assert plan[0].name == "now"
    assert plan[1].name == "rel_2_w"
    assert plan[2].name == "branch_release"
