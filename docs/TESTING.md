# SENTINEL TESTING POLICY

The testing architecture distinguishes between structural enforcement, performance, and deterministic behavior. A future engineer must understand which tests validate core invariants versus which tests contain legacy debt.

## 1. Canonical V1 Functional Suite (Release Gate)
To validate that the V1 architecture behaves safely:
```bash
python -m pytest tests/release/
```
This suite verifies:
- Offline execution (No network/cloud dependency).
- Read-only guarantees (Scanner cannot mutate project files).
- Secret Non-Leakage (Redaction of credentials).

## 2. Layer 1 (Excluding Debt)
To validate the deterministic pattern-matching engine (S1-S16):
```bash
python -m pytest tests/layer1/ -k "not test_rule_metadata"
```

## 3. Legacy Test Debt (Expected Failures)
If you run the full suite (`python -m pytest`), you will see exactly **37 failures**. These are explicitly accepted as **Legacy Test Debt** and are NOT production bugs.
- **34 failures** in `tests/layer1/test_rule_metadata.py`: These tests enforce an old API (`check()`) rather than the active API (`scan()`).
- **3 failures** in `tests/test_deep_rules.py` & `tests/test_scanner.py`: These tests enforce old additive penalty math. V1 production uses correct subtractive math. Do not modify production math to satisfy these tests.

## 4. Benchmark Command
```bash
python benchmark/run_benchmark.py
```
*Expected Output: TP=12, FP=0, TN=48, FN=1.*

## 5. Performance Gate
```bash
python -m sentinel.cli scan --hooks-only <target_dir>
```
*Expected: Sub-400ms execution.*

## 6. Mentor Demo Procedure
To validate end-to-end integration:
```bash
python -m sentinel.cli scan samples/trapdoor_style_demo.md
```

## Matrix Summary
- **Layer 0**: `pytest tests/layer0/`
- **Layer 1**: `pytest tests/layer1/`
- **Layer 2**: Tested via integration in `release/` tests.
- **Layer 3**: Tested via integration in `release/` tests.
- **Layer 4**: Tested via integration in `release/` tests.
- **API**: Verified via `test_offline_runtime.py`.
- **CLI**: Verified via `test_read_only_runtime.py`.
