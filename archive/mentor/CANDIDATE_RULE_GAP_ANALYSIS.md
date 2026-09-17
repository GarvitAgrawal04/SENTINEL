# CANDIDATE RULE GAP ANALYSIS

The corpus defines 49 candidate rules. Sentinel currently implements 16 deterministic Layer 1 rules.
This is not a defect. Sentinel is not designed to be a 300-rule regex engine (like AgentAuditKit).

### Analysis of Gaps

**1. Grep-Style Behaviors (e.g., Credential Regex)**
- **Candidate Gap:** The corpus suggests rules for `CRED_ENV_ACCESS` and `CRED_REPO_SECRET`.
- **Why it's missing:** Layer 1 explicitly avoids basic keyword matching on "token", "password", or "ssh" to maintain 100% precision. Benign test suites frequently use these keywords. 
- **Future Layer:** Layer 3 Classifier (semantic context is required to determine if the credential access is malicious).

**2. Bash Script Execution (e.g., `EXEC_INTERPRETER_INLINE`)**
- **Candidate Gap:** Standalone bash script parsing.
- **Why it's missing:** Sentinel V1 operates on Agent Instruction files (markdown, json), not arbitrary `.sh` files.
- **Future Layer:** Layer 2 Sandbox (Bash static analysis and simulation).

**3. Cross-File Policies (e.g., `XFILE_CONTRADICTION`)**
- **Candidate Gap:** Detecting when a global rule is contradicted by a local rule.
- **Why it's missing:** S8 is designed for this but it requires a multi-file batch to be submitted to the API. Current offline CLI usage scans file-by-file contextually.
- **Future Layer:** Fully covered conceptually, requires IDE integration to submit full context.

**4. Semantic Drift (e.g., `DRIFT_SEMANTIC`)**
- **Candidate Gap:** Pure paraphrasing of instructions.
- **Why it's missing:** Layer 1 is a structural engine. 
- **Future Layer:** Layer 2 (Semantic Displacement cosine distance).

### Final Classification of the 49 Candidates
- **ALREADY COVERED (Structural):** ~15 rules (Hooks, MCP, Exfiltration, Overrides, Unicode)
- **PARTIALLY COVERED:** ~10 rules (Requires hook context)
- **SHOULD BE CONSIDERED FOR V1.x:** 0 (We will not add more grep rules to Layer 1)
- **LAYER 2 (Semantic/Execution):** ~12 rules
- **LAYER 3 (Intent Classification):** ~8 rules
- **CROSS-FILE / MANIFEST:** ~4 rules
