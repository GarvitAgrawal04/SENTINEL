# GITHUB BACKLOG

This file represents concrete issue-sized tasks ready for Jira/GitHub.

---

### [TASK] Clean Legacy Test Contract Debt
- **Why**: 34 tests fail against the legacy `check()` module interface instead of the modern `scan()` interface.
- **Files**: `tests/layer1/test_rule_metadata.py`
- **Dependencies**: None.
- **Acceptance Criteria**: The 34 test failures are resolved without changing V1 production detection logic.
- **Tests Required**: N/A (this is a test fix).
- **Not in Scope**: Changing `sentinel/rules/*.py` implementations.

---

### [TASK] Clean Scoring Mathematical Assertions
- **Why**: 3 test assertions fail because they hardcode expectation of additive scoring (`100 + penalty`) rather than production subtractive scoring (`100 - sum(penalty)`).
- **Files**: `tests/test_deep_rules.py`, `tests/test_scanner.py`
- **Dependencies**: None.
- **Acceptance Criteria**: Hardcoded numeric asserts equal the correct V1 math output.
- **Not in Scope**: Changing `sentinel/scoring/formula.py`.

---

### [TASK] Layer 2: Trusted Semantic Centroid Asset Work
- **Why**: Semantic Direction is currently unavailable, defaulting `attack_multiplier` to 1.0.
- **Files**: `sentinel/layer2/displacement.py`
- **Dependencies**: BGE-M3 corpus evaluation data.
- **Acceptance Criteria**: Generate mean vector embeddings for `clean` and `attack` manifolds. Implement logic to measure trajectory distance from these centroids.
- **Not in Scope**: Re-adding network calls to fetch remote cluster data.

---

### [TASK] Layer 3: Classifier Promotion Evaluation
- **Why**: The domain-adapted classifier is not promoted.
- **Files**: `sentinel/layer3/classifier.py`
- **Dependencies**: Training dataset extraction.
- **Acceptance Criteria**: Train the classifier. If it achieves >96% F1 with 0 FP, replace the KNN `NearestNeighborBaseline`.
- **Not in Scope**: Re-introducing LLMs as the classification decider.

---

### [TASK] V1.5 Chatbot & LLM Explanation
- **Why**: Deterministic guides lack deep contextual narrative around exactly *how* a specific injected prompt functions.
- **Files**: `sentinel/layer5/` (New)
- **Dependencies**: All V1 artifacts.
- **Acceptance Criteria**: Implement a conversational wrapper around `ScanResult`.
- **Not in Scope**: Running this loop automatically during standard CLI `scan` (it must remain interactive).

---

### [TASK] Network Vulnerability Correlation
- **Why**: C2 bridges (S11) and Exfiltration links (S5) are flagged structurally but not verified.
- **Files**: `sentinel/enrichment/network.py`
- **Dependencies**: None.
- **Acceptance Criteria**: Add a safe, opt-in mechanism to enrich offline findings with passive DNS or Threat Intel APIs.
- **Not in Scope**: Executing HTTP requests over user code or enabling it by default.
