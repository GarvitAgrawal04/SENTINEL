"""SARIF 2.1.0 exporter for Sentinel Doctor findings."""
from __future__ import annotations

from typing import Any

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"

DOCTOR_RULES: dict[str, dict[str, Any]] = {
    "D001": {
        "id": "D001",
        "name": "BrokenInclude",
        "shortDescription": {"text": "Broken @include / @import directive"},
        "fullDescription": {"text": "The agent file includes or imports a sub-file that does not exist on disk."},
        "defaultConfiguration": {"level": "warning"},
    },
    "D002": {
        "id": "D002",
        "name": "MissingBacktickedPath",
        "shortDescription": {"text": "Backticked file path does not exist on disk"},
        "fullDescription": {"text": "A backticked relative path in instruction text does not match any existing file in the repository."},
        "defaultConfiguration": {"level": "note"},
    },
    "D003": {
        "id": "D003",
        "name": "UndefinedScript",
        "shortDescription": {"text": "Named script or command not defined in project manifests"},
        "fullDescription": {"text": "The instruction references a command or script not found in package.json, Makefile, or pyproject.toml."},
        "defaultConfiguration": {"level": "note"},
    },
    "D004": {
        "id": "D004",
        "name": "DuplicateRule",
        "shortDescription": {"text": "Duplicate instruction rule detected"},
        "fullDescription": {"text": "Identical or semantically equivalent rule appears multiple times in the file."},
        "defaultConfiguration": {"level": "note"},
    },
    "D005": {
        "id": "D005",
        "name": "GuardrailContradiction",
        "shortDescription": {"text": "Instruction contradicts a guardrail in the same load graph"},
        "fullDescription": {"text": "A rule orders an action that is explicitly prohibited by a negative constraint in the load graph."},
        "defaultConfiguration": {"level": "warning"},
    },
    "D006": {
        "id": "D006",
        "name": "FileTokenBudget",
        "shortDescription": {"text": "Agent file exceeds token budget"},
        "fullDescription": {"text": "File length exceeds recommended context window budget (1500 tokens)."},
        "defaultConfiguration": {"level": "note"},
    },
    "D007": {
        "id": "D007",
        "name": "SecretShapedValue",
        "shortDescription": {"text": "Secret-shaped value in agent instruction file"},
        "fullDescription": {"text": "Detected high-entropy token or hardcoded credential in an instruction file."},
        "defaultConfiguration": {"level": "warning"},
    },
    "D008": {
        "id": "D008",
        "name": "AnsiEscapeSequence",
        "shortDescription": {"text": "ANSI or terminal escape sequences in instruction text"},
        "fullDescription": {"text": "Instruction text contains terminal control or escape codes that could confuse or inject into agent terminals."},
        "defaultConfiguration": {"level": "warning"},
    },
}


def to_sarif(all_findings: dict[str, list[dict[str, Any]]], version: str = "0.9.1") -> dict[str, Any]:
    """Convert Sentinel Doctor findings dictionary into a valid SARIF v2.1.0 document."""
    results = []
    used_rule_ids: set[str] = set()

    for file_uri, findings in all_findings.items():
        for f in findings:
            rule_id = f.get("id", "UNKNOWN")
            used_rule_ids.add(rule_id)

            kind = f.get("kind", "WARNING")
            level = "note" if kind == "OBSERVATION" else "warning"

            res_obj: dict[str, Any] = {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": f.get("message", "")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": file_uri},
                            "region": {
                                "startLine": max(1, f.get("line", 1)),
                                "startColumn": 1,
                            },
                        }
                    }
                ],
            }

            if f.get("fix") and f["fix"].get("replacement") is not None:
                res_obj["fixes"] = [
                    {
                        "description": {"text": f"Apply safe fix: {f['fix'].get('description', 'remove or update line')}"},
                        "fileChanges": [
                            {
                                "artifactLocation": {"uri": file_uri},
                                "replacements": [
                                    {
                                        "deletedRegion": {
                                            "startLine": max(1, f.get("line", 1)),
                                            "startColumn": 1,
                                        },
                                        "insertedContent": {"text": f["fix"]["replacement"]},
                                    }
                                ],
                            }
                        ],
                    }
                ]

            results.append(res_obj)

    rules = [DOCTOR_RULES.get(rid, {"id": rid, "name": rid, "shortDescription": {"text": rid}}) for rid in sorted(used_rule_ids)]

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Sentinel Doctor",
                        "version": version,
                        "informationUri": "https://github.com/GarvitAgrawal04/SENTINEL",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
