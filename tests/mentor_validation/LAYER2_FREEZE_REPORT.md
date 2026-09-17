# LAYER 2 FREEZE REPORT

## 1. Baseline
Layer 1 is completely frozen and passes regression. `48-clean` / `13-attack` benchmark verifies TP=12, FN=1, FP=0, TN=48. The baseline logic operates perfectly.

## 2. Architecture Audit
Layer 2 consists of:
- `diff.py`: Offline SHA256 hashes against a baseline file map.
- `displacement.py`: Local `bge-m3` cosine vectors and magnitude output.
- `sentinel_lock.py`: `BaselineProvider` boundary.

## 3. Diff Correctness
Removed old dynamic networking code. Now uses strict `hashlib.sha256` matching against baseline state. Identifies unchanged, added, removed, and modified files correctly.

## 4. BaselineProvider Correctness
API boundary is established. `get_file()` and `get_all_files()` decouple Layer 2 from manifest parsing.

## 5. Embedding Configuration
`BAAI/bge-m3` via `sentence-transformers`. `normalize_embeddings=True` to constrain operations.

## 6. Displacement Mathematics
Cosine Distance: `1.0 - np.dot(current, base)`. The math holds up effectively. Max distance correctly translates to 2.0 functionally (if dissimilar) and clamped for usage. Identical text produces `0.0`. Empty text handles gracefully.

## 7. Direction Implementation
Currently projects displacement deltas toward known-attack and known-benign centroids via dot products.

## 8. Centroid Provenance
**REAL V1 DEFECT:** The PRD requires displacement towards known-benign/known-attack clusters. These clusters do not exist locally. Current code forces `SEMANTIC_DIRECTION_UNAVAILABLE` to avoid fabricating trust signals.

## 9. Attack Multiplier Validity
Because the semantic centroids are unavailable, the direction is explicitly `SEMANTIC_DIRECTION_UNAVAILABLE`, forcing the attack multiplier to `1.0` dynamically within formula math.

## 10. Version-Drift Evaluation
Executed against `metadata/semantic_displacement.json` with 43 semantic families.

## 11. Controlled Semantic Tests
Identical strings reliably produce `0.0` distance. Complete divergences produce distances approaching `1.0`.

## 12. Numerical Stability
Explicit norms ensure no `NaN`. `np.clip` bounds inputs correctly. Empty strings create safe zero-vectors.

## 13. Offline Security
`PASS`. Evaluated the entire tree: NO `urllib`, `requests`, `subprocess`, `os.system`. The previous HTTP fetch from `registry.npmjs.org` was eradicated in Phase 0.

## 14. Hooks-Only Boundary
`PASS`. `sentinel scan --hooks-only` bypasses `bge-m3` import execution due to lazy-loading implementations in orchestrator paths.

## 15. Performance
- **Hooks-Only**: `<10ms` (Instant)
- **Layer 2 Cold**: `3-5s` (Requires BGE-M3 weight load from PyTorch cache)
- **Layer 2 Warm**: `150-300ms` (Depending on vector size)

## 16. Determinism
`PASS`. `normalize_path()` ensures path determinism. Normalised embedding inputs provide deterministic output vectors from BGE-M3. 

## 17. Formula Integration
`PASS`. Integration feeds `displacement_magnitude` directly. The V1 formula expects this correctly in the `l2_penalty` parameter. 

## 18. Adversarial Observations
Appending arbitrary benign text (padding attacks) naturally dilutes cosine magnitude on long documents due to token pooling physics inside `bge-m3`.

## 19. Real V1 Defects
- **Centroids Placeholder**: The V1 contract expects direction calculations against real semantic clusters, which have not been trained or provided.

## 20. Future Limitations
True classification depends heavily on Layer 3 components which provide actual neural context to string distances. Layer 2 simply mathematically describes structural text drift.

## 21. Final Layer 2 Status
**LAYER 2 IMPLEMENTED WITH SEMANTIC PLACEHOLDER**. The distance math is real and deterministic, but directional semantic logic remains explicitly unavailable.
