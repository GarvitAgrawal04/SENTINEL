"""Trigger extraction for Time-Warp sandbox scenario planning.

Analyzes agent instruction files to discover dormant, conditional, or time-delayed triggers:
- Ordinal session wordings ("third session", "from the fifth run")
- Numeric session conditions ("session >= 3", "after 4 sessions")
- Relative date offsets ("in two weeks", "after 3 days", "in two months")
- Milestone events ("after the beta", "post-beta", "after launch")
- Calendar events ("on weekends", "at end of month", "after October 2026")
- Branch and environment conditions ("on release branch", "in CI environment")

Extracts structured Trigger objects and generates concrete Scenarios for time-warp detonation.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import Any

from sentinel.timewarp.clock import DEFAULT_DEMO_DATE, Scenario

ORDINAL_WORDS: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}

WORD_NUMBERS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fourteen": 14,
    "thirty": 30,
}

MONTH_MAP: dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


@dataclass(frozen=True)
class Trigger:
    kind: str
    raw_text: str
    scenario: Scenario
    line: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "raw_text": self.raw_text,
            "line": self.line,
            "scenario": {
                "name": self.scenario.name,
                "session": self.scenario.session,
                "branch": self.scenario.branch,
                "clock": (
                    self.scenario.clock.isoformat()
                    if isinstance(self.scenario.clock, datetime.datetime)
                    else str(self.scenario.clock)
                ),
                "env": self.scenario.env,
            },
        }


def _parse_number(token: str) -> int | None:
    token = token.lower().strip()
    if token.isdigit():
        return int(token)
    return WORD_NUMBERS.get(token)


def extract_triggers(
    text: str,
    base_date: datetime.datetime | None = None,
) -> list[Trigger]:
    """Extract all dormant/conditional triggers from instruction text."""
    if base_date is None:
        base_date = DEFAULT_DEMO_DATE
    if base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=datetime.timezone.utc)

    triggers: list[Trigger] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue

        lower = line_clean.lower()

        # -------------------------------------------------------------
        # 1. Ordinal session wordings: "third session", "from the second run"
        # -------------------------------------------------------------
        ord_pattern = re.compile(
            r"\b(?:from|on|after|at|in|during|starting\s+with)\s+(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(?:session|run|interaction|turn|conversation|invocation)\b",
            re.I,
        )
        for m in ord_pattern.finditer(line_clean):
            word = m.group(1).lower()
            sess_num = ORDINAL_WORDS.get(word, 1)
            triggers.append(
                Trigger(
                    kind="session_ordinal",
                    raw_text=m.group(0),
                    scenario=Scenario(
                        name=f"session_{sess_num}",
                        session=sess_num,
                        branch="main",
                        clock=base_date.isoformat(),
                        env={"CI": "false"},
                    ),
                    line=idx,
                )
            )

        # -------------------------------------------------------------
        # 2. Numeric session conditions: "session 3", "session >= 5", "after 4 sessions"
        # -------------------------------------------------------------
        num_pattern = re.compile(
            r"\b(?:(?:if\s+)?session\s*(?:>=?|>|=|==)?\s*(\d+)(?:\s+or\s+later)?|after\s+(\d+)\s+(?:sessions?|runs?|times?|turns?|interactions?|invocations?)|from\s+session\s+(\d+))\b",
            re.I,
        )
        for m in num_pattern.finditer(line_clean):
            sess_str = m.group(1) or m.group(2) or m.group(3)
            sess_num = int(sess_str)
            if 2 <= sess_num <= 100:
                triggers.append(
                    Trigger(
                        kind="session_numeric",
                        raw_text=m.group(0),
                        scenario=Scenario(
                            name=f"session_{sess_num}",
                            session=sess_num,
                            branch="main",
                            clock=base_date.isoformat(),
                            env={"CI": "false"},
                        ),
                        line=idx,
                    )
                )

        # -------------------------------------------------------------
        # 3. Relative dates: "in two weeks", "after 3 days", "in 1 month"
        # -------------------------------------------------------------
        rel_pattern = re.compile(
            r"\b(?:in|after)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fourteen|thirty)\s+(days?|weeks?|months?)\b",
            re.I,
        )
        for m in rel_pattern.finditer(line_clean):
            qty = _parse_number(m.group(1))
            unit = m.group(2).lower()
            if qty is not None and qty > 0:
                if "day" in unit:
                    delta = datetime.timedelta(days=qty)
                elif "week" in unit:
                    delta = datetime.timedelta(days=qty * 7)
                elif "month" in unit:
                    delta = datetime.timedelta(days=qty * 30)
                else:
                    delta = datetime.timedelta(days=qty)

                target_date = base_date + delta
                name_slug = f"rel_{qty}_{unit[0]}"
                triggers.append(
                    Trigger(
                        kind="relative_date",
                        raw_text=m.group(0),
                        scenario=Scenario(
                            name=name_slug,
                            session=1,
                            branch="main",
                            clock=target_date.isoformat(),
                            env={"CI": "false"},
                        ),
                        line=idx,
                    )
                )

        # -------------------------------------------------------------
        # 4. Milestone / phase events: "after the beta", "post-beta", "after launch"
        # -------------------------------------------------------------
        milestone_pattern = re.compile(
            r"\b(?:after\s+|following\s+|post-?\s*)(?:the\s+)?(beta|alpha|v\d+(?:\.\d+)?|launch|release)\b",
            re.I,
        )
        for m in milestone_pattern.finditer(line_clean):
            milestone = m.group(1).lower().replace(".", "_")
            # Milestone default offset: +45 days from baseline
            target_date = base_date + datetime.timedelta(days=45)
            triggers.append(
                Trigger(
                    kind="milestone",
                    raw_text=m.group(0),
                    scenario=Scenario(
                        name=f"milestone_{milestone}",
                        session=1,
                        branch="main",
                        clock=target_date.isoformat(),
                        env={"STAGE": milestone, "CI": "false"},
                    ),
                    line=idx,
                )
            )

        # -------------------------------------------------------------
        # 5. Calendar dates & recurring moments
        # -------------------------------------------------------------
        if "weekend" in lower:
            # First Saturday following base date (2026-09-01 is Tuesday -> 2026-09-05 is Saturday)
            sat = base_date + datetime.timedelta(days=(5 - base_date.weekday()) % 7 or 7)
            sat = sat.replace(hour=12, minute=0, second=0)
            triggers.append(
                Trigger(
                    kind="calendar_weekend",
                    raw_text="weekend",
                    scenario=Scenario(
                        name="weekend",
                        session=1,
                        branch="main",
                        clock=sat.isoformat(),
                        env={"CI": "false"},
                    ),
                    line=idx,
                )
            )

        if "end of month" in lower or "month-end" in lower or "month end" in lower:
            # End of September 2026
            eom = base_date.replace(day=30, hour=23, minute=59, second=0)
            triggers.append(
                Trigger(
                    kind="calendar_month_end",
                    raw_text="end of month",
                    scenario=Scenario(
                        name="month_end",
                        session=1,
                        branch="main",
                        clock=eom.isoformat(),
                        env={"CI": "false"},
                    ),
                    line=idx,
                )
            )

        if "friday" in lower:
            fri = base_date + datetime.timedelta(days=(4 - base_date.weekday()) % 7 or 7)
            fri = fri.replace(hour=18, minute=0, second=0)
            triggers.append(
                Trigger(
                    kind="calendar_friday",
                    raw_text="friday",
                    scenario=Scenario(
                        name="friday",
                        session=1,
                        branch="main",
                        clock=fri.isoformat(),
                        env={"CI": "false"},
                    ),
                    line=idx,
                )
            )

        # "after October 2026", "after Nov 2026"
        month_yr_match = re.search(
            r"\b(?:after|from|starting)\s+([a-zA-Z]+)\s+(\d{4})\b",
            line_clean,
            re.I,
        )
        if month_yr_match:
            m_name = month_yr_match.group(1).lower()
            year = int(month_yr_match.group(2))
            if m_name in MONTH_MAP and 2020 <= year <= 2035:
                m_num = MONTH_MAP[m_name]
                dt = datetime.datetime(year, m_num, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
                triggers.append(
                    Trigger(
                        kind="calendar_future_date",
                        raw_text=month_yr_match.group(0),
                        scenario=Scenario(
                            name=f"date_{year}_{m_num:02d}",
                            session=1,
                            branch="main",
                            clock=dt.isoformat(),
                            env={"CI": "false"},
                        ),
                        line=idx,
                    )
                )

        # -------------------------------------------------------------
        # 6. Branch triggers: "on release branch", "on production branch"
        # -------------------------------------------------------------
        branch_match = re.search(
            r"\b(?:on|when on|in|under|for)\s+(?:the\s+)?(release|prod(?:uction)?|staging|dev(?:elopment)?)\s+branch\b",
            line_clean,
            re.I,
        )
        if branch_match:
            b_raw = branch_match.group(1).lower()
            b_norm = "production" if "prod" in b_raw else "release" if "rel" in b_raw else "dev" if "dev" in b_raw else b_raw
            triggers.append(
                Trigger(
                    kind="branch",
                    raw_text=branch_match.group(0),
                    scenario=Scenario(
                        name=f"branch_{b_norm}",
                        session=1,
                        branch=b_norm,
                        clock=base_date.isoformat(),
                        env={"CI": "false", "BRANCH": b_norm},
                    ),
                    line=idx,
                )
            )

        # -------------------------------------------------------------
        # 7. CI / Environment triggers: "in CI", "if CI environment"
        # -------------------------------------------------------------
        if re.search(r"\b(?:if|when|in)\s+(?:the\s+)?(?:CI|continuous\s+integration)(?:\s+environment)?\b", line_clean, re.I):
            triggers.append(
                Trigger(
                    kind="env_ci",
                    raw_text="CI environment",
                    scenario=Scenario(
                        name="ci_env",
                        session=1,
                        branch="main",
                        clock=base_date.isoformat(),
                        env={"CI": "true"},
                    ),
                    line=idx,
                )
            )

    return triggers


def deduplicate_scenarios(scenarios: list[Scenario]) -> list[Scenario]:
    """De-duplicate scenarios so the plan never tests the exact same moment twice."""
    seen: set[tuple[str, int, str, str]] = set()
    unique: list[Scenario] = []

    for sc in scenarios:
        clock_str = (
            sc.clock.isoformat()
            if isinstance(sc.clock, datetime.datetime)
            else str(sc.clock)
        )
        env_str = str(sorted(sc.env.items()))
        key = (clock_str, sc.session, sc.branch, env_str)
        if key not in seen:
            seen.add(key)
            unique.append(sc)

    return unique


def plan_scenarios(
    text: str,
    base_date: datetime.datetime | None = None,
    include_baseline: bool = True,
    config: Any = None,
) -> list[Scenario]:
    """Generate a deduplicated time-warp evaluation plan from instruction text.

    Optionally incorporates default matrix configurations from sentinel.timewarp.yml.
    """
    if config is not None:
        if base_date is None and getattr(config, "matrix", None) and config.matrix.base_date:
            base_date = config.matrix.base_date
        if hasattr(config, "matrix") and config.matrix is not None:
            include_baseline = config.matrix.include_baseline

    if base_date is None:
        base_date = DEFAULT_DEMO_DATE
    if base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=datetime.timezone.utc)

    plan: list[Scenario] = []
    if include_baseline:
        plan.append(
            Scenario(
                name="now",
                session=1,
                branch="main",
                clock=base_date.isoformat(),
                env={"CI": "false"},
            )
        )

    # 1. Extracted conditional triggers
    triggers = extract_triggers(text, base_date=base_date)
    for t in triggers:
        plan.append(t.scenario)

    # 2. Config matrix scenarios
    if config is not None:
        from sentinel.timewarp import config as tw_config
        config_scenarios = tw_config.generate_scenarios_from_config(config)
        plan.extend(config_scenarios)

    deduped = deduplicate_scenarios(plan)

    # 3. Budget enforcement if configured
    if config is not None and getattr(config, "budget", None) and config.budget.max_scenarios:
        deduped = deduped[: config.budget.max_scenarios]

    return deduped
