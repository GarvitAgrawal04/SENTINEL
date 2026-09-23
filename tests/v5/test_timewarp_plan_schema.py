"""Schema and CLI tests for `sentinel timewarp <file> --json` (Day 4 T4)."""

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from sentinel.cli import main

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "specs" / "timewarp_plan.schema.json"


@pytest.fixture
def plan_schema():
    assert SCHEMA_PATH.is_file(), f"Schema not found at {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_timewarp_plan_schema_sleeper_fixture(plan_schema, capsys):
    """Test that sentinel timewarp <file> --json output strictly validates against JSON schema."""
    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    ret = main(["timewarp", str(target_file), "--json"])
    assert ret == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    # Validate against JSON schema
    jsonschema.validate(instance=data, schema=plan_schema)

    assert data["version"] == "1.0.0"
    assert data["triggers_count"] == 1
    assert data["scenarios_count"] == 2
    assert data["triggers"][0]["kind"] == "session_numeric"
    assert data["plan"][0]["name"] == "now"
    assert data["plan"][1]["name"] == "session_3"
    assert data["estimate"]["scenarios"] == 2
    assert data["estimate"]["tokens"] > 0
    assert data["estimate"]["cost_usd"] > 0.0


def test_timewarp_plan_schema_multi_trigger(tmp_path, plan_schema, capsys):
    """Test multi-trigger file scenario plan adheres strictly to schema."""
    agent_file = tmp_path / "CLAUDE.md"
    agent_file.write_text(
        "# Engineering Instructions\n"
        "In two weeks, perform database migration.\n"
        "Starting with the fourth session, enable verbose diagnostics.\n"
        "On release branch, run deployment check.\n"
        "After the beta, collect user telemetry.\n",
        encoding="utf-8",
    )

    ret = main(["timewarp", str(agent_file), "--json"])
    assert ret == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    # Strict jsonschema validation
    jsonschema.validate(instance=data, schema=plan_schema)

    assert data["triggers_count"] == 4
    # Plan: now, rel_2_w, session_4, branch_release, milestone_beta
    assert data["scenarios_count"] == 5

    kinds = [t["kind"] for t in data["triggers"]]
    assert "relative_date" in kinds
    assert "session_ordinal" in kinds
    assert "branch" in kinds
    assert "milestone" in kinds


def test_timewarp_plan_human_output(capsys):
    """Test human text output of sentinel timewarp."""
    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    ret = main(["timewarp", str(target_file)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "sentinel timewarp  plan for AGENTS.md" in captured.out
    assert "[now" in captured.out
    assert "[session_3" in captured.out
    assert "estimate:" in captured.out


def test_timewarp_plan_file_not_found(capsys):
    """Test error handling when file does not exist."""
    ret = main(["timewarp", "non_existent_file.md"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "error: file not found" in captured.err


def test_timewarp_cli_subparser_direct(capsys, plan_schema):
    """Test explicit subparser call `sentinel timewarp plan <file> --json`."""
    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    ret = main(["timewarp", "plan", str(target_file), "--json"])
    assert ret == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    jsonschema.validate(instance=data, schema=plan_schema)
    assert data["scenarios_count"] == 2
