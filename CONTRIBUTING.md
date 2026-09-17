# CONTRIBUTING TO SENTINEL

Thank you for contributing! To maintain SENTINEL's strict security boundaries, please adhere to the following workflow.

## 1. Branch Workflow
- Base your work on `main`.
- Create a feature branch (e.g., `feature/l2-centroid-training`).
- Pass the full release-gate tests before requesting review.

## 2. Adding a Detection Rule
- **Location**: Add your rule module (e.g. `s17_new_pattern.py`) to `sentinel/rules/`.
- **Implementation**: You must expose a `scan(text: str, filename: str) -> list[Finding]` method.
- **Scoring**: Define logical penalties based on impact. Do not force verdicts unless it fundamentally breaks project safety.
- **Testing**: Add `tests/layer1/test_s17_new_pattern.py` ensuring TP=1 and FP=0 against standard datasets.

## 3. Modifying Scoring / Layers
- All modifications to `sentinel/scoring/formula.py` or the Layer Dataflow (`sentinel/pipeline.py`) require **Architecture Review**. 
- A contributor must NEVER modify benchmark labels or expected results merely to make a patch pass. The mathematical benchmark (TP, FP, TN, FN) must improve legitimately.

## 4. Benchmark & Security Policy
- **ZERO FALSE POSITIVES**: The clean corpus MUST yield 0 False Positives. A single false positive fundamentally compromises SENTINEL's ability to act as an invisible security guardrail.
- **Offline & Read-Only**: New PRs must not add implicit HTTP dependencies (`requests`, `httpx`) inside the core pipeline. 
- **Secrets**: Do not commit actual `sk-proj` or GitHub tokens to the repository. Use dummy fixtures.

## 5. Review Expectations
Any change that bypasses Layer 1 determinism for an LLM fallback, executes a scanned file, or alters `sentinel.lock` handling will be automatically rejected.
