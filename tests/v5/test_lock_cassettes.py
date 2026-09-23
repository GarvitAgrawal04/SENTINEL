"""Unit tests for pinning test cassettes into AGENTS.lock (Day 5 T4)."""

import json
from pathlib import Path

import jsonschema
import pytest

from sentinel import core, lock

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "spec" / "agents-lock.schema.json").read_text(encoding="utf-8"))


def test_discover_test_cassettes():
    """Verify that discover_test_cassettes finds all test fixture cassettes."""
    cassettes = lock.discover_test_cassettes(ROOT)
    assert len(cassettes) >= 20
    paths = [p.name for p in cassettes]
    assert "cassette.json" in paths or any(p.endswith(".cassette.json") for p in paths)


def test_lock_schema_validation_with_cassettes(tmp_path):
    """Verify that a lock containing pinned cassettes conforms strictly to the schema."""
    fake_fixture = tmp_path / "tests" / "fixtures" / "sleeper"
    fake_fixture.mkdir(parents=True)
    cassette_file = fake_fixture / "cassette.json"
    cassette_file.write_text(json.dumps({"entries": {"abc": {"role": "assistant"}}}), encoding="utf-8")

    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text("# Project Instructions\nNever force-push to main.\n", encoding="utf-8")

    rep = core.scan_repo(tmp_path, {})
    lock_data = lock.build_lock(tmp_path, rep, {}, pin_cassettes=True)

    assert "cassettes" in lock_data
    rel_p = "tests/fixtures/sleeper/cassette.json"
    assert rel_p in lock_data["cassettes"]
    assert lock_data["cassettes"][rel_p]["sha256"] == core.sha256_file(cassette_file)

    # Validate against JSON schema
    jsonschema.validate(instance=lock_data, schema=SCHEMA)


def test_verify_detects_tampered_cassette(tmp_path):
    """Assert that modifying a pinned cassette causes lock verification to fail."""
    # Setup key pair
    priv_path = tmp_path / "key.pem"
    pub_path = tmp_path / lock.PUBKEY
    pub_fp = lock.keygen(priv_path, pub_path)
    priv_bytes = priv_path.read_bytes()
    pub_bytes = pub_path.read_bytes()

    # Setup files and cassette
    fake_fixture = tmp_path / "tests" / "fixtures" / "demo"
    fake_fixture.mkdir(parents=True)
    cassette_file = fake_fixture / "cassette.json"
    cassette_file.write_text(json.dumps({"entries": {"step_1": {"role": "assistant"}}}), encoding="utf-8")

    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text("# Agent\nDo not upload secrets.\n", encoding="utf-8")

    # Build and sign lock
    rep = core.scan_repo(tmp_path, {})
    lock_data = lock.build_lock(tmp_path, rep, {}, pin_cassettes=True)
    lock.write_lock(tmp_path, lock_data, private_pem=priv_bytes)

    # 1. Untampered verification must pass
    res_clean = lock.verify(tmp_path, public_pem=pub_bytes)
    assert res_clean["ok"] is True
    assert res_clean["tampered_cassettes"] == []
    assert res_clean["missing_cassettes"] == []

    # 2. Tampering with cassette content must fail verification
    cassette_file.write_text(json.dumps({"entries": {"step_1": {"role": "malicious"}}}), encoding="utf-8")
    res_tampered = lock.verify(tmp_path, public_pem=pub_bytes)
    assert res_tampered["ok"] is False
    assert "tests/fixtures/demo/cassette.json" in res_tampered["tampered_cassettes"]

    # 3. Restoring content recovers verification pass
    cassette_file.write_text(json.dumps({"entries": {"step_1": {"role": "assistant"}}}), encoding="utf-8")
    assert lock.verify(tmp_path, public_pem=pub_bytes)["ok"] is True

    # 4. Deleting cassette reports missing and fails verification
    cassette_file.unlink()
    res_missing = lock.verify(tmp_path, public_pem=pub_bytes)
    assert res_missing["ok"] is False
    assert "tests/fixtures/demo/cassette.json" in res_missing["missing_cassettes"]
