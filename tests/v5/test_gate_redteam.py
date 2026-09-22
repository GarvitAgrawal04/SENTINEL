"""Unit test verifying the 30-file red-team evaluation asserts 0 gate escapes."""
from bench.gate_redteam import evaluate


def test_gate_redteam_has_zero_escapes():
    summary = evaluate()
    assert summary["total_tested"] == 30
    assert summary["total_blocked"] == 30
    assert summary["escapes"] == 0
    assert summary["escape_rate"] == 0.0
