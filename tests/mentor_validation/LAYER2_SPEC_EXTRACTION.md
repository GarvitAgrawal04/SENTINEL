# LAYER 2 SPEC EXTRACTION
(Derived directly from SENTINEL_PRD_Master_v3.md)

1. **Baseline State & sentinel.lock Relationship**
`sentinel.lock` stores a compact behavioral embedding vector alongside the file's sha256 hash. This represents the baseline state. 
Layer 2 requires reading this baseline representation (hash + embedding) rather than dynamically fetching previous versions over the internet.

2. **Hash diff**
Compare each file's sha256 against `sentinel.lock`. Any mismatch triggers a structural diff cross-referenced against S1-S16 and Layer 2 Semantic Displacement.

3. **Semantic Displacement**
Measures the semantic drift between the current file and the baseline state. Applied to agent configuration files on disk, or MCP tool description JSON re-fetched at session start (Deadbugz pattern). 
Output format required: magnitude (float) and direction (string).

4. **Cosine Distance**
Displacement magnitude is derived from the cosine distance (0-1) between the baseline embedding and the current file embedding.

5. **Displacement Direction**
Must be classified as moving toward known-benign or known-attack clusters. 
(Note: the PRD does not specify exact centroid math beyond "toward known-benign or known-attack clusters," which implies measuring relative distance to curated cluster centroids).

6. **Displacement Magnitude**
Derived from cosine distance (0.0 to 1.0 scale).

7. **Attack Multiplier**
If direction == "attack", attack_multiplier = 1.5. Else, 1.0.

8. **Confidence**
Mentioned alongside Layer 3 (L3 clean-confidence bonus), not explicitly part of Layer 2 displacement calculation (unless L2 uncertainty propagates, but formula.py handles it cleanly).

9. **Thresholds**
The PRD does NOT define specific thresholds for when a semantic displacement is considered anomalous or forces a verdict, other than scaling the penalty linearly:
`l2_penalty = displacement_magnitude * 30 * attack_multiplier`

10. **Version/History Semantics**
The baseline is strictly defined by the locked embedding in `sentinel.lock`, *not* temporal diffs or external Git history.

11. **Failure/Unknown Behavior**
If the local model (BGE-M3) is unavailable, it must fail deterministically or report an unavailable state. Do not silently fall back. Do not throw uncaught NaNs into the scoring formula. Missing baseline = 100% displacement or undetermined depending on whether it's an "addition" or missing lockfile. (To be mapped safely).
