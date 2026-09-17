# LAYER 3 SPEC EXTRACTION

## Exemplar Representation & Nearest-Neighbor (3a-i)
- **PRD Source**: Section 13.5 (Layer 3 - EXPLAIN).
- **Requirement**: "Embedding + Nearest-Neighbor (day one, zero training): compare the file's embedding against a curated exemplar set (18 attack + 18 clean)."
- **Output**: "Output: matched exemplar and similarity score — 'this resembles ATK-S10: ChainDrop-pattern SessionStart hook, similarity 0.91.'"
- **Boundary**: Zero training required for baseline. Uses existing Layer 2 embeddings to compute cosine similarity against a static dataset of reference exemplars.

## Agent-Impact Reconstruction
- **PRD Source**: Section 13.5.
- **Requirement**: "for every COMPROMISED or SUSPICIOUS finding where reconstruction is possible... decode payload, name target, state the concrete action the agent would have taken."
- **Examples provided**: 
  - Invisible Unicode decoded to exfiltration URL -> "Your agent would have posted $AWS_ACCESS_KEY and $GITHUB_TOKEN to https://c2-malicious.io/collect"
  - Missing-path hook -> "This SessionStart hook would have executed .claude/setup.mjs on every session start; the script no longer exists, suggesting it was planted by an uninstalled package"
- **Constraint**: Must use concrete evidence from Layer 0, Layer 1 (findings), or Layer 2. No speculative LLM reasoning.

## Domain-Adapted Classifier (3a-ii)
- **PRD Source**: Section 13.5.
- **Requirement**: "Domain-Adapted Classifier... fine-tune protectai/deberta-v3-small-prompt-injection-v2 on agent-config corpus. Promoted only if it outperforms 3a-i on held-out data."
- **Constraint**: It is explicitly an *optional/future* checkpoint. Its promotion is strictly gated by beating the 3a-i baseline on held-out evaluation sets.

## LLM Escalation (3b)
- **PRD Source**: Section 13.5.
- **Requirement**: "Injection-Hardened LLM Escalation (opt-in, low-confidence only)."
- **Constraint**: Explicitly OUT OF SCOPE for this build phase per prompt instructions.

## Security & Boundary Constraints
- Must remain strictly offline (no external APIs).
- Must handle Layer 2 placeholder semantic direction safely (direction=unavailable, multiplier=1.0) without fabricating labels.
- Test/holdout exemplars must absolutely not leak into the 3a-i reference index.

## Score Integration
- **PRD Source**: Section 13.2 Formula.
- **Requirement**: `+ (L3_confidence * L3_bonus)`. Layer 3 bonus is up to +10 for high classifier confidence-of-clean. Cannot push a score above 70 if any Layer 1 rule fired.
