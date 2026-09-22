"""Unit tests for the doctor token delta benchmark across 50 public agent files."""
from bench.doctor_token_delta import evaluate


def test_doctor_token_delta_50_files():
    summary = evaluate(assert_median_non_positive=True)

    assert summary["files_tested"] == 50
    assert summary["files_with_fixes"] > 0
    assert summary["total_fixes_applied"] > 0
    assert summary["median_token_delta"] <= 0.0
    assert summary["mean_token_delta"] <= 0.0
    assert summary["max_token_delta"] <= 0  # No file must ever bloat in tokens from hygiene fixes
    assert summary["net_token_delta"] < 0
