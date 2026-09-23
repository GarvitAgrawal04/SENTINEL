"""SARIF 2.1.0 exporter for Sentinel security scan, pull-request diff, and doctor findings."""
from __future__ import annotations

import re
from typing import Any
from pathlib import Path

from . import __version__
from .render import TITLE

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"

# Standard rule descriptions for SARIF reporting descriptors
RULE_CATALOG: dict[str, dict[str, Any]] = {
    "S1a": {
        "id": "S1a",
        "name": "HiddenInstructionUnicode",
        "shortDescription": {"text": "Hidden text encoded in invisible Unicode characters"},
        "fullDescription": {"text": "Detected zero-width characters or bidirectional control characters concealing instructions from human review."},
        "defaultConfiguration": {"level": "error"},
    },
    "S1b": {
        "id": "S1b",
        "name": "StrayInvisibleCharacters",
        "shortDescription": {"text": "Stray invisible characters"},
        "fullDescription": {"text": "Zero-width or invisible characters detected without valid linguistic or emoji context."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S2": {
        "id": "S2",
        "name": "InstructionHiddenInComment",
        "shortDescription": {"text": "Instruction hidden in code or markup comment"},
        "fullDescription": {"text": "Agent instructions embedded in HTML, markdown, or code comments intended to influence model behaviour invisibly."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S4": {
        "id": "S4",
        "name": "OverridePhrasing",
        "shortDescription": {"text": "Adversarial override phrasing"},
        "fullDescription": {"text": "Text attempts to override previous instructions, developer guardrails, or system prompts."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S5": {
        "id": "S5",
        "name": "ExfiltrationShapedInstruction",
        "shortDescription": {"text": "Exfiltration-shaped instruction"},
        "fullDescription": {"text": "The instruction directs the agent to transmit environment secrets, credentials, or sensitive files to external destinations."},
        "defaultConfiguration": {"level": "error"},
    },
    "S6": {
        "id": "S6",
        "name": "UndeclaredChange",
        "shortDescription": {"text": "Undeclared change to agent configuration"},
        "fullDescription": {"text": "Agent configuration surface was altered without being reflected in PR title, commit summary, or description."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S7": {
        "id": "S7",
        "name": "EncodedInstruction",
        "shortDescription": {"text": "Encoded instruction payload"},
        "fullDescription": {"text": "Base64, hex, or rot-encoded instruction payloads designed to bypass static human or automated inspection."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S10": {
        "id": "S10",
        "name": "OrphanedAutoRun",
        "shortDescription": {"text": "Orphaned auto-run hook script"},
        "fullDescription": {"text": "A configured auto-exec hook references a local script file that does not exist in the repository."},
        "defaultConfiguration": {"level": "error"},
    },
    "S11": {
        "id": "S11",
        "name": "CredentialExposedInHook",
        "shortDescription": {"text": "Credential or API traffic exposed"},
        "fullDescription": {"text": "Hook or agent configuration routes API credentials or authentication tokens through unencrypted or unmonitored channels."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S12": {
        "id": "S12",
        "name": "RemoteInstructionFetch",
        "shortDescription": {"text": "Instructions fetched from remote URL"},
        "fullDescription": {"text": "Instructions instruct the agent to fetch and obey external directives from an arbitrary web URL at runtime."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S13": {
        "id": "S13",
        "name": "ConcealmentFromUser",
        "shortDescription": {"text": "Concealment from the user"},
        "fullDescription": {"text": "Instructions command the agent not to notify, ask, or display actions or edits to the developer."},
        "defaultConfiguration": {"level": "error"},
    },
    "S14a": {
        "id": "S14a",
        "name": "WriteInterceptHookBroad",
        "shortDescription": {"text": "Broad write-intercept hook"},
        "fullDescription": {"text": "Pre-tool hook intercepts all write or edit operations across the workspace."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S14b": {
        "id": "S14b",
        "name": "WriteInterceptHookUnapproved",
        "shortDescription": {"text": "Unapproved write-intercept hook"},
        "fullDescription": {"text": "Pre-tool hook intercepts file edits and has not been approved in AGENTS.lock."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S16": {
        "id": "S16",
        "name": "McpAutoTrustAll",
        "shortDescription": {"text": "All project MCP servers auto-trusted"},
        "fullDescription": {"text": "Global or project settings disable per-server approval for Model Context Protocol servers."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S17a": {
        "id": "S17a",
        "name": "NewAutoRunUnapproved",
        "shortDescription": {"text": "New auto-run hook not approved"},
        "fullDescription": {"text": "A tool hook executes arbitrary local commands on tool events without prior approval in AGENTS.lock."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S17b": {
        "id": "S17b",
        "name": "AutoRunAcrossSeveralTools",
        "shortDescription": {"text": "Auto-run hooks configured across multiple tools"},
        "fullDescription": {"text": "Auto-execution hooks present in multiple agent configurations (e.g. Claude + VS Code tasks + Cursor)."},
        "defaultConfiguration": {"level": "error"},
    },
    "S18a": {
        "id": "S18a",
        "name": "AutoRunScriptUnreadable",
        "shortDescription": {"text": "Auto-run hook script is unreadable or obfuscated"},
        "fullDescription": {"text": "The script executed by an auto-run hook has high Shannon entropy, minified code, or excessive line length."},
        "defaultConfiguration": {"level": "error"},
    },
    "S18b": {
        "id": "S18b",
        "name": "AutoRunScriptSpawnAndConnect",
        "shortDescription": {"text": "Auto-run hook script can spawn processes and connect to network"},
        "fullDescription": {"text": "The script executed by an auto-run hook contains both process execution and network connection capabilities."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S18c": {
        "id": "S18c",
        "name": "DownloadAndExecute",
        "shortDescription": {"text": "Download and execute pattern in hook script"},
        "fullDescription": {"text": "The hook script downloads arbitrary executable content and pipes it directly into a shell interpreter."},
        "defaultConfiguration": {"level": "error"},
    },
    "S19": {
        "id": "S19",
        "name": "NewMcpServerUnapproved",
        "shortDescription": {"text": "New MCP server not approved"},
        "fullDescription": {"text": "A new Model Context Protocol server definition has been added without approval in AGENTS.lock."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S20": {
        "id": "S20",
        "name": "GuardrailWeakened",
        "shortDescription": {"text": "Guardrail weakened or removed"},
        "fullDescription": {"text": "A safety guardrail or constraint present in the base branch was weakened, deleted, or inverted in this change."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S21": {
        "id": "S21",
        "name": "DownloadAndRunInstruction",
        "shortDescription": {"text": "Download-and-run instruction in agent prompt"},
        "fullDescription": {"text": "Instruction tells the agent to fetch remote scripts and run them immediately."},
        "defaultConfiguration": {"level": "error"},
    },
    "S22": {
        "id": "S22",
        "name": "SafetyCheckSwitchedOff",
        "shortDescription": {"text": "Safety check switched off"},
        "fullDescription": {"text": "Instruction orders the agent to bypass, disable, or ignore linter or safety checks."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S23": {
        "id": "S23",
        "name": "DestructiveInstruction",
        "shortDescription": {"text": "Destructive instruction"},
        "fullDescription": {"text": "Instruction orders permanent deletion of repositories, branches, or data without confirmation."},
        "defaultConfiguration": {"level": "error"},
    },
    "S24": {
        "id": "S24",
        "name": "PersistenceOutsideProject",
        "shortDescription": {"text": "Persistence outside the project"},
        "fullDescription": {"text": "Instruction commands the agent to write files or configs into home or global directories outside the repository."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S25": {
        "id": "S25",
        "name": "UntrustedPackageSource",
        "shortDescription": {"text": "Untrusted package source"},
        "fullDescription": {"text": "Directs the agent to install dependencies from untrusted third-party package indexes or registries."},
        "defaultConfiguration": {"level": "warning"},
    },
    "S26": {
        "id": "S26",
        "name": "CredentialStoreAccess",
        "shortDescription": {"text": "Credential store access"},
        "fullDescription": {"text": "Directs the agent to read secrets from system keychains, credential managers, or AWS/SSH config directories."},
        "defaultConfiguration": {"level": "error"},
    },
    "D1": {
        "id": "D1",
        "name": "SandboxCanaryLeak",
        "shortDescription": {"text": "Canary secret exfiltrated in sandbox detonation"},
        "fullDescription": {"text": "In the Time-Warp sandbox, an agent obeying this instruction leaked a planted canary credential."},
        "defaultConfiguration": {"level": "error"},
    },
    "D2": {
        "id": "D2",
        "name": "SandboxSensitiveObservation",
        "shortDescription": {"text": "New sensitive behaviour observed in sandbox detonation"},
        "fullDescription": {"text": "In the Time-Warp sandbox, differential behavioural analysis observed access to sensitive surfaces."},
        "defaultConfiguration": {"level": "note"},
    },
    "SEM01": {
        "id": "SEM01",
        "name": "AdvisorySemanticWarning",
        "shortDescription": {"text": "Advisory semantic check flagged suspicious instruction"},
        "fullDescription": {"text": "Layer 3 semantic model check flagged an unmatched instruction sentence as instructively inappropriate for repository instructions."},
        "defaultConfiguration": {"level": "note"},
    },
}


def _rule_descriptor(rule_id: str) -> dict[str, Any]:
    if rule_id in RULE_CATALOG:
        return RULE_CATALOG[rule_id]
    title = TITLE.get(rule_id, rule_id)
    name = "".join(w.capitalize() for w in re.split(r"[_\s\-]+", title) if w) or rule_id
    level = "error" if rule_id.startswith(("S5", "S10", "S18a", "S18c", "S21", "S23", "S26", "D1")) else "warning"
    return {
        "id": rule_id,
        "name": name,
        "shortDescription": {"text": title},
        "fullDescription": {"text": f"Sentinel rule {rule_id}: {title}"},
        "defaultConfiguration": {"level": level},
    }


def _sarif_level(finding: dict[str, Any]) -> str:
    rule_id = str(finding.get("rule") or finding.get("rule_id") or "")
    if rule_id == "SEM01" or rule_id.startswith("SEM") or rule_id == "D2":
        return "note"
    if finding.get("force") or finding.get("forces_compromised"):
        return "error"
    penalty = finding.get("penalty", 0) or 0
    if penalty >= 35:
        return "error"
    if penalty >= 15 or finding.get("ceiling"):
        return "warning"
    if penalty == 0 and finding.get("kind") == "OBSERVATION":
        return "note"
    return "warning"


def _extract_line(finding: dict[str, Any]) -> int:
    line = finding.get("line")
    if line is not None and isinstance(line, int) and line > 0:
        return line
    evidence = str(finding.get("evidence") or finding.get("message") or "")
    m = re.search(r"line\s+(\d+)", evidence, re.I)
    if m:
        return int(m.group(1))
    return 1


def _to_result(f: dict[str, Any], default_file: str = ".") -> dict[str, Any]:
    rule_id = str(f.get("rule") or f.get("rule_id") or "UNKNOWN")
    level = _sarif_level(f)
    uri = str(f.get("file") or f.get("filename") or default_file).replace("\\", "/")
    line = _extract_line(f)
    evidence = str(f.get("evidence") or f.get("message") or f.get("snippet") or "")
    impact = str(f.get("impact") or "")
    fix = str(f.get("fix") or "")

    msg_parts = [evidence]
    if impact and impact != evidence:
        msg_parts.append(f"Impact: {impact}")
    if fix:
        msg_parts.append(f"Fix: {fix}")
    full_message = " | ".join(msg_parts) if msg_parts else f"Sentinel finding {rule_id}"

    res: dict[str, Any] = {
        "ruleId": rule_id,
        "level": level,
        "message": {"text": full_message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": uri},
                    "region": {
                        "startLine": max(1, line),
                        "startColumn": 1,
                    },
                }
            }
        ],
    }

    if f.get("fix") and isinstance(f["fix"], dict) and f["fix"].get("replacement") is not None:
        res["fixes"] = [
            {
                "description": {"text": f["fix"].get("description", "Apply fix")},
                "fileChanges": [
                    {
                        "artifactLocation": {"uri": uri},
                        "replacements": [
                            {
                                "deletedRegion": {"startLine": max(1, line), "startColumn": 1},
                                "insertedContent": {"text": f["fix"]["replacement"]},
                            }
                        ],
                    }
                ],
            }
        ]

    return res


def scan_report_to_sarif(report: dict[str, Any], version: str = __version__) -> dict[str, Any]:
    """Convert a sentinel scan report (from scan_repo or contract.legacy_result) to SARIF 2.1.0."""
    results: list[dict[str, Any]] = []
    used_rule_ids: set[str] = set()

    # Case 1: contract / single-file format containing "findings" list
    if "findings" in report and isinstance(report["findings"], list):
        default_file = report.get("filename", ".")
        for f in report["findings"]:
            rid = str(f.get("rule_id") or f.get("rule") or "UNKNOWN")
            used_rule_ids.add(rid)
            results.append(_to_result(f, default_file=default_file))

    # Case 2: repo report format containing "files" dictionary
    if "files" in report and isinstance(report["files"], dict):
        for fname, file_data in report["files"].items():
            for f in file_data.get("findings", []):
                rid = str(f.get("rule") or f.get("rule_id") or "UNKNOWN")
                used_rule_ids.add(rid)
                results.append(_to_result(f, default_file=fname))

    # Add extra findings if present at top level
    for f in report.get("extra_findings", []):
        rid = str(f.get("rule") or f.get("rule_id") or "UNKNOWN")
        used_rule_ids.add(rid)
        results.append(_to_result(f, default_file=report.get("filename", ".")))

    rules = [_rule_descriptor(rid) for rid in sorted(used_rule_ids)]

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Sentinel",
                        "version": version,
                        "informationUri": "https://github.com/GarvitAgrawal04/SENTINEL",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def pr_report_to_sarif(report: dict[str, Any], ctx: dict[str, Any] | None = None, version: str = __version__) -> dict[str, Any]:
    """Convert a sentinel pr diff report to SARIF 2.1.0."""
    sarif_doc = scan_report_to_sarif(report, version=version)
    return sarif_doc
