# FINAL SCORE AUDIT

This audit cross-references the mathematically defined penalties and bounds from the Master v3 PRD against the actual frozen implementation in `sentinel/rules/base.py` and `sentinel/scoring/formula.py`.

### S1: Invisible Unicode
- **PRD:** Penalty -50. Structurally Unambiguous -> Forces COMPROMISED.
- **Code:** Penalty = 50. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S2: Hidden Comments
- **PRD:** Penalty -35.
- **Code:** Penalty = 35.
- **Status:** **PASS**

### S3: MCP Tool Description Injection
- **PRD:** Penalty -35.
- **Code:** Penalty = 35.
- **Status:** **PASS**

### S4: Override Phrasing
- **PRD:** Penalty -25.
- **Code:** Penalty = 25.
- **Status:** **PASS**

### S5: Exfiltration Patterns
- **PRD:** Penalty -40.
- **Code:** Penalty = 40.
- **Status:** **PASS**

### S6: New File in Dependency PR
- **PRD:** Penalty -15. Deterministic Layer 1 trigger feeding Layer 2.
- **Code:** Penalty = 15. Fires on `postinstall-suspected` and `postinstall-confirmed` origin.
- **Status:** **PASS**

### S7: Encoded Payload
- **PRD:** Structurally Unambiguous -> COMPROMISED.
- **Code:** Penalty = 45. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S8: Cross-File Contradiction
- **PRD:** Penalty -20 (derived context).
- **Code:** Penalty = 20.
- **Status:** **PASS**

### S9: Tool Shadowing
- **PRD:** Penalty -30.
- **Code:** Penalty = 30.
- **Status:** **PASS**

### S10: Hook References Missing Path
- **PRD:** Structurally Unambiguous -> COMPROMISED.
- **Code:** Penalty = 70. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S11: Bridge URL
- **PRD:** Structurally Unambiguous -> COMPROMISED.
- **Code:** Penalty = 70. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S12: Trust Delegation
- **PRD:** Penalty -35.
- **Code:** Penalty = 35.
- **Status:** **PASS**

### S13: Persona Override + Self-Concealment
- **PRD:** Structurally Unambiguous -> COMPROMISED.
- **Code:** Penalty = 50. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S14a: Write-Intercept (Missing Script)
- **PRD:** Structurally Unambiguous -> COMPROMISED.
- **Code:** Penalty = 70. In `STRUCTURALLY_UNAMBIGUOUS` set.
- **Status:** **PASS**

### S14b: Write-Intercept (Existing Script)
- **PRD:** Cannot produce CLEAN. Ceiling 60 (SUSPICIOUS). Not forced compromised.
- **Code:** Penalty = None. Ceiling = 60. `compute_verdict` respects ceiling.
- **Status:** **PASS**

### S15: Deposited Slash Command
- **PRD:** Penalty -55.
- **Code:** Penalty = 55.
- **Status:** **PASS**

### S16: Auto-enable MCP
- **PRD:** Ceiling 60 alone. With postinstall origin -> COMPROMISED.
- **Code:** Ceiling = 60. `compute_verdict` forces COMPROMISED if origin in `_POSTINSTALL_ORIGINS`.
- **Status:** **PASS**

### Verdict Logic
- **PRD:** < 40 = COMPROMISED. 40 <= score < 70 = SUSPICIOUS. 70+ = CLEAN.
- **Code:** Threshold logic matches PRD precisely.
- **Status:** **PASS**
