"""
Performance sanity for Layer 1 (PRD: DETECT is the fast, deterministic pass — low
milliseconds per file). This is a guardrail against a rule that accidentally goes
super-linear (catastrophic regex backtracking, O(n²) rescans) on a large but perfectly
ordinary file, not a benchmark. The bound is deliberately generous so it stays green on
shared CI; a real regression (seconds, not milliseconds) still trips it.

Run with the rest of the suite, or isolate/skip via the marker:  -m perf  /  -m 'not perf'
"""
import time

import pytest

from tests.layer1.corpus import CLEAN_CLAUDE_MD

# ~150 KB of benign, realistic guidance text (well above any normal config file).
BIG_BENIGN = (CLEAN_CLAUDE_MD + "\n") * 1500
TIME_BUDGET_S = 2.0


@pytest.mark.perf
def test_all_rules_scale_on_large_benign_file(run_all_rules, make_ctx):
    assert len(BIG_BENIGN) > 100_000  # guard the fixture actually got big
    ctx = make_ctx(git_tracked={"CLAUDE.md"}, files={"CLAUDE.md": BIG_BENIGN}, origin="git")

    start = time.perf_counter()
    findings = run_all_rules(BIG_BENIGN, "CLAUDE.md", ctx)
    elapsed = time.perf_counter() - start

    assert findings == [], f"large benign file should stay clean, fired {[f.rule_id for f in findings]}"
    assert elapsed < TIME_BUDGET_S, f"Layer 1 took {elapsed:.2f}s on ~{len(BIG_BENIGN)//1024}KB (budget {TIME_BUDGET_S}s)"


@pytest.mark.perf
def test_single_rule_not_pathological(run_rule, make_ctx):
    """No individual rule may dominate the budget on its own."""
    ctx = make_ctx(git_tracked={"CLAUDE.md"}, files={"CLAUDE.md": BIG_BENIGN}, origin="git")
    for rule in [f"S{i}" for i in range(1, 17)]:
        start = time.perf_counter()
        run_rule(rule, BIG_BENIGN, "CLAUDE.md", ctx)
        elapsed = time.perf_counter() - start
        assert elapsed < TIME_BUDGET_S, f"{rule} took {elapsed:.2f}s (budget {TIME_BUDGET_S}s)"
