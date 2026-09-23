"""Tests for Rewrite Gate red-team: 30 poisoned injection files must yield 0 escapes."""
from __future__ import annotations

from pathlib import Path
from sentinel.doctor import gate

ROOT = Path(__file__).resolve().parents[2]
GATE_FIXTURES = ROOT / "tests" / "fixtures" / "gate_redteam"


def test_gate_redteam_thirty_poisoning_files_zero_escapes():
    """All 30 poisoned instruction rewrites must be blocked with 0 escapes."""
    attack_files = sorted(GATE_FIXTURES.glob("attack_*.md"))
    assert len(attack_files) >= 30, f"Expected 30 redteam attack fixtures, found {len(attack_files)}"

    escapes = []
    for f_path in attack_files:
        content = f_path.read_text(encoding="utf-8")
        res = gate.check(content, filename=f_path.name)

        passed = res.get("passed", False)
        status = res.get("status", "BLOCKED")

        if passed or status != "BLOCKED":
            escapes.append((f_path.name, res))

    assert not escapes, f"Gate escapes detected! {escapes}"
