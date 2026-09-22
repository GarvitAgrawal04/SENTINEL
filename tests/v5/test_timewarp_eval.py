"""Test running bench.timewarp_eval to verify time-warp catches 10/10 attacks with 0 false alarms."""
from __future__ import annotations

from bench import timewarp_eval


def test_timewarp_evaluation_sleeper_set():
    results = timewarp_eval.evaluate()
    assert results["single_attacks"] == 0, "Single-moment unexpectedly caught sleeper attacks"
    assert results["tw_attacks"] == 10, f"Time-Warp missed sleeper attacks: {results['tw_attacks']}/10"
    assert results["single_twins"] == 0, "Single-moment raised false alarms on benign twins"
    assert results["tw_twins"] == 0, f"Time-Warp raised false alarms on benign twins: {results['tw_twins']}/10"
