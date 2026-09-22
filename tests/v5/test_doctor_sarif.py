"""Tests for sentinel doctor --format sarif."""
import json
from pathlib import Path
from sentinel import cli
from sentinel.doctor import sarif


def test_doctor_to_sarif_structure():
    findings = {
        "CLAUDE.md": [
            {
                "id": "D001",
                "line": 5,
                "message": "Broken @include / @import: 'missing.md' does not exist on disk",
                "fix": {"description": "Remove broken include", "replacement": ""},
                "kind": "WARNING",
            },
            {
                "id": "D004",
                "line": 12,
                "message": "Duplicate rule: 'run tests' (first defined on line 4)",
                "fix": {"description": "Remove duplicate rule", "replacement": ""},
                "kind": "OBSERVATION",
            }
        ]
    }
    data = sarif.to_sarif(findings, version="0.9.1")
    assert data["$schema"] == sarif.SARIF_SCHEMA
    assert data["version"] == "2.1.0"
    assert len(data["runs"]) == 1
    run = data["runs"][0]
    assert run["tool"]["driver"]["name"] == "Sentinel Doctor"
    assert run["tool"]["driver"]["version"] == "0.9.1"

    results = run["results"]
    assert len(results) == 2

    # Check D001 finding (WARNING -> warning)
    d001 = next(r for r in results if r["ruleId"] == "D001")
    assert d001["level"] == "warning"
    assert d001["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "CLAUDE.md"
    assert d001["locations"][0]["physicalLocation"]["region"]["startLine"] == 5
    assert len(d001["fixes"]) == 1

    # Check D004 finding (OBSERVATION -> note)
    d004 = next(r for r in results if r["ruleId"] == "D004")
    assert d004["level"] == "note"
    assert d004["locations"][0]["physicalLocation"]["region"]["startLine"] == 12


def test_cli_doctor_sarif_command(capsys, monkeypatch):
    fixture = Path("tests/fixtures/doctor/d001_broken_include.md")
    code = cli.main(["doctor", str(fixture), "--format", "sarif"])
    assert code == 1
    out, err = capsys.readouterr()
    parsed = json.loads(out)
    assert parsed["version"] == "2.1.0"
    assert parsed["runs"][0]["tool"]["driver"]["name"] == "Sentinel Doctor"
    assert any(r["ruleId"] == "D001" for r in parsed["runs"][0]["results"])
