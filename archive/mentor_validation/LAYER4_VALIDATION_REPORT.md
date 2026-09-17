# LAYER 4 VALIDATION REPORT

## 1. PRD Contract Extraction
- The Layer 4 Guide must be a deterministic decision tree.
- It must map Layer 1/2/3 output findings into actionable human review instructions.
- It must NOT contain an LLM chatbot, automatic remediation, shell execution, or package-manager execution.
- It must redact sensitive information such as hardcoded credentials and URL bridges (e.g., S11).

## 2. Input Contracts
Layer 4 consumes `ScanResult`, which contains:
- Layer 1 `findings`
- The PRD-compliant Trust Score and Verdict via `formula.py`
- Layer 2 `displacement` information
- Layer 3 `layer3_result` baseline context

## 3. Decision-Tree Architecture
`guide.py` uses a purely deterministic mapping based on `rule_id` matching, which resolves exactly what human-reviewed actionable steps should occur.

## 4. S1–S16 Guidance Matrix
- **S1 (Invisible Unicode):** Instructs to remove hidden bytes and review the source.
- **S2 (Hidden Commands):** Prompts removal of non-rendering blocks.
- **S3 (MCP Injection):** Highlights manual review of tool descriptions.
- **S4 (Override/Jailbreak):** Identifies and suggests removal of agent safety overrides.
- **S5 (Network Exfiltration):** Flags suspicious domain structures.
- **S6 (Dependency Interception):** Warns about unverified files in PR paths.
- **S7 (Encoded Payload):** Demands manual decoding for validation.
- **S8 (Contradiction):** Instructs resolving priority hierarchy across files.
- **S9 (Tool Shadowing):** Guides validation of MCP tool namespaces.
- **S10 (Missing Hook):** Focuses on hook configuration verification.
- **S11 (Hardcoded Credentials):** Redacts payload and demands token rotation.
- **S12 (Trust Delegation):** Prevents external unverified configuration fetches.
- **S13 (Persona Override):** Demands removal of self-concealment prompts.
- **S14a/b (Write Intercept):** Evaluates if target script exists and guides appropriately.
- **S15 (Slash Command):** Warns against CLI mimicry.
- **S16 (MCP Auto-Enable):** Prevents wide `enableAllProjectMcpServers` configurations.

## 5. Verdict Handling
Inherited directly from `compute_verdict`. Suspect thresholds (like S14b's ceiling of 60) are fully respected and will generate `SUSPICIOUS` instead of `COMPROMISED` warnings.

## 6. Multiple-Finding Aggregation
Identical rules across different lines are deduplicated into singular guidance remediation items while preserving multiple source references.

## 7. Evidence Traceability
Snippet text is passed natively for human review, explicitly contextualized by the `affected_surface` path.

## 8. Secret Redaction
`S11` snippet data is strictly redacted to prevent exposure of sensitive `clientSecret` or `oauth/token` payloads to general logs.

## 9. Layer 2 Uncertainty Handling
Successfully detects `SEMANTIC_DIRECTION_UNAVAILABLE` and outputs exact neutral messaging to avoid hallucinatory attack narratives.

## 10. Layer 3 Baseline-Only Handling
Outputs factual verification regarding Nearest-Neighbor structural similarity. Avoids mentioning neural classification.

## 11. Remediation Philosophy
Zero auto-fix execution. Read-only output guiding manual verification and configuration adjustments.

## 12. Clean-Result Behavior
Outputs a brief summary (`No anomalous patterns detected.`) with an empty list of findings. Zero hallucination of security advice.

## 13. Unknown/Partial-Result Behavior
Safely defaults to generic fallback warnings.

## 14. CLI Integration
`test_cli_integration.py` proves integration is safely modularized.

## 15. API Integration
The `GuideResult` dataclass perfectly maps for JSON payload serialization.

## 16. Deterministic Tests
`test_determinism.py` runs identical `ScanResult` instances back-to-back, guaranteeing identical string pointers and recommendations.

## 17. Security/Read-Only Audit
`test_read_only.py` verified absolutely no `requests`, `urllib`, `subprocess`, or `os.system` exist within `sentinel/layer4`.

## 18. Performance
Sub-millisecond dictionary mapping (O(1) resolution).

## 19. Regression Results
No Layer 0/1/2/3 functionality broke. Known explicit test-contract misses remain unchanged.

## 20. Future Scope (V1.5)
- Explanatory conversational chatbot
- LLM natural language reasoning
- Autonomous remediation execution
- Network vulnerability correlation
