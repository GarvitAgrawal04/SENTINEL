"""Token and cost estimation for Time-Warp detonation runs.

Estimates token usage and provider API costs before running scenarios,
enforcing budget limits by dropping lower-priority scenarios when necessary.
"""
from __future__ import annotations

import math
from typing import Any

from sentinel.timewarp.clock import Scenario

# Estimated tokens per scenario turn (system instructions + prompt + tools + history)
AVG_PROMPT_TOKENS_PER_TURN = 1200
AVG_COMPLETION_TOKENS_PER_TURN = 80
AVG_TURNS_PER_PROBE = 3
PROBES_PER_SCENARIO = 3

# Cost per 1M tokens (blended input/output reference across cheap obedient models, e.g. gpt-4o-mini / haiku)
COST_PER_MILLION_TOKENS = 0.25


def estimate_scenario_tokens(file_text: str) -> int:
    """Estimate total tokens consumed by one scenario run."""
    file_tokens = max(10, len(file_text) // 4)
    turn_tokens = AVG_PROMPT_TOKENS_PER_TURN + file_tokens + AVG_COMPLETION_TOKENS_PER_TURN
    return turn_tokens * AVG_TURNS_PER_PROBE * PROBES_PER_SCENARIO


def estimate_plan_cost(file_text: str, plan_len: int) -> tuple[int, float]:
    """Return (total_tokens, total_cost_usd) for a plan."""
    per_scenario = estimate_scenario_tokens(file_text)
    total_tokens = per_scenario * plan_len
    total_cost = (total_tokens / 1_000_000) * COST_PER_MILLION_TOKENS
    return total_tokens, total_cost


def apply_budget(
    plan: list[Scenario | dict[str, Any]],
    file_text: str,
    budget: float | None = None,
) -> tuple[list[Scenario | dict[str, Any]], list[str]]:
    """Enforce budget constraint, returning (kept_scenarios, dropped_scenario_names)."""
    if budget is None or budget <= 0 or not plan:
        return plan, []

    per_scenario_tokens = estimate_scenario_tokens(file_text)
    per_scenario_cost = (per_scenario_tokens / 1_000_000) * COST_PER_MILLION_TOKENS

    # If budget is integer >= 1 and plan is larger, budget could be number of scenarios
    if budget >= 1 and float(budget).is_integer():
        max_allowed = int(budget)
    else:
        max_allowed = max(1, math.floor(budget / per_scenario_cost)) if per_scenario_cost > 0 else len(plan)

    if len(plan) <= max_allowed:
        return plan, []

    kept = plan[:max_allowed]
    dropped = []
    for item in plan[max_allowed:]:
        name = getattr(item, "name", None) if not isinstance(item, dict) else item.get("name")
        dropped.append(str(name or "scenario"))

    return kept, dropped
