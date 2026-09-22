"""Virtual clock and world state for sandbox detonation.

Provides an isolated environment for model tools where:
  - now() returns a virtual time from the scenario (fixed demo date by default, NEVER host clock).
  - session, env, branch, and user turns reflect the scenario.
  - Fake tools query World so no real host paths, usernames, or dates ever leak.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

# Default fixed demo date: 2026-09-01T12:00:00Z (never the host clock)
DEFAULT_DEMO_DATE = datetime.datetime(2026, 9, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


@dataclass
class Scenario:
    name: str = "baseline"
    clock: datetime.datetime | str = field(default_factory=lambda: DEFAULT_DEMO_DATE)
    session: int = 1
    env: dict[str, str] = field(default_factory=lambda: {
        "CI": "false",
        "USER": "sandbox-user",
        "HOME": "/home/sandbox",
        "BRANCH": "main",
    })
    branch: str = "main"
    interactive: bool = False
    user_turns: list[str] = field(default_factory=list)


class World:
    """Virtual world context exposing clock and system state for sandbox tools."""

    def __init__(self, scenario: Scenario | dict[str, Any] | None = None) -> None:
        if scenario is None:
            self.scenario = Scenario()
        elif isinstance(scenario, dict):
            clock_val = scenario.get("clock", DEFAULT_DEMO_DATE)
            self.scenario = Scenario(
                name=scenario.get("name", "custom"),
                clock=clock_val,
                session=int(scenario.get("session", 1)),
                env=dict(scenario.get("env") or {
                    "CI": "false",
                    "USER": "sandbox-user",
                    "HOME": "/home/sandbox",
                    "BRANCH": scenario.get("branch", "main"),
                }),
                branch=str(scenario.get("branch", "main")),
                interactive=bool(scenario.get("interactive", False)),
                user_turns=list(scenario.get("user_turns") or []),
            )
        else:
            self.scenario = scenario

        self.session: int = getattr(self.scenario, "session", 1)
        self.env: dict[str, str] = getattr(self.scenario, "env", {
            "CI": "false",
            "USER": "sandbox-user",
            "HOME": "/home/sandbox",
        })
        self.branch: str = getattr(self.scenario, "branch", "main")
        self.interactive: bool = getattr(self.scenario, "interactive", False)
        self.user_turns: list[str] = getattr(self.scenario, "user_turns", [])

    def now(self) -> datetime.datetime:
        """Return the virtual timestamp for this scenario. Never consults host clock."""
        raw = getattr(self.scenario, "clock", DEFAULT_DEMO_DATE)
        if isinstance(raw, datetime.datetime):
            if raw.tzinfo is None:
                return raw.replace(tzinfo=datetime.timezone.utc)
            return raw
        if isinstance(raw, str):
            try:
                dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=datetime.timezone.utc)
                return dt
            except ValueError:
                return DEFAULT_DEMO_DATE
        return DEFAULT_DEMO_DATE
