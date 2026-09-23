"""Unit and schema tests for sentinel.timewarp.config (Day 4 T5)."""

import json
from pathlib import Path

import jsonschema
import pytest

from sentinel.timewarp import config, triggers
from sentinel.timewarp.config import ConfigValidationError, TimewarpConfig

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "specs" / "timewarp_config.schema.json"


def test_schema_valid_yaml():
    """Assert that a standard sentinel.timewarp.yml validates against the JSON schema."""
    yaml_text = """
version: "1"
matrix:
  base_date: "2026-09-01T12:00:00Z"
  include_baseline: true
  sessions:
    - 2
    - 5
  branches:
    - release
    - staging
  env:
    CI:
      - "false"
      - "true"
  extra_scenarios:
    - name: "compliance_audit"
      session: 1
      branch: "main"
      clock: "2026-12-31T23:59:59Z"
      env:
        AUDIT: "true"
budget:
  max_scenarios: 10
  max_cost_usd: 0.05
"""
    cfg = config.parse_config(yaml_text)
    assert isinstance(cfg, TimewarpConfig)
    assert cfg.version == "1"
    assert cfg.matrix.include_baseline is True
    assert cfg.matrix.sessions == [2, 5]
    assert cfg.matrix.branches == ["release", "staging"]
    assert cfg.matrix.env == {"CI": ["false", "true"]}
    assert len(cfg.matrix.extra_scenarios) == 1
    assert cfg.matrix.extra_scenarios[0].name == "compliance_audit"
    assert cfg.budget.max_scenarios == 10
    assert cfg.budget.max_cost_usd == 0.05


def test_schema_json_validation_direct():
    """Directly test jsonschema validation against the schema file."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    valid_instance = {
        "version": "1.0",
        "matrix": {
            "base_date": "2026-09-01T12:00:00+00:00",
            "include_baseline": False,
            "sessions": [1, 3],
            "branches": ["main"],
            "extra_scenarios": [
                {
                    "name": "custom",
                    "session": 1,
                    "branch": "main",
                    "clock": "2026-09-01T12:00:00Z",
                    "env": {"DEBUG": "true"},
                }
            ],
        },
        "budget": {
            "max_scenarios": 5,
        },
    }
    jsonschema.validate(instance=valid_instance, schema=schema)


def test_schema_rejects_missing_version():
    """Config without version must be rejected."""
    bad_yaml = """
matrix:
  sessions: [1, 2]
"""
    with pytest.raises(ConfigValidationError):
        config.parse_config(bad_yaml)


def test_schema_rejects_invalid_types():
    """Config with invalid types must be rejected."""
    bad_yaml = """
version: "1"
matrix:
  sessions: "not-a-list"
"""
    with pytest.raises(ConfigValidationError):
        config.parse_config(bad_yaml)


def test_schema_rejects_invalid_date():
    """Config with invalid ISO date must be rejected."""
    bad_yaml = """
version: "1"
matrix:
  base_date: "not-a-valid-date"
"""
    with pytest.raises(ConfigValidationError):
        config.parse_config(bad_yaml)


def test_plan_scenarios_with_config():
    """Verify that plan_scenarios combines extracted triggers and config matrix."""
    yaml_text = """
version: "1"
matrix:
  include_baseline: true
  sessions: [2]
  branches: [release]
  extra_scenarios:
    - name: "special_audit"
      session: 4
      branch: "audit"
"""
    cfg = config.parse_config(yaml_text)
    text = (
        "# Agent file\n"
        "In two weeks, perform full sync.\n"
    )
    plan = triggers.plan_scenarios(text, config=cfg)
    names = [s.name for s in plan]

    assert "now" in names
    assert "rel_2_w" in names  # from trigger
    assert "session_2" in names  # from config sessions
    assert "branch_release" in names  # from config branches
    assert "special_audit" in names  # from config extra_scenarios
    assert len(plan) == 5


def test_load_config_file_not_found():
    """Explicitly requesting a non-existent config path must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        config.load_config(ROOT / "non_existent_config.yml")
