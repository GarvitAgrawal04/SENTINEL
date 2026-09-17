# ARCHITECTURE DECISIONS

This document records the major architectural design decisions explicitly codified in SENTINEL V1.

**1. Agents/rules do not bypass service boundaries.**
- *Reason*: Avoid tight coupling; rules must be isolated and evaluated holistically.
- *Do not regress*: Never allow a single rule to instantly return a verdict without running the full suite.

**2. Layer 1 is deterministic.**
- *Reason*: The foundation of the system must be fast, offline, and math-based.
- *Do not regress*: Do not introduce LLM calls to resolve regex ambiguities.

**3. S8 is static multi-file contradiction analysis.**
- *Reason*: Complex context resolution is too slow/fragile dynamically.
- *Do not regress*: Do not spawn a sub-agent to read the entire workspace to satisfy S8.

**4. Layer 2 is offline.**
- *Reason*: Privacy and speed.
- *Do not regress*: Do not switch to OpenAI/Anthropic embeddings.

**5. External historical network fetching was removed.**
- *Reason*: Scanner must be stateless and fast.
- *Do not regress*: Do not re-add dynamic URL curling.

**6. Layer 2 consumes BaselineProvider.**
- *Reason*: Allows the baseline to be a Git artifact or a separate locked manifest (`sentinel.lock`).

**7. Semantic direction is unavailable until trusted centroid assets exist.**
- *Reason*: Generating fake attack classifications compromises the mathematical integrity of the system.
- *Do not regress*: Do not use placeholders like `direction = random()`.

**8. attack_multiplier remains 1.0 while direction is unavailable.**
- *Reason*: Penalty math must remain standard if vector trajectory is unknown.

**9. Layer 3 uses nearest-neighbor baseline.**
- *Reason*: It provides mathematically provable context matching based on Euclidean distances.

**10. Classifier promotion requires evidence that it beats the baseline.**
- *Reason*: Prevents deploying complex ML models that perform worse than basic KNN.

**11. Layer 4 is deterministic.**
- *Reason*: Security guidance must be reproducible.

**12. Layer 4 does not use LLM reasoning in V1.**
- *Reason*: LLM reasoning is prone to hallucinating non-existent attacks based on code chunks.

**13. Scanner is read-only.**
- *Reason*: The scanner must not accidentally corrupt user code or act like malware.

**14. Scanner does not execute scanned content.**
- *Reason*: Prevents RCE during analysis.

**15. Hooks-only does not load Layer 2/3 models.**
- *Reason*: Extreme performance mode (<400ms) for pre-commit CI integration.

**16. Secret evidence is redacted before presentation.**
- *Reason*: Displaying captured `sk-proj` credentials to CI logs expands the blast radius of the attack.
- *Do not regress*: Do not disable `redact_scan_result`.

**17. V1.5 capabilities are intentionally deferred.**
- *Reason*: Ensures V1 remains fundamentally robust.
