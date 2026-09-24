# Testing Guide

Sentinel maintains a comprehensive automated test suite covering static rules, sandbox detonation, cryptographic signing, CI integration, VS Code extension, web frontend, and stress benchmarks.

## Test Suite Overview

| Test Module | Focus Area | Approximate Count |
|-------------|-----------|-------------------|
| `test_engine.py` | Core scanning engine, 26 rules, scoring formula | 35 |
| `test_prose.py` | Markdown tokenization, sentence extraction, regex patterns | 49 |
| `test_evidence.py` | Reproducibility of published benchmark numbers | 34 |
| `test_detonation.py` | Time-Warp sandbox, virtual clock, cassette replay | 13 |
| `test_doctor_lints.py` | Instruction Doctor D001-D008 hygiene checks | 10 |
| `test_doctor_graph.py` | Include DAG traversal and cycle detection | 7 |
| `test_doctor_gate.py` | Rewrite Gate prompt injection interception | 8 |
| `test_lock_and_pr.py` | AGENTS.lock signing, PR diff scanning | 6 |
| `test_frontend.py` | Web UI Content-Security-Policy, XSS prevention | 12 |
| `test_api.py` | FastAPI endpoints and JSON contract | 7 |
| `test_semantic.py` | Layer 3 advisory classifier invariants | 9 |
| `test_extreme_stress.py` | ReDoS, megadoc, megaline, concurrency soak | 8 |
| `test_readme.py` | README link integrity, anchor resolution, SVG staleness | 7 |
| `test_packaging.py` | PyPI metadata, wheel contents, SBOM schema | 4 |
| `test_portfolio.py` | Documentation completeness and cross-links | 9 |
| Release tests | Offline runtime, read-only, secret non-leakage | 3 |

**Total: 340+ tests**

## Running Tests

```bash
# Full suite
pytest

# Specific module
pytest tests/v5/test_engine.py

# Engine self-test (built-in fixtures)
sentinel selftest

# Self-scan invariant
sentinel scan .

# External link verification (requires internet)
python docs/check_readme_links.py

# Rebuild and verify all SVG diagrams
python docs/build_readme_assets.py
pytest tests/v5/test_readme.py::test_the_committed_diagrams_are_exactly_what_the_generator_makes
```

## Writing Tests for New Rules

Every new detection rule (S-series or D-series) requires:

1. **Attack fixture:** A realistic agent instruction file that triggers the rule.
2. **Benign twin:** A file using similar vocabulary that must NOT trigger the rule.
3. **Engine test:** Assert that the attack fixture produces the expected verdict and score.
4. **Render metadata:** Verify the rule has a human title in `sentinel/render.py`.
5. **Wild corpus benchmark:** Run `python bench/bench.py wild corpus` and verify 0 false conviction regressions.

## Stress Testing Philosophy

Sentinel's stress tests verify:

- **No catastrophic backtracking (ReDoS):** Every regex is tested against adversarial 500,000+ character payloads.
- **Memory stability:** 64-worker concurrent scans must show 0.0 MB memory drift.
- **Deterministic scoring:** Identical inputs must produce identical scores across unlimited reruns.
- **Graceful degradation:** Corrupted JSON, binary files, and encoding errors must not crash the scanner.
