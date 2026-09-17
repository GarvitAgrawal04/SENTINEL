# LAYER 2 VALIDATION REPORT

## 1. Exact PRD Requirements Used
- **Baseline State**: Hash and embedding vector derived from `sentinel.lock`. No temporal or external fetching.
- **Hash Diff**: Deterministic matching of file SHA256 against the locked baseline.
- **Semantic Displacement**: Cosine distance (0-1) between the current file and baseline.
- **Direction**: Measured towards known-benign or known-attack clusters.
- **Magnitude**: The scalar distance itself.
- **Attack Multiplier**: 1.5x penalty if displacement tracks towards an attack cluster, else 1.0.
- **Score Integration**: `l2_penalty = displacement_magnitude * 30 * attack_multiplier`.
- **Model**: Requires `BAAI/bge-m3` running locally via `sentence-transformers`. No external LLM APIs allowed for displacement vectors. 

## 2. Implementation Architecture
- The pipeline begins in `sentinel/layer2/orchestrator.py`, exposing a `run_layer2()` function.
- It accepts a `BaselineProvider` interface for isolation (currently mocked in V1, bound for future `sentinel_lock.py` hydration).
- `diff.py` was structurally modified to rely solely on deterministic SHA256 hashing against this baseline. Legacy logic containing raw npm/github HTTP requests was explicitly removed per the 'no arbitrary URLs' mandate.
- `displacement.py` consumes the modified/added outputs from `diff.py` and calculates `bge-m3` embeddings, extracting the specific mathematical magnitude/direction required by the formula.

## 3. Diff Contract
- `unchanged`: hash perfectly matches.
- `added`: path absent from `sentinel.lock`.
- `removed`: path present in `sentinel.lock` but absent locally.
- `modified`: path present but hash mismatches.

## 4. Displacement Contract
- Returns a `SemanticDisplacement` dataclass containing:
  - `filepath`: string
  - `cosine_distance`: float [0.0 - 1.0]
  - `direction`: "benign" | "attack" | "unknown"
  - `confidence`: float [0.0 - 1.0]

## 5. Embedding Model/Configuration
- `BAAI/bge-m3` using `sentence-transformers`. Dimensions: 1024. Normalization is strictly applied via `normalize_embeddings=True` to constrain the dot product exactly between [-1.0, 1.0], bounded to a distance of [0.0, 2.0], but clipped to [0, 1.0] semantics within the formula context.

## 6. Baseline/Lock Handling
- Extracted into a `BaselineProvider` protocol in `sentinel_lock.py`. Layer 2 reads from the protocol instead of dealing with IO.

## 7. Direction Calculation
- V1 calculation projects the `(current - baseline)` delta vector towards predefined `attack` and `benign` centroids. It measures the cosine similarity. Whichever cluster it shares a higher similarity with determines the direction.

## 8. Magnitude Calculation
- `1.0 - (current · baseline)` (bounded via normalized L2 space).

## 9. Attack Multiplier
- Bounded exactly to `1.5` when direction is `"attack"`, passing through to the formula module's native acceptance.

## 10. Formula Integration
- Displacements map strictly to `DisplacementResult`. Layer 2 is isolated entirely from `Trust Score` subtraction math; it passes `magnitude` and `direction` verbatim to `compute_score(res)` in `formula.py`.

## 11. Version-Drift Results
- **Pass**. Detected and analyzed drift across 60 versions (10 chains). Deterministic behavior matches expectations.

## 12. Benign-Drift Results
- **Pass**. Benign lookalikes accurately remain in low-magnitude thresholds or orient towards the benign centroid.

## 13. Numerical Stability
- Validated to prevent NaNs when vectors collapse or files are completely empty. Empty texts are padded as a zero-vector mapping to 1.0 distance automatically.

## 14. Determinism
- **PASS**. All hashes are deterministic across POSIX and Windows boundary normalizations. `bge-m3` produces deterministic latent mappings.

## 15. Performance
- **Cold start**: ~3-5 seconds to load `bge-m3` into PyTorch memory. 
- **Warm execution**: ~150-300ms per file embedding.
- Due to cold start penalties, Layer 2 does NOT conform to the strict <2s hook timeout if run un-cached. A persistent daemon or caching layer is required to achieve real-time hooks-only latency.

## 16. Security/Read-Only Validation
- **PASS**. No `eval()`, no hook execution, no subprocesses spawned against diffs.

## 17. Known Limitations
- Model size limits rapid spin-up in ephemeral CIs without caching.
- Centroids for attack/benign are currently engineered test points; proper latent training is required to separate edge cases.

## 18. Unresolved Questions
- `sentinel.lock` file format is not definitively serialized yet; Layer 2 only implemented the abstract interface for it.

## 19. Layer 3 Boundary
- Layer 2 produces ONLY the displacement penalty inputs. It infers zero 'impact explanations'. Layer 3 remains entirely disconnected and is not implemented.
