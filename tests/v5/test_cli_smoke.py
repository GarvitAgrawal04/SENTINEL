"""Smoke tests for every sentinel CLI subcommand.

Asserts that every subcommand:
  1. Responds to --help with exit code 0.
  2. Runs cleanly on a trivial input without crashing, asserting its exit code.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT, sentinel, sh

SUBCOMMANDS = [
    "scan",
    "run",
    "pr",
    "init",
    "approve",
    "sign",
    "verify",
    "keygen",
    "apikey",
    "detonate",
    "fixtures",
    "selftest",
    "timewarp",
    "doctor",
]


@pytest.mark.parametrize("subcmd", SUBCOMMANDS)
def test_subcommand_help_exits_zero(tmp_path: Path, subcmd: str):
    r = sentinel(tmp_path, subcmd, "--help")
    assert r.returncode == 0, f"sentinel {subcmd} --help failed:\n{r.stderr}"
    assert "usage: sentinel" in r.stdout or f"sentinel {subcmd}" in r.stdout or "options:" in r.stdout or "-h" in r.stdout


def test_cli_scan_trivial(tmp_path: Path):
    r = sentinel(tmp_path, "scan", str(tmp_path))
    assert r.returncode == 0


def test_cli_run_trivial(tmp_path: Path):
    r = sentinel(tmp_path, "run", "--path", str(tmp_path), "--", sys.executable, "-c", "pass")
    assert r.returncode == 0


def test_cli_init_and_approve_trivial(tmp_path: Path):
    r = sentinel(tmp_path, "init", "--path", str(tmp_path))
    assert r.returncode == 0
    r_app = sentinel(tmp_path, "approve", "--path", str(tmp_path))
    assert r_app.returncode == 0


def test_cli_keygen_sign_verify_trivial(tmp_path: Path):
    key = tmp_path / "test_key.pem"
    r_key = sentinel(tmp_path, "keygen", "--path", str(tmp_path), "--private", str(key))
    assert r_key.returncode == 0
    sentinel(tmp_path, "init", "--path", str(tmp_path))
    r_sign = sentinel(tmp_path, "sign", "--path", str(tmp_path), "--key", str(key))
    assert r_sign.returncode == 0
    r_ver = sentinel(tmp_path, "verify", "--path", str(tmp_path))
    assert r_ver.returncode == 0


def test_cli_apikey_show_trivial(tmp_path: Path):
    r = sentinel(tmp_path, "apikey", "--show")
    assert r.returncode == 0


def test_cli_detonate_mock_trivial(tmp_path: Path):
    sample = tmp_path / "CLAUDE.md"
    sample.write_text("# Project Guidelines\n\nRun pytest before pushing.\n", encoding="utf-8")
    r = sentinel(tmp_path, "detonate", str(sample), "--mock")
    assert r.returncode == 0


def test_cli_fixtures_trivial(tmp_path: Path):
    out_dir = tmp_path / "fx_out"
    r = sentinel(tmp_path, "fixtures", str(out_dir))
    assert r.returncode == 0
    assert out_dir.is_dir()


def test_cli_selftest_trivial(tmp_path: Path):
    r = sentinel(tmp_path, "selftest")
    assert r.returncode == 0


def test_cli_pr_trivial(tmp_path: Path):
    repo = tmp_path / "git_repo"
    sh(tmp_path, "git", "init", "-q", "-b", "main", str(repo))
    sh(repo, "git", "config", "user.email", "smoke@example.invalid")
    sh(repo, "git", "config", "user.name", "SmokeTest")
    (repo / "README.md").write_text("# Smoke Test Repo\n", encoding="utf-8")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-qm", "initial commit")
    r = sentinel(repo, "pr", "--path", str(repo), "--base", "HEAD")
    assert r.returncode == 0
    assert "sentinel-agent-behaviour-diff" in r.stdout


def test_cli_timewarp_run_trivial():
    fixture_dir = ROOT / "tests" / "fixtures" / "sleeper"
    agents_file = fixture_dir / "AGENTS.md"
    r = sentinel(ROOT, "timewarp", "run", str(agents_file), "--replay", str(fixture_dir))
    # Sleeper finding correctly triggers exit code 1 (SUSPICIOUS)
    assert r.returncode == 1
    assert "sentinel timewarp" in r.stdout
    assert "SUSPICIOUS" in r.stdout


def test_cli_doctor_trivial(tmp_path: Path):
    clean_file = tmp_path / "CLAUDE.md"
    clean_file.write_text("# Clean project rules\nRun tests before commit.\n", encoding="utf-8")
    r = sentinel(tmp_path, "doctor", str(clean_file))
    assert r.returncode == 0
    assert "no instruction hygiene issues found" in r.stdout


