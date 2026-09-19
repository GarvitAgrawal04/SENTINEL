"""Plug Sentinel into the team's sentinel-test-corpus harness.

    python scripts/evaluate_layer1.py --scanner /path/to/SENTINEL/bench/corpus/sentinel_adapter.py:scan --split test

Two ways to read a sample (set SENTINEL_CORPUS_MODE):
  repo  (default)  put the file at its realistic project path and scan the folder exactly as `sentinel scan` would.
                   A file Sentinel does not treat as an agent surface comes back CLEAN: that is a SURFACE miss.
  text             hand the text to the engine as an instruction file whatever its name: measures the RULES alone.
"detected" means Sentinel made a CLAIM about the file: COMPROMISED, or SUSPICIOUS with at least one finding that is
not a pure approval request. "An unapproved hook exists, please approve it once" (S14b, S16, S17a, S19) is an inventory
question, not an accusation, so by itself it does not count as a detection (set SENTINEL_CORPUS_INVENTORY=1 to count it).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sentinel import contract, core  # noqa: E402

MODE = os.environ.get("SENTINEL_CORPUS_MODE", "repo")
INVENTORY = {"S14b", "S16", "S17a", "S19"}
COUNT_INVENTORY = os.environ.get("SENTINEL_CORPUS_INVENTORY") == "1"
SPLIT_DIRS = {"benign", "suspicious", "malicious", "obfuscated", "adversarial_holdout"}


def project_path(path: str) -> str:
    """dataset/train/malicious/AGENT-001/.claude/settings.json -> .claude/settings.json"""
    parts = Path(path).as_posix().split("/")
    for i, part in enumerate(parts):
        if part in SPLIT_DIRS and i + 2 <= len(parts) - 1:
            return "/".join(parts[i + 2:])
    return parts[-1]


def scan(path: str, content: str, meta: dict) -> dict:
    if MODE == "text":
        res = contract.scan_text(Path(path).name, content)
        verdict, findings = res["verdict"], [(f["rule_id"], f["severity"]) for f in res["findings"]]
    else:
        with tempfile.TemporaryDirectory(prefix="corpus-") as tmp:
            target = Path(tmp) / project_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            rep = core.scan_repo(Path(tmp), repo_context=False)
        verdict = rep["verdict"]
        findings = [(f["rule"], "high" if f["force"] or f["penalty"] >= 35 else "medium") for v in rep["files"].values() for f in v["findings"]]
    claims = [r for r, _ in findings if COUNT_INVENTORY or r not in INVENTORY]
    return {"detected": verdict == "COMPROMISED" or (verdict == "SUSPICIOUS" and bool(claims)), "rule_ids": [r for r, _ in findings], "indicators": [],
            "severity": {"COMPROMISED": "high", "SUSPICIOUS": "medium"}.get(verdict, "none"), "notes": verdict}
