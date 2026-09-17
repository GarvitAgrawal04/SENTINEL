# VERSION-DRIFT DATA READINESS

The corpus includes 10 version-drift chains spanning 60 versions (e.g., CLEAN_v1 -> CLEAN_v2 -> SUSPICIOUS_v3).

### What current Layer 1 sees
Layer 1 is stateless. It scans `v3` and evaluates it purely on the structural patterns present in that exact file. It has no concept of "this file used to be clean, and only 2 words changed."

### What a future Layer 2 needs
Layer 2 requires:
1. An established baseline (the `v1` or `v2` state stored in `sentinel.lock`).
2. An embedding or string-distance comparison (Semantic Displacement).
3. A cryptographic chain of trust (HMAC signatures).

### Corpus Readiness
The corpus perfectly prepares this future experiment. By providing structured, incremental semantic drift chains, the corpus gives the Layer 2 engineering team exactly what they need to tune the cosine distance thresholds for Semantic Displacement once the embedding models are integrated.

**Status:** Experiment Prepared. DO NOT claim current detection of semantic drift.
