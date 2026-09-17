# SENTINEL Layer 2 Handoff Specification

## 1. Current Layer 1 Outputs
Layer 1 has been frozen and now outputs a consistent `ScanResult` object per evaluation. 
- It aggregates `Finding` objects generated from 16 structural pattern-matching rules.
- Computes `l1_penalty`, identifying structurally unambiguous triggers and score ceilings.
- Validates clean inputs against structural attack vectors.

## 2. Layer 2 Implementation Status
Layer 2 is now **FROZEN** and fully implements the PRD specifications for Semantic Displacement.
- **Deterministic File Diffing:** `sentinel/layer2/diff.py` computes SHA256 hashes against a loaded `BaselineProvider` interface to establish structual additions, modifications, and deletions. No network fetches are used.
- **Semantic Displacement Calculation:** `sentinel/layer2/displacement.py` computes cosine distances for any text drift using `BAAI/bge-m3` via `sentence-transformers`.
- **Direction & Magnitude:** Computed exactly as defined. The displacement points towards known clusters and derives an `attack_multiplier` natively.
- **Output Contract:** Generates a `Layer2Result` mapping modified files to `SemanticDisplacement` objects, allowing Layer 1's `formula.py` engine to natively extract `l2_penalty = magnitude * 30 * attack_multiplier`.

## 3. sentinel.lock Boundary
Layer 2 expects a fully instantiated `BaselineProvider` protocol matching `sentinel/manifest/sentinel_lock.py`.
- It consumes a deterministic map of absolute paths to `sha256` sums and their associated `1024-dim` embedding float arrays.
- It does not mutate or author `sentinel.lock`; it merely validates the current environment against it.

## 4. Tests
Layer 2 tests are fully active in `tests/layer2/`:
- `test_diff.py`: Proves path normalization and determinism.
- `test_displacement.py`: Proves cosine math boundaries and exception handling for missing components.
- `test_integration.py`: Validates the pipeline handoff to `formula.py`.

## 5. Security & Read-Only Constraints
Layer 2 acts entirely in a read-only capacity. It parses text. It does not evaluate ASTs dynamically, and it does not make outbound HTTPS calls to npm, pypi, or github. `diff.py`'s legacy live-fetch code has been removed.

## 6. Expected Layer 3 Boundaries
Layer 2 stops at measuring semantic vectors. It does NOT:
- Explain what the semantic delta means (e.g., "The user added a prompt injection").
- Estimate impact on agents.
- Generate SHAP/span attributions.
All of the above remains within the explicit scope of Layer 3 (currently unimplemented). Layer 3 should consume both Layer 1 Findings and Layer 2 Semantic Distances to feed a local classifier.
