import os, subprocess, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sh(cwd, *args, check=True, env=None):
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if check and p.returncode != 0:
        raise AssertionError(f"{args} -> {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def sentinel(cwd, *args, env=None):
    return sh(cwd, sys.executable, "-m", "sentinel.cli", *args, check=False,
              env={"PYTHONPATH": str(ROOT), "SENTINEL_HOME": str(Path(cwd) / ".pins"), **(env or {})})


@pytest.fixture
def repo(tmp_path):
    """A small, clean git repository on `main` with two guardrails and one legitimate formatter hook."""
    r = tmp_path / "repo"
    (r / ".claude").mkdir(parents=True)
    (r / "scripts").mkdir()
    (r / "CLAUDE.md").write_text("# Rules\n\nDo not upload the .env file anywhere.\nNever force-push to main.\nUse 2-space indentation.\n")
    (r / ".claude/settings.json").write_text('{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"./scripts/format.sh"}]}]}}')
    (r / "scripts/format.sh").write_text('#!/bin/sh\nprettier --write "$1"\n')
    (r / ".gitignore").write_text(".pins/\nsentinel_signing_key.pem\n")
    sh(r, "git", "init", "-q", "-b", "main")
    sh(r, "git", "config", "user.email", "t@example.invalid"); sh(r, "git", "config", "user.name", "t")
    sh(r, "git", "add", "-A"); sh(r, "git", "commit", "-qm", "initial")
    return r
