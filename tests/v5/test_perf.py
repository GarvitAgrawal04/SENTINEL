"""Perf guardrail: scan all reference fixtures and assert it completes in under 2 seconds.

This is a SMOKE TEST, not a benchmark. It is a guardrail against accidental O(n^2) regressions —
not a promise of any particular wall-clock speed. The limit (2 s) is intentionally loose so it
never fails on a slow CI runner. If you see this test failing, the engine has regressed to
quadratic behaviour: profile before changing the limit.
"""
import tempfile
import time
from pathlib import Path

from sentinel import core


def test_scan_all_reference_fixtures_is_fast():
    # Guardrail against accidental O(n^2), not a promise of wall-clock speed.
    # 13 fixtures covering every verdict and rule family; 2 s is ~20x the current measured time.
    tmp = Path(tempfile.mkdtemp(prefix="sentinel-perf-"))
    fixtures = core.build_fixtures(tmp)
    assert len(fixtures) >= 12, f"expected at least 12 fixtures, got {len(fixtures)}"

    t0 = time.perf_counter()
    for fx in fixtures:
        core.scan_repo(fx["path"], baseline=fx.get("baseline"))
    elapsed = time.perf_counter() - t0

    assert elapsed < 2.0, (
        f"scanning {len(fixtures)} reference fixtures took {elapsed:.2f}s — this suggests O(n^2) "
        f"has crept back in (prose.findings or core.scan_repo). Profile before raising the limit."
    )
