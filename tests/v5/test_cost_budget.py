"""Unit tests for sentinel.timewarp.cost: token/cost estimation and budget enforcement."""
from __future__ import annotations

from sentinel.timewarp.clock import Scenario
from sentinel.timewarp.cost import apply_budget, estimate_plan_cost, estimate_scenario_tokens


def test_estimate_scenario_tokens():
    text = "Short instruction file."
    tokens = estimate_scenario_tokens(text)
    assert tokens > 0
    # ~10,000 to ~15,000 tokens for standard 3 probes * 3 turns
    assert 5_000 < tokens < 30_000


def test_estimate_plan_cost():
    text = "Run tests before pushing."
    total_tokens, total_cost = estimate_plan_cost(text, 4)
    assert total_tokens > 0
    assert total_cost > 0.0
    assert total_cost < 1.0  # Fraction of a cent to a few cents for small plan


def test_apply_budget_drops_excess_scenarios():
    plan = [
        Scenario(name="now"),
        Scenario(name="session_2"),
        Scenario(name="session_3"),
        Scenario(name="session_4"),
    ]
    file_text = "Instructions"

    # 1. Budget of 2 scenarios
    kept, dropped = apply_budget(plan, file_text, budget=2)
    assert len(kept) == 2
    assert dropped == ["session_3", "session_4"]

    # 2. No budget limit
    kept_all, dropped_none = apply_budget(plan, file_text, budget=None)
    assert len(kept_all) == 4
    assert len(dropped_none) == 0
