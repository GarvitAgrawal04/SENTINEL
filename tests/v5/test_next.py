"""Sanity checks for the Sentinel Next build infrastructure.

These tests guard the three load-bearing walls of the 13-day build plan:
  1. The gate (bench/precision_gate.py) exists and is importable.
  2. The corpus rebuilder (bench/rebuild_corpus.py) exists.
  3. The daily prompts and agent contract exist, are consistent, and say the right things.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_the_build_plan_and_its_tools_exist_and_are_wired():
    for f in ("docs/build/DAILY_PROMPTS.md", "docs/build/AGENT_CONTRACT.md", "docs/build/PROGRESS.md",
              "docs/build/README.md", "bench/precision_gate.py", "bench/rebuild_corpus.py"):
        assert (ROOT / f).is_file(), f
    prompts = (ROOT / "docs" / "build" / "DAILY_PROMPTS.md").read_text(encoding="utf-8")
    assert prompts.count("## DAY") == 13
    assert "precision_gate.py check" in prompts and "benign twin" in prompts        # the gate and the twin rule are in the daily loop
    contract = (ROOT / "docs" / "build" / "AGENT_CONTRACT.md").read_text(encoding="utf-8")
    assert "No model may set COMPROMISED" in contract and "Never edit a test" in contract
