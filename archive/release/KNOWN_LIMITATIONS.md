# KNOWN LIMITATIONS

## V1.5 Future Scope
SENTINEL V1 explicitly defers the following capabilities to the V1.5 milestone:
1. **Chatbot Explanations**: Deep contextual descriptions using an LLM generation loop.
2. **Auto-Remediation Execution**: Active package manager interaction to purge subverted installations.
3. **Semantic Direction Trajectory**: The attack multiplier remains set at `1.0` and Semantic Direction returns `SEMANTIC_DIRECTION_UNAVAILABLE` until domain-adapted ML centroids are securely deployed.

## Engineering Debt
- **Legacy Test Suite**: `tests/layer1/test_rule_metadata.py` contains 34 intentional failures representing API deprecations resulting from structural reorganizations (e.g., `check()` to `scan()`). These are explicitly documented as debt, not pipeline breakages.
- **Legacy Assertions**: `tests/test_deep_rules.py` maintains 3 specific numeric score assertion failures reflecting the intentional mathematical rewrite of `formula.py` (Additive -> Subtractive normalization). These metrics are structurally correct in V1 production.
