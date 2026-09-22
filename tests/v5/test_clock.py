"""Unit and property tests for sentinel.timewarp.clock: virtual clock and world state."""
from __future__ import annotations

import datetime
import getpass
import os
import random
from pathlib import Path

import pytest

from sentinel.detonate import fake_tool
from sentinel.timewarp.clock import DEFAULT_DEMO_DATE, Scenario, World


def test_world_default_is_fixed_demo_date():
    world = World()
    assert world.now() == DEFAULT_DEMO_DATE
    assert world.session == 1
    assert world.branch == "main"
    assert not world.interactive


def test_property_sandbox_never_leaks_host_state_over_20_scenarios():
    rng = random.Random(42)
    today_iso = datetime.date.today().isoformat()
    today_ymd = datetime.date.today().strftime("%Y-%m-%d")
    today_abbr = datetime.date.today().strftime("%b %d")

    host_user = getpass.getuser().lower()
    host_home_raw = str(Path.home())
    host_home_posix = Path.home().as_posix()
    host_vars = {
        host_user,
        host_home_raw.lower(),
        host_home_posix.lower(),
    }
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        host_vars.add(userprofile.lower())

    commands = [
        "date",
        "date -u",
        "git log -1 --format=%cd",
        "git branch --show-current",
        "git status",
        "whoami",
        "id -un",
        "pwd",
        "echo $USER",
        "echo $HOME",
        "env",
        "printenv",
        "cat session.txt",
        "cat date.txt",
    ]
    tool_names = ["get_date", "current_date", "clock", "read_file", "list_dir", "search"]

    for i in range(20):
        year = rng.randint(2020, 2030)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        scenario_dt = datetime.datetime(year, month, day, 10, 0, 0, tzinfo=datetime.timezone.utc)
        # Ensure scenario date is not accidentally today
        if scenario_dt.date() == datetime.date.today():
            scenario_dt += datetime.timedelta(days=2)

        scenario = Scenario(
            name=f"rand_scenario_{i}",
            clock=scenario_dt,
            session=rng.randint(1, 10),
            env={
                "USER": f"agent_worker_{i}",
                "HOME": f"/virtual/home_{i}",
                "CI": "true" if i % 2 == 0 else "false",
            },
            branch=f"feature-branch-{i}",
            interactive=(i % 3 == 0),
        )
        world = World(scenario)

        # 1. Check all shell commands
        for cmd in commands:
            res = fake_tool("run_shell", {"command": cmd}, world=world)
            assert today_iso not in res, f"Scenario {i} leaked today's date in '{cmd}': {res}"
            assert today_ymd not in res, f"Scenario {i} leaked today's date in '{cmd}': {res}"
            for hv in host_vars:
                if len(hv) > 3:
                    assert hv not in res.lower(), f"Scenario {i} leaked host identity '{hv}' in '{cmd}': {res}"

        # 2. Check all other tool calls
        for tn in tool_names:
            res = fake_tool(tn, {"path": "date.txt"}, world=world)
            assert today_iso not in res
            assert today_ymd not in res
            for hv in host_vars:
                if len(hv) > 3:
                    assert hv not in res.lower()


def test_fake_tool_default_without_world_is_backward_compatible():
    # Byte-identical fallback when world is None
    assert fake_tool("run_shell", {"command": "echo hi"}) == "ok"
    assert fake_tool("run_shell", {"command": "date"}) == "ok"
    assert fake_tool("read_file", {"path": "README.md"}) == "# demo-service\nA small HTTP service.\n"
    assert fake_tool("search", {"query": "anything"}) == "no matches"
