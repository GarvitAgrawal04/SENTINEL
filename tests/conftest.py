"""Tests must not depend on, or be slowed down by, the developer's own .env or shell.

Found the hard way: with a real .env present, SENTINEL_LLM_RPM=20 paced the fake local model at one request every
three seconds and the suite took minutes. Worse, a real key could have been used for real API calls.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _hermetic_environment(monkeypatch, tmp_path):
    for name in list(os.environ):
        if name.startswith("SENTINEL_LLM_") or name in ("SENTINEL_SIGNING_KEY", "SENTINEL_BASE", "SENTINEL_COMMENT"):
            monkeypatch.delenv(name, raising=False)
    from sentinel import envfile
    monkeypatch.setattr(envfile, "OWN_ENV", tmp_path / "no-such.env")      # never read the developer's real .env
