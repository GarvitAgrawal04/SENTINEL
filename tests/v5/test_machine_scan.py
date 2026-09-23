"""Tests for sentinel scan --machine: discovery, consent gating, and zero-execution invariant."""
from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path
import pytest

from sentinel import cli, machine


@pytest.fixture
def mock_home(tmp_path):
    """Create a simulated developer home directory with agent configurations."""
    home = tmp_path / "userhome"
    home.mkdir()

    # 1. Claude configs
    claude_dir = home / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit",
                    "hooks": [{"type": "command", "command": "./scripts/hook.sh"}]
                }
            ]
        }
    }), encoding="utf-8")
    (claude_dir / "CLAUDE.md").write_text("# Claude global rules\nDo not push without tests.\n", encoding="utf-8")

    # 2. Cursor configs
    (home / ".cursorrules").write_text("# Cursor rules\nAlways use typescript.\n", encoding="utf-8")

    # 3. VS Code configs
    appdata = home / "AppData" / "Roaming"
    vscode_user = appdata / "Code" / "User"
    vscode_user.mkdir(parents=True)
    (vscode_user / "tasks.json").write_text(json.dumps({
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Auto Setup",
                "type": "shell",
                "command": "node ./setup.js",
                "runOptions": {"runOn": "folderOpen"}
            }
        ]
    }), encoding="utf-8")

    # 4. Gemini configs
    gemini_dir = home / ".gemini"
    gemini_dir.mkdir()
    (gemini_dir / "GEMINI.md").write_text("# Gemini CLI rules\nFollow conventions.\n", encoding="utf-8")

    return home, {"APPDATA": str(appdata)}


def test_discover_machine_targets(mock_home):
    home, env = mock_home
    targets = machine.discover_machine_targets(home=home, env=env)

    tools = {t.tool for t in targets}
    assert "claude" in tools
    assert "cursor" in tools
    assert "vscode" in tools
    assert "gemini" in tools

    paths = [str(t.path) for t in targets]
    assert any(".claude" in p and "settings.json" in p for p in paths)
    assert any(".cursorrules" in p for p in paths)
    assert any("tasks.json" in p for p in paths)
    assert any("GEMINI.md" in p for p in paths)


def test_consent_gate_behavior():
    # 1. auto_yes returns True unconditionally
    assert machine.prompt_consent(auto_yes=True) is True

    # 2. non-interactive without auto_yes returns False
    err_stream = io.StringIO()
    assert machine.prompt_consent(interactive=False, auto_yes=False, out_stream=err_stream) is False
    assert "requires user consent" in err_stream.getvalue()

    # 3. interactive with 'y' input returns True
    in_yes = io.StringIO("y\n")
    out = io.StringIO()
    assert machine.prompt_consent(interactive=True, auto_yes=False, in_stream=in_yes, out_stream=out) is True
    assert "Proceed with machine scan?" in out.getvalue()

    # 4. interactive with 'n' input returns False
    in_no = io.StringIO("n\n")
    assert machine.prompt_consent(interactive=True, auto_yes=False, in_stream=in_no, out_stream=out) is False


def test_scan_machine_static_analysis(mock_home):
    home, env = mock_home
    targets = machine.discover_machine_targets(home=home, env=env)
    rep = machine.scan_machine(targets)

    assert rep["machine_scan"] is True
    assert rep["targets_discovered"] == len(targets)
    assert rep["verdict"] in ("CLEAN", "SUSPICIOUS", "COMPROMISED")

    # The tasks.json has a folderOpen task, which triggers S17a (SUSPICIOUS)
    assert rep["verdict"] == "SUSPICIOUS"
    all_findings = [f for fdata in rep["files"].values() for f in fdata.get("findings", [])]
    assert any(f.get("rule") == "S17a" for f in all_findings)


def test_zero_execution_invariant(mock_home, monkeypatch):
    """SECURITY INVARIANT: Machine scan must strictly NEVER execute or spawn any code it finds."""
    home, env = mock_home

    # Add an executable payload in home that screams if executed
    exploit_script = home / "exploit.sh"
    exploit_script.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")

    # Mock all process execution APIs
    exec_called = []

    def mock_popen(*args, **kwargs):
        exec_called.append(("popen", args))
        raise RuntimeError("SECURITY VIOLATION: Subprocess spawned during static scan!")

    def mock_run(*args, **kwargs):
        exec_called.append(("run", args))
        raise RuntimeError("SECURITY VIOLATION: Subprocess run during static scan!")

    def mock_system(*args, **kwargs):
        exec_called.append(("system", args))
        raise RuntimeError("SECURITY VIOLATION: os.system called during static scan!")

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(os, "system", mock_system)

    # Run machine scan across all targets
    targets = machine.discover_machine_targets(home=home, env=env)
    rep = machine.scan_machine(targets)

    # Assert 0 execution calls occurred
    assert len(exec_called) == 0, f"Expected 0 execution calls, got: {exec_called}"
    assert rep["machine_scan"] is True


def test_cli_scan_machine_headless_consent_failure(capsys):
    # Headless without --yes exits with 1
    code = cli.main(["scan", "--machine"])
    assert code == 1
