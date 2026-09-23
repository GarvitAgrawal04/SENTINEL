"""Configuration loader and schema validator for sentinel.timewarp.yml.

Supports custom default matrix dimensions, custom sessions/branches/env,
extra scenarios, and scenario budget limits.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sentinel.timewarp.clock import DEFAULT_DEMO_DATE, Scenario

# Path to the JSON schema for validation
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "specs" / "timewarp_config.schema.json"


@dataclass
class TimewarpMatrix:
    base_date: datetime.datetime | None = None
    include_baseline: bool = True
    sessions: list[int] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    env: dict[str, list[str]] = field(default_factory=dict)
    extra_scenarios: list[Scenario] = field(default_factory=list)


@dataclass
class TimewarpBudget:
    max_scenarios: int | None = None
    max_cost_usd: float | None = None


@dataclass
class TimewarpConfig:
    version: str = "1"
    matrix: TimewarpMatrix = field(default_factory=TimewarpMatrix)
    budget: TimewarpBudget | None = None


class ConfigValidationError(ValueError):
    """Raised when sentinel.timewarp.yml fails schema or structural validation."""
    pass


def _parse_yaml_or_json(content: str) -> dict[str, Any]:
    """Parse YAML content using PyYAML if available, or fallback to JSON."""
    try:
        import yaml
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise ConfigValidationError("Configuration must be a mapping/dictionary.")
        return parsed
    except ImportError:
        # Fallback to JSON
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ConfigValidationError("Configuration must be a mapping/dictionary.")
            return parsed
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(f"Failed to parse configuration: {exc}") from exc


def validate_config_dict(data: dict[str, Any]) -> None:
    """Validate a parsed configuration dictionary against timewarp_config.schema.json."""
    if not isinstance(data, dict):
        raise ConfigValidationError("Configuration root must be an object.")

    if not SCHEMA_PATH.is_file():
        # If schema file is missing, do basic manual checks
        if "version" not in data:
            raise ConfigValidationError("Missing required 'version' field.")
        return

    try:
        import jsonschema
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        # Manual validation if jsonschema package is absent
        if "version" not in data:
            raise ConfigValidationError("Missing required 'version' field.")
    except Exception as exc:
        raise ConfigValidationError(f"Schema validation error: {exc}") from exc


def parse_config(content: str) -> TimewarpConfig:
    """Parse and validate configuration text into a TimewarpConfig instance."""
    data = _parse_yaml_or_json(content)
    validate_config_dict(data)

    version = str(data.get("version", "1"))
    matrix_data = data.get("matrix", {}) or {}

    base_date_val = matrix_data.get("base_date")
    base_date: datetime.datetime | None = None
    if base_date_val:
        try:
            base_date = datetime.datetime.fromisoformat(str(base_date_val).replace("Z", "+00:00"))
        except Exception as e:
            raise ConfigValidationError(f"Invalid base_date ISO format: {base_date_val}") from e

    include_baseline = bool(matrix_data.get("include_baseline", True))
    sessions = [int(s) for s in matrix_data.get("sessions", [])]
    branches = [str(b) for b in matrix_data.get("branches", [])]
    env = {str(k): [str(x) for x in v] for k, v in matrix_data.get("env", {}).items()}

    extra_scenarios: list[Scenario] = []
    for sc in matrix_data.get("extra_scenarios", []):
        sc_name = str(sc["name"])
        sc_sess = int(sc.get("session", 1))
        sc_branch = str(sc.get("branch", "main"))
        sc_clock = str(sc.get("clock", base_date.isoformat() if base_date else DEFAULT_DEMO_DATE.isoformat()))
        sc_env = {str(k): str(v) for k, v in sc.get("env", {}).items()}
        extra_scenarios.append(
            Scenario(
                name=sc_name,
                session=sc_sess,
                branch=sc_branch,
                clock=sc_clock,
                env=sc_env,
            )
        )

    budget_data = data.get("budget")
    budget: TimewarpBudget | None = None
    if budget_data:
        budget = TimewarpBudget(
            max_scenarios=budget_data.get("max_scenarios"),
            max_cost_usd=budget_data.get("max_cost_usd"),
        )

    matrix = TimewarpMatrix(
        base_date=base_date,
        include_baseline=include_baseline,
        sessions=sessions,
        branches=branches,
        env=env,
        extra_scenarios=extra_scenarios,
    )
    return TimewarpConfig(version=version, matrix=matrix, budget=budget)


def load_config(path: Path | str | None = None) -> TimewarpConfig | None:
    """Load configuration from the specified path or standard repository locations.

    If path is None, looks for sentinel.timewarp.yml / sentinel.timewarp.yaml in cwd.
    Returns None if no configuration file is present.
    """
    if path is not None:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Configuration file not found: {p}")
        return parse_config(p.read_text(encoding="utf-8"))

    # Check default file names in cwd
    for candidate in ("sentinel.timewarp.yml", "sentinel.timewarp.yaml"):
        p = Path(candidate)
        if p.is_file():
            return parse_config(p.read_text(encoding="utf-8"))

    return None


def generate_scenarios_from_config(config: TimewarpConfig) -> list[Scenario]:
    """Generate scenario list implied by the configured dimensions and extra scenarios."""
    scenarios: list[Scenario] = []
    base_dt = config.matrix.base_date or DEFAULT_DEMO_DATE
    clock_str = base_dt.isoformat()

    # 1. Custom sessions
    for sess in config.matrix.sessions:
        scenarios.append(
            Scenario(
                name=f"session_{sess}",
                session=sess,
                branch="main",
                clock=clock_str,
                env={"CI": "false"},
            )
        )

    # 2. Custom branches
    for br in config.matrix.branches:
        scenarios.append(
            Scenario(
                name=f"branch_{br}",
                session=1,
                branch=br,
                clock=clock_str,
                env={"CI": "false", "BRANCH": br},
            )
        )

    # 3. Custom environment variables
    for env_var, values in config.matrix.env.items():
        for val in values:
            scenarios.append(
                Scenario(
                    name=f"env_{env_var.lower()}_{val.lower()}",
                    session=1,
                    branch="main",
                    clock=clock_str,
                    env={env_var: val},
                )
            )

    # 4. Explicit extra scenarios
    scenarios.extend(config.matrix.extra_scenarios)
    return scenarios
