"""Unit test for trigger prevalence benchmark (Day 4 T2)."""
from pathlib import Path
from bench import trigger_prevalence

ROOT = Path(__file__).resolve().parents[2]


def test_trigger_prevalence_fixture_corpus(tmp_path):
    """Assert trigger prevalence on doctor fixture corpus stays <= 1.25 scenarios/repo mean."""
    fixture_dir = ROOT / "tests" / "fixtures" / "doctor_corpus"
    summary = trigger_prevalence.evaluate(
        target_dir=fixture_dir,
        output_dir=tmp_path,
        max_mean_threshold=1.25,
    )
    custom_res = summary["corpora"]["custom_target"]
    assert custom_res["targets_evaluated"] == 50
    assert custom_res["mean_scenarios_per_target"] <= 1.25
    assert custom_res["trigger_rate"] <= 0.10  # less than 10% of repos have conditional triggers
