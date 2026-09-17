# SENTINEL V1 THREAT MODEL

## 1. Assets
- **Project Configuration:** Developer environment, runtime configurations, build scripts.
- **Hooks:** Git pre-commit, setup scripts, and automated task runners.
- **MCP Definitions:** Model Context Protocol configurations.
- **Trust Baseline:** `sentinel.lock` file tracking authorized project changes.
- **Credentials:** API Keys, tokens, client secrets stored in configuration scopes.

## 2. Attack Surfaces
- **Config Files:** Manipulation of JSON settings (e.g., `settings.json`, `claude.json`).
- **Hooks & Build Steps:** Overwriting benign scripts with malicious tasks.
- **Slash Commands & Tool Shadows:** Overriding system capabilities or mirroring legitimate endpoints.
- **Unicode / Encoded Content:** Invisible control characters bypassing human review.
- **Baseline Manipulation:** Forcing unauthorized updates to the vector baseline.

## 3. Trust Boundaries
- **Filesystem (External):** SENTINEL operates as a strict **Read-Only** entity over user files.
- **Baseline (Internal):** `sentinel.lock` must be protected by standard Version Control mechanisms (Git).
- **Scanner / Pipeline (Internal):** Deterministic evaluation decoupled from untrusted external APIs.
- **Output (External):** JSON & CLI streams redact raw secret payloads to prevent upstream data-leaks.

## 4. Capabilities Handled (V1)
- Prompt Injection & Overrides (Rule S4, S13)
- Invisible Payload Delivery (Rule S1, S7)
- Trust Delegation / Exfiltration (Rule S5, S11, S12)
- Tool Subversion & Write Interception (Rule S9, S14)
- Missing Hooks (Rule S10)
- Structural Similarity Matching (Layer 2 & 3 vectors).

## 5. Capabilities Not Handled (V1)
- **Automatic Remediation:** The system will not automatically rewrite your project files or invoke package managers to uninstall dependencies.
- **Network Validation:** The scanner does not actively ping or interrogate discovered endpoints/C2s.
- **LLM Reasoning:** Semantic narratives explaining the attacker's trajectory are deferred to V1.5.

## 6. Fail-Safe Behavior
If dependencies, environment paths, models, or network availability fail, SENTINEL defaults to Layer 1 deterministic matching. It **does not** return a false CLEAN verdict if a subsystem crashes. It preserves error context and proceeds deterministically.
