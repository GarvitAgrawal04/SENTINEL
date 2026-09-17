# MENTOR Q&A PREPARATION

### 1. What exactly does Sentinel detect today?
Sentinel detects deterministic, structural markers of agent manipulation (Layer 1). This includes invisible Unicode, exfiltration URLs, persona overrides, write-intercept hooks, missing target files, encoded binary payloads in text configs, and tool shadowing.

### 2. Why do you need Layer 0 separately from Layer 1?
Layer 1 is blind text scanning. Layer 0 provides the vital context of *what* a file is. Scanning a `settings.json` file as plain text misses the hierarchical nature of `PreToolUse` hooks and whether a project-local configuration shields against a compromised global configuration.

### 3. Why is S14b SUSPICIOUS instead of COMPROMISED?
S14b detects a `PreToolUse` hook attached to file modifications. This is the exact shape of a malicious interceptor, but it is *also* the exact shape of a legitimate auto-formatter. Labeling it `COMPROMISED` creates massive false positives. Labeling it `SUSPICIOUS` (Score 60) honestly defers the decision to human review.

### 4. What happens if the malicious hook script exists?
If the script exists, it triggers S14b (`SUSPICIOUS`). If the script was removed but the hook remains (e.g. ChainDrop style failed cleanup), it triggers S10 (`COMPROMISED`).

### 5. How does Sentinel distinguish local and global Claude hooks?
Layer 0 parses both `.claude/settings.json` and `~/.claude/settings.json`. It merges arrays where specific scopes override global scopes, accurately determining if a local project inherits a global hook or overrides it, reporting the true effective state.

### 6. Why does S16 alone not mean COMPROMISED?
`enableAllProjectMcpServers: true` is a severe security risk, but it is also a documented, legitimate configuration option that real developers use for convenience. Automatically compromising it breaks standard workflows. However, if it appears *alongside* a freshly modified package manifest (`postinstall` origin), it becomes a highly probable attack and is forced to `COMPROMISED`.

### 7. What happens on the first scan?
Layer 1 evaluates the rules mathematically starting from 100. Any findings deduct from the baseline, apply ceilings, or force a verdict.

### 8. What is currently implemented versus planned in Layer 2?
Currently, Layer 2 (`sentinel/layer2/displacement.py`) is an unvalidated architectural stub. Hash diffing, HMAC `sentinel.lock` verification, and Semantic Displacement clustering are deferred to post-mentor implementation.

### 9. How would Semantic Displacement address Miasma?
*Design Rationale:* Miasma constantly re-encrypts its payload to defeat static hashes. Semantic Displacement measures the *behavioral intent* of the prompt drift. Even if the text changes entirely, the vector displacement toward the "Override" cluster remains mathematically obvious. (*Note: This is design rationale; Semantic Displacement is not yet implemented*).

### 10. What exactly is your evidence for Deadbugz coverage?
*Current Deterministic Detection:* S3 and S9 rules currently detect Deadbugz by flagging tool names that shadow known-trusted tools (e.g. `read_file`) and looking for sensitive filesystem targets (`.ssh`, `.aws`) in the manifest strings.
*Future Design:* The Layer 2 Semantic Displacement engine will explicitly track MCP tool metadata over time to catch runtime description mutations.

### 11. How is Sentinel different from a plain regex scanner?
Sentinel merges AST-aware JSON parsing (Layer 0 hook structures, origin heuristics) with mathematical score bounding (Ceilings and Unambiguous Locks) to produce graded, actionable agent-impact analyses, rather than simple grep matches.

### 12. Why not just use an LLM?
LLMs are slow, expensive, and subject to the exact same prompt injections they are trying to detect. A deterministic pipeline (L0/L1) strips 95% of the obvious attack surface at millisecond speeds, leaving only ambiguous semantic drift for the LLM (L3) to analyze.

### 13. What happens if Sentinel itself is compromised?
If the attacker edits the rules, Sentinel fails. This is exactly what the future `sentinel.lock` cryptographic HMAC signature (Layer 2) is designed to solve by enforcing a trusted execution boundary.

### 14. What are the benchmark numbers?
**Corpus:** 13 malicious, 48 clean files.
**True Positives:** 12
**False Positives:** 0
**False Negatives:** 1
**True Negatives:** 48
**Precision:** 100.0%
**Recall:** 92.3%
**F1 Score:** 96.0%

### 15. What attacks does Sentinel NOT catch?
Sentinel currently cannot catch purely conversational semantic manipulations (e.g. subtle phrasing attacks that bypass static regex) because Layer 3 is not fully active. It also cannot analyze the inside of external bash scripts referenced by hooks (V2 scope).
