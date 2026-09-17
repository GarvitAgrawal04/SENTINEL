# KNOWN LIMITATIONS (V1)

This file documents explicit limitations in the current V1 production release. These are not "bugs", but defined boundaries of the current capabilities.

## Layer 2
- **Semantic Direction Unavailable**: The vector displacement algorithm accurately identifies displacement magnitude from the trust baseline, but cannot classify the *intent* (attack vs. benign) of that displacement.
- **Attack Trajectory Unavailable**: Cannot map displacement to specific threat-actor manifolds.
- **Multiplier Defaults to 1.0**: Because direction is unavailable, `attack_multiplier` remains forced to 1.0.
- **Displacement is not Maliciousness**: A high cosine displacement only means "significantly different from baseline," which happens during normal large refactors.

## Layer 3
- **Nearest-Neighbor Baseline Only**: Impact generation relies purely on retrieving the closest K exemplars from the local index.
- **No Promoted Domain Classifier**: The production domain-adapted semantic classifier has not been trained or integrated.
- **Baseline Limitations**: KNN limits nuance; it can only categorize threats it has exactly seen before in the corpus.

## Layer 4
- **Deterministic Guidance Only**: Output strings are hardcoded to trigger based on specific rules.
- **No Conversational Reasoning**: It will not dynamically explain *how* a specific prompt injection circumvents a specific agent prompt.
- **No Automatic Remediation**: The tool will not actively revert changes or uninstall npm packages.

## Detection & Benchmarking
- **FN=1 (False Negative)**: One benchmark sample explicitly evades the current S1-S16 deterministic ruleset because it utilizes highly sophisticated, context-aware prompt bridging that requires LLM reasoning (V1.5) to reliably identify without inflating False Positives.
- **Benchmark Constraints**: The benchmark is currently limited to the 61-sample default eval set.

## Test Debt
- **34 Metadata/API-Contract Legacy Failures**: Found in `tests/layer1/test_rule_metadata.py`.
- **3 Legacy Scoring Assertions**: Found in `tests/test_deep_rules.py` and `tests/test_scanner.py`.
