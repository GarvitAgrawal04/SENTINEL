# ENGINEERING DEBT REGISTER

| ID | Description | Why it exists | Current Status | Severity | Blocks V1? | Recommended Action | Relevant Files |
|---|---|---|---|---|---|---|---|
| **DEBT-001** | 34 legacy metadata/test contract failures | During architecture scaling, `check()` was deprecated for `scan()` and module schemas changed. The original metadata tests were not updated to reflect this. | Open | Low | No | Refactor tests to assert against `ScanResult` rather than internal module structure. | `tests/layer1/test_rule_metadata.py` |
| **DEBT-002** | 3 legacy scoring assertions | The production formula was corrected from additive (`100 + penalty`) to subtractive (`100 - sum(penalty)`). The tests still hardcode expectations for the old additive output. | Open | Low | No | Update the numeric asserts in the tests to reflect the new boundaries. | `tests/test_deep_rules.py`, `tests/test_scanner.py` |
| **DEBT-003** | Layer 2 semantic centroid/direction assets unavailable | The pipeline cannot determine malicious direction until domain-adapted vector clusters (centroids) are trained and embedded into the release. | Open | Medium | No | Research and generate centroid models using the test corpus. | `sentinel/layer2/displacement.py` |
| **DEBT-004** | Layer 3 domain classifier not promoted | A sophisticated classifier needs to prove it outperforms the baseline KNN approach before it can replace it. | Open | Medium | No | Train classifier, evaluate against KNN baseline. | `sentinel/layer3/classifier.py` |
