"""Tests for pre-commit hooks configuration (.pre-commit-hooks.yaml)."""
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
PRECOMMIT_FILE = ROOT / ".pre-commit-hooks.yaml"


def test_precommit_hooks_definition():
    assert PRECOMMIT_FILE.is_file(), f".pre-commit-hooks.yaml missing at {PRECOMMIT_FILE}"
    hooks = yaml.safe_load(PRECOMMIT_FILE.read_text(encoding="utf-8"))

    assert isinstance(hooks, list), "Expected list of hook configurations"
    hook_ids = {h.get("id") for h in hooks}

    assert "sentinel-scan" in hook_ids
    assert "sentinel-doctor" in hook_ids

    scan_hook = next(h for h in hooks if h["id"] == "sentinel-scan")
    assert scan_hook["entry"] == "sentinel scan"
    assert scan_hook["language"] == "python"

    doc_hook = next(h for h in hooks if h["id"] == "sentinel-doctor")
    assert doc_hook["entry"] == "sentinel doctor"
    assert doc_hook["language"] == "python"
    assert doc_hook["pass_filenames"] is True
