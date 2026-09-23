"""Tests for GitHub Action specification (action/action.yml)."""
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTION_YML = ROOT / "action" / "action.yml"


def test_action_yml_structure():
    assert ACTION_YML.is_file(), f"action.yml missing at {ACTION_YML}"
    data = yaml.safe_load(ACTION_YML.read_text(encoding="utf-8"))

    # Metadata
    assert "name" in data
    assert "branding" in data
    assert data["branding"]["icon"] == "shield"

    # Inputs
    inputs = data.get("inputs", {})
    assert "fail-on" in inputs
    assert "detonate" in inputs
    assert "comment" in inputs
    assert "sarif" in inputs

    # Outputs
    outputs = data.get("outputs", {})
    assert "code" in outputs
    assert "sarif-file" in outputs

    # Runs
    runs = data.get("runs", {})
    assert runs.get("using") == "composite"
    steps = runs.get("steps", [])
    assert len(steps) >= 4

    # Verify python setup and pip install
    step_runs = [s.get("run", "") for s in steps]
    assert any("setup-python" in s.get("uses", "") for s in steps)
    assert any("pip install" in r for r in step_runs)
    assert any("sentinel pr" in r for r in step_runs)
