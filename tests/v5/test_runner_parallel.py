"""Tests for concurrent scenario execution in sentinel.timewarp.runner."""
from __future__ import annotations

import threading
import time

from sentinel.timewarp.clock import Scenario
from sentinel.timewarp.runner import run


class ConcurrencyTrackingModel:
    """Mock model tracking the peak number of concurrent worker threads."""

    def __init__(self, delay: float = 0.05) -> None:
        self.delay = delay
        self.active_threads = 0
        self.peak_concurrent = 0
        self.lock = threading.Lock()

    def step(self, messages: list[dict]) -> dict:
        with self.lock:
            self.active_threads += 1
            if self.active_threads > self.peak_concurrent:
                self.peak_concurrent = self.active_threads
        try:
            time.sleep(self.delay)
            return {"role": "assistant", "content": "Done."}
        finally:
            with self.lock:
                self.active_threads -= 1


def test_runner_six_scenarios_run_concurrently():
    plan = [Scenario(name=f"scenario_{i}", session=i) for i in range(6)]
    model = ConcurrencyTrackingModel(delay=0.04)

    start_time = time.monotonic()
    traces = run("# Guidelines\n", plan, model=model, parallel=4)
    elapsed = time.monotonic() - start_time

    assert len(traces) == 6
    # Proves concurrency: peak > 1 thread
    assert model.peak_concurrent > 1
    # Proves worker cap: peak <= 4
    assert model.peak_concurrent <= 4
    # Serial execution for 6 * 3 probes would take at least 0.72s; concurrent is much faster
    assert elapsed < 0.6
