# LAYER 2 SEMANTIC AUDIT

## 1. Embeddings Generation
- **REAL IMPLEMENTATION:** Uses `BAAI/bge-m3` via `sentence-transformers.encode()`. The model generates real embeddings.
- **PRD REQUIREMENT:** Use the canonical BGE-M3 local embedding stack.
- **CURRENT STATUS:** Validated. Generates authentic 1024-dim dense vectors.

## 2. Normalization
- **REAL IMPLEMENTATION:** `normalize_embeddings=True` is explicitly passed to `encode()`. The resulting vectors have an L2 norm of 1.
- **PRD REQUIREMENT:** Normalized space for cosine operations.
- **CURRENT STATUS:** Validated.

## 3. Cosine Distance
- **REAL IMPLEMENTATION:** Computes `1.0 - dot_product(v1, v2)`. Explicitly clips value to `[-1.0, 1.0]` internally before subtraction to guarantee outputs bound `[0.0, 2.0]` (functionally clipped to 0.0-1.0 because of positive similarities).
- **PRD REQUIREMENT:** Distance magnitude metric between 0 and 1.
- **CURRENT STATUS:** Validated. 

## 4. Direction Representation
- **REAL IMPLEMENTATION:** Returns a hardcoded label (`"attack"`, `"benign"`, or `"unknown"`) based on vector projection toward centroids.
- **PRD REQUIREMENT:** Must output "toward known-benign or known-attack clusters."
- **CURRENT STATUS:** Valid API boundary, but completely synthetic projection vectors.

## 5. Centroids Loading/Generation
- **PLACEHOLDER:** `_get_centroids()` currently seeds `np.random.seed(42)` and generates two orthogonal unit vectors for attack and benign clusters.
- **PRD REQUIREMENT:** Displacement towards "known-benign or known-attack clusters."
- **CURRENT STATUS:** **PLACEHOLDER.** No curated model artifact is actually loaded to represent these semantic points.

## 6. Attack Direction Determination
- **PLACEHOLDER:** Calculates cosine similarity of the displacement vector against the random attack unit vector vs the random benign unit vector. Whichever is greater determines the label.
- **PRD REQUIREMENT:** Classification based on real semantic trajectories.
- **CURRENT STATUS:** **PLACEHOLDER.**

## 7. Attack Multiplier Selection
- **REAL IMPLEMENTATION:** Maps `direction == "attack"` directly to `1.5` multiplier natively.
- **PRD REQUIREMENT:** 1.5x scaling when traversing towards an attack trajectory.
- **CURRENT STATUS:** API Contract is valid, but the trigger relies on placeholder centroids.
