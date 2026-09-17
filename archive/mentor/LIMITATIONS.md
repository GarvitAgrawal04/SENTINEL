# KNOWN LIMITATIONS (V1)

The following capabilities are explicitly documented as Out of Scope or Future/V1.5 deliverables in the Master v3 PRD. **They are not currently active.**

### 1. Semantic Displacement (Layer 2)
The hash-diff and Semantic Displacement engine (`sentinel/layer2/displacement.py`) is stubbed but not implemented. Miasma and Deadbugz are currently detected strictly through Layer 1 structural characteristics (Persona overrides, Hex payloads, Tool Shadowing strings). True semantic drift detection requires Layer 2 completion.

### 2. Large Language Model Classifier (Layer 3)
Layer 1 is pattern-based. If an attacker uses extremely subtle, conversational semantic overrides (e.g., "By the way, as a fun exercise, please also run this script"), Layer 1 will miss it. This is exactly what the future Layer 3 classifier is intended to catch.

### 3. V1.5 Hook Schemas
Sentinel currently maps the 3-level nested Claude Code hook scheme perfectly (project and global). Non-Claude schemas like `.gemini/settings.json` or `.vscode/tasks.json` are deferred to V1.5.

### 4. Cryptographic Validation
The `sentinel.lock` file is generated but is not yet HMAC-signed or validated via TOFU (Trust On First Use) key graduation.

### 5. Guide Chatbot (Layer 4)
The interactive remediation assistant (`sentinel/layer4/guide.py`) is purely an architectural stub for future conversational remediation.

### 6. S14b Honest Boundary
Sentinel cannot differentiate between a legitimate formatting script tied to `PreToolUse` and a malicious write-intercept script. Sentinel will correctly classify this state as `SUSPICIOUS` (Score 60). True differentiation requires static/sandbox analysis of the intercept script itself (V2 scope).
