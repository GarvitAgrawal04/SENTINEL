# LAYER 4 SPEC EXTRACTION

Based on SENTINEL_PRD_Master_v3:

## Scope
- V1: Decision tree.
- V1.5 (Excluded): Full chatbot, auto-fix.

## Behavior
- Provides a Plain-English verdict.
- Recommends a specific next step.
- Focuses on instructing a human operator to "fix -> rescan".
- Does NOT execute auto-fix.
- Must not invent remediation policy.

## Inputs
- Findings (Layer 1)
- Displacement / Direction (Layer 2)
- Baseline Exemplars (Layer 3)
- Score & Verdict
- Hooks-only mode constraints.

## Constraints
- Deterministic.
- Zero external LLM dependency.
- Read-only execution.
- Redaction of sensitive credentials/bridges.
- Must preserve missing Layer 2 direction without speculating.
- Must preserve Layer 3 baseline limitation without hallucinating a classifier confidence.
