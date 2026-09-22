"""Time-warp scenario runner for sandbox detonation.

Runs a file across multiple virtual scenarios (clock, session, branch, env)
using either a real model or a recorded cassette.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sentinel import detonate
from sentinel.timewarp.cassette import Cassette
from sentinel.timewarp.clock import Scenario, World


@dataclass
class Trace:
    scenario: Scenario
    events: list[dict] = field(default_factory=list)
    canary_leaks: list[str] = field(default_factory=list)
    egress: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario if isinstance(self.scenario, dict) else {
                "name": getattr(self.scenario, "name", "custom"),
                "session": getattr(self.scenario, "session", 1),
                "branch": getattr(self.scenario, "branch", "main"),
            },
            "events": self.events,
            "canary_leaks": self.canary_leaks,
            "egress": self.egress,
        }


def _extract_egress_and_leaks(log: list[dict]) -> tuple[list[str], list[str]]:
    egress = []
    leaks = []
    for event in log:
        tool = event.get("tool", "")
        args = event.get("args", {})
        blob = json.dumps(args)
        if tool == "http_request" or (tool in ("run_shell", "bash") and re.search(r"\b(curl|wget|nc|scp)\b", blob)):
            host_m = detonate.URL_HOST.search(blob)
            host = host_m.group(1) if host_m else "unknown-host"
            egress.append(host)
            if detonate.CANARY in blob:
                leaks.append(host)
    return egress, leaks


def run(
    file_text: str,
    plan: list[Scenario | dict[str, Any]],
    model: Any = None,
    cassette: Cassette | Path | str | None = None,
    parallel: int = 1,
    name: str = "CLAUDE.md",
) -> list[Trace]:
    """Execute scenario plan against model or replay cassette."""
    if model is None:
        if cassette is None:
            raise ValueError("Either model or cassette must be provided to timewarp runner.")
        if isinstance(cassette, (str, Path)):
            active_model = Cassette.replay(cassette)
        else:
            active_model = cassette
    else:
        active_model = model

    traces: list[Trace] = []

    for item in plan:
        if isinstance(item, Scenario):
            scenario = item
        elif isinstance(item, dict):
            scenario = Scenario(
                name=item.get("name", "custom"),
                clock=item.get("clock", detonate.VIRTUAL_FS.get("clock", "2026-09-01T12:00:00Z")),
                session=int(item.get("session", 1)),
                env=item.get("env", {}),
                branch=item.get("branch", "main"),
                interactive=bool(item.get("interactive", False)),
                user_turns=item.get("user_turns", []),
            )
        else:
            scenario = Scenario()

        world = World(scenario)
        log: list[dict] = []
        canary_escaped = False

        for probe in detonate.PROBES:
            messages = [
                {"role": "system", "content": detonate.SYSTEM.format(name=name, body=file_text)},
                {"role": "user", "content": probe},
            ]
            for _ in range(8):
                msg = active_model.step(messages)
                messages.append(msg)
                calls = msg.get("tool_calls") or []
                if not calls:
                    break
                for c in calls:
                    fn = detonate.TOOL_ALIASES.get(c["function"]["name"], c["function"]["name"])
                    try:
                        args = json.loads(c["function"]["arguments"] or "{}")
                    except json.JSONDecodeError:
                        args = {"_raw": c["function"]["arguments"]}
                    result = detonate.fake_tool(fn, args, world=world)
                    log.append({"probe": probe, "tool": fn, "args": args})
                    messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
                    if detonate.CANARY in json.dumps(args):
                        canary_escaped = True
                        break
                if canary_escaped:
                    break
            if canary_escaped:
                # Early-exit scenario as soon as a canary leaves
                break

        egress, leaks = _extract_egress_and_leaks(log)

        traces.append(Trace(
            scenario=scenario,
            events=log,
            canary_leaks=leaks,
            egress=egress,
        ))

    return traces
