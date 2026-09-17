# SEMANTIC DISPLACEMENT READINESS

The corpus contains `metadata/semantic_displacement.json`, which defines 43 families structured for displacement testing.

### What Data Exists
- Triplet structures mapping a baseline clean instruction, a structurally malicious injection, a semantically reworded malicious injection, and a benign lookalike.
- Pre-computed token distances based on the author's hypothetical metrics (not validated).

### What Experiment It Enables
Once Layer 2 is active, we can run a chosen embedding model (e.g., `text-embedding-3-small` or a local equivalent) across these triplets to tune the cosine distance threshold. 

### What is Still Missing
- The actual embedding model infrastructure in Sentinel.
- Field testing to ensure the chosen threshold separates the benign lookalikes from the reworded attacks.

### What Constitutes a Valid Future Result
A valid Layer 2 result will be achieved when the cosine distance reliably clusters the "reworded" and "obfuscated" variants close to the "structurally malicious" baseline, while keeping the "benign lookalike" outside the alarm radius. 

**Status:** The data is structurally perfect for the future Layer 2 experiment. We explicitly do NOT claim Semantic Displacement is validated or functional today.
