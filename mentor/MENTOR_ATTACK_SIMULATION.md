# MENTOR ATTACK SIMULATION

These 25 questions simulate a skeptical cybersecurity review. Use these exact boundaries to avoid accidentally overclaiming future capabilities.

### 1. Why isn't this just regex?
**Best Answer:** Regex is context-blind. Sentinel uses Layer 0 AST parsing to understand nested JSON hook inheritance (e.g., local hooks overriding global hooks), relies on package-manager origin heuristics (D2), and applies mathematical bounds (ceilings) that standard grep scanners cannot support.
**Evidence:** S14b ceilings, D2 origin tracking.
**One-sentence:** Regex doesn't understand JSON inheritance or mathematical severity ceilings; Sentinel does.
**Do Not Say:** "It uses advanced AI." (Layer 1 does not).

### 2. Why not just use an LLM?
**Best Answer:** LLMs are slow, expensive, and susceptible to the exact same prompt injections they are scanning for. A deterministic Layer 1 pipeline strips 95% of the obvious attack volume at millisecond speeds, leaving only complex semantic drift for the LLM.
**Evidence:** The 4-minute offline demo runs locally in milliseconds.
**One-sentence:** LLMs are too slow and vulnerable to injection to act as the first line of defense.
**Do Not Say:** "LLMs are useless."

### 3. How do you know the rule isn't producing false positives?
**Best Answer:** We achieved 100% precision on our validation corpus of 48 production agent-instruction files. For instance, we specifically bounded the S14b write-interceptor at `SUSPICIOUS` rather than `COMPROMISED` because we recognize it mathematically overlaps with benign code formatters.
**Evidence:** 0/48 False Alarms on the benchmark.
**One-sentence:** We tuned the math and verified it against 48 production files, achieving 0 false positives.
**Do Not Say:** "It will never produce a false positive."

### 4. Why 100% precision but 92.3% recall?
**Best Answer:** We optimize for developer trust. A noisy scanner that flags every "ignore previous instructions" joke gets uninstalled. We accepted one False Negative (a subtle conversational prompt injection) because catching it with Layer 1 regex would have caused massive false positives on benign files. That miss proves exactly why we designed the future Layer 3 classifier.
**Evidence:** `teammate_moderate_claude.md` miss.
**One-sentence:** We prioritize zero false positives to maintain trust; semantic misses are the domain of our future Layer 3.
**Do Not Say:** "We just didn't have time to write the regex for it."

### 5. What exactly is your benchmark?
**Best Answer:** It is a 61-file corpus (13 malicious, 48 clean) designed to measure the deterministic recall of our PRD Layer 1 rules against known attack structures (TrapDoor, Miasma, ChainDrop, Deadbugz, etc.).
**Evidence:** The `benchmark/run_benchmark.py` outputs structural detection (TP/FP).
**One-sentence:** A static corpus measuring deterministic Layer 1 detection of structural attacks.
**Do Not Say:** "It's an adversarial robustness benchmark."

### 6. Why is S14b only SUSPICIOUS?
**Best Answer:** An existing `PreToolUse` write hook is structurally indistinguishable from a legitimate auto-formatter like Prettier. Automatically failing it breaks developer workflows. SUSPICIOUS honestly defers the decision to human review.
**Evidence:** `s14b` demo fixture scores exactly 60.
**One-sentence:** We cannot statically differentiate a malicious hook script from a benign formatter script in Layer 1.
**Do Not Say:** "We catch malicious write hooks."

### 7. What happens if the hook script exists and is malicious?
**Best Answer:** In Layer 1, it is flagged as `SUSPICIOUS` (S14b). Sentinel V1 does not perform sandboxed execution or bash-script static analysis to prove the script itself is malicious. That is a V2 capability.
**Evidence:** `S14b` ceiling behavior.
**One-sentence:** V1 bounds it at Suspicious and alerts the human to review the referenced script.
**Do Not Say:** "Sentinel scans the bash script."

### 8. What happens on first scan?
**Best Answer:** Sentinel parses the context (Layer 0), applies the 16 deterministic rules (Layer 1), deducts from a 100 baseline, applies severity ceilings, and outputs a final grade.
**Evidence:** The standard CLI output trace.
**One-sentence:** It parses the config tree, runs the rules, and computes a mathematical score.
**Do Not Say:** "It learns your codebase."

### 9. What happens if a malicious configuration is already present?
**Best Answer:** Sentinel operates statelessly in Layer 1. It scans the current file state. If a malicious config is already present (e.g., TrapDoor invisible Unicode), it flags it immediately upon scanning.
**Evidence:** TrapDoor demo.
**One-sentence:** Layer 1 is stateless and catches existing malicious structures instantly.
**Do Not Say:** "It blocks the install."

### 10. How does D2 know a package deposited a file?
**Best Answer:** D2 compares the file's modification timestamp against the nearest `package-lock.json` modification timestamp (within a 60-second window). If they match, it marks the origin as `postinstall-suspected`.
**Evidence:** `sentinel/layer0/origin.py` heuristics.
**One-sentence:** It correlates file creation time with package-lock modification time.
**Do Not Say:** "It intercepts npm."

### 11. What exactly does S6 do?
**Best Answer:** If a file's origin is tagged by D2 as a package manager installation, S6 applies a baseline -15 penalty because auto-generated agent instructions from third-party dependencies are a known supply-chain attack vector.
**Evidence:** `sentinel/rules/s6_new_file.py` checking origin.
**One-sentence:** It penalizes agent-trust files that were deposited silently by an npm/pip install.
**Do Not Say:** "It performs a diff against sentinel.lock."

### 12. What is the difference between S6 and Layer 2?
**Best Answer:** S6 is a structural trigger (the file came from npm). Layer 2 (Semantic Displacement) is the future capability that measures *how much* that file changed the agent's behavior compared to the baseline `sentinel.lock`.
**Evidence:** S6 is implemented. Layer 2 is a stub.
**One-sentence:** S6 flags that a dependency changed the file; Layer 2 measures how dangerous that change is.
**Do Not Say:** "S6 is Layer 2."

### 13. Where is Semantic Displacement?
**Best Answer:** It is thoroughly designed in the Master v3 PRD but intentionally deferred to the post-mentor build phase. Today we are demonstrating the deterministic Layer 1 foundation that it will build upon.
**Evidence:** `sentinel/layer2/displacement.py` stub.
**One-sentence:** It is a designed future capability, not implemented in V1.
**Do Not Say:** "We built it."

### 14. Did you actually catch Miasma?
**Best Answer:** Yes, our Layer 1 structural fallback caught the Miasma payload deterministically because it relies on a Persona Override (S13) paired with an encoded payload block (S7). 
**Evidence:** Miasma demo outputting 0/100.
**One-sentence:** We caught its structural markers in Layer 1, though true semantic tracking of Miasma requires Layer 2.
**Do Not Say:** "We used semantic displacement to catch Miasma."

### 15. Did you actually catch Deadbugz?
**Best Answer:** Yes, we caught the Deadbugz static manifest pattern by detecting an MCP tool that shadows a trusted name (`read_file`) while requesting sensitive file access (`.ssh`).
**Evidence:** Deadbugz demo outputting 40/100.
**One-sentence:** We detect the static Tool Shadowing pattern in Layer 1; runtime tracking is scheduled for V2.
**Do Not Say:** "We stop Deadbugz in memory."

### 16. What happens if the attacker paraphrases the instruction?
**Best Answer:** If they paraphrase it enough to avoid our S4 (Override) and S13 (Persona) regexes, Layer 1 will miss it. That is exactly what the future Layer 3 LLM classifier is designed to solve.
**Evidence:** The 1 False Negative in our benchmark.
**One-sentence:** Layer 1 misses semantic paraphrasing, which validates our design for the Layer 3 LLM.
**Do Not Say:** "Our regex is foolproof."

### 17. What happens if the payload is hidden in another encoding?
**Best Answer:** We catch standard Base64 and Hex blocks embedded in text files (S7). If they use an esoteric encoding, Layer 1 might miss the payload itself, but it usually still catches the accompanying override instructions needed to execute it.
**Evidence:** S7 rule code.
**One-sentence:** We catch Base64 and Hex, but heavily fragmented obfuscation requires Layer 2 diffing.
**Do Not Say:** "We detect all encodings."

### 18. Can Sentinel itself be attacked?
**Best Answer:** Currently, yes, if the attacker has filesystem access to rewrite Sentinel's rule definitions. The defense against this is the `sentinel.lock` HMAC cryptographic boundary, which is designed for Layer 2.
**Evidence:** Cryptography is explicitly documented as a future state.
**One-sentence:** V1 relies on standard file permissions; V2 adds cryptographic HMAC verification.
**Do Not Say:** "Sentinel is tamper-proof."

### 19. Can your scanner be disabled?
**Best Answer:** If an attacker modifies the GitHub Action or pre-commit hook that invokes Sentinel, yes. Secure integration requires branch protection rules enforcing the Sentinel action, which is standard CI/CD practice.
**Evidence:** GitHub action integration (`action/scan_pr.py`).
**One-sentence:** It requires standard CI/CD branch protection to enforce.
**Do Not Say:** "It can never be bypassed."

### 20. What happens if sentinel.lock is modified?
**Best Answer:** In the future Layer 2 design, `sentinel.lock` is HMAC-signed. If it is modified, the signature validation fails, and Sentinel halts the agent environment (TOFU validation).
**Evidence:** PRD A 13.4 design.
**One-sentence:** Our future Layer 2 design uses HMAC signatures to prevent `sentinel.lock` tampering.
**Do Not Say:** "It currently halts execution."

### 21. What is actually V1 versus V1.5?
**Best Answer:** V1 (Today) is the complete deterministic Layer 0/Layer 1 scanner mapping Claude Code hook hierarchies. V1.5 covers non-Claude schemas like `.gemini/settings.json` and `.vscode/tasks.json`.
**Evidence:** Limitations document.
**One-sentence:** V1 covers Claude; V1.5 expands to other AI assistants.
**Do Not Say:** "We support all IDEs today."

### 22. What remains for V2?
**Best Answer:** Static analysis of bash scripts referenced by hooks, sandboxed simulation, runtime memory scanning, and agent-to-agent handoff integrity.
**Evidence:** PRD limitations.
**One-sentence:** Deep execution analysis and cross-agent handoffs.
**Do Not Say:** "V2 is already done."

### 23. Why should anyone trust your benchmark?
**Best Answer:** Because it is an honest, static corpus of 61 production-grade files containing exact reconstructions of documented attacks (Miasma, TrapDoor). It doesn't prove Sentinel is unbreakable; it proves Sentinel's Layer 1 mathematical rules perform exactly as designed without hallucination.
**Evidence:** 100% precision with documented false negative.
**One-sentence:** It proves our rules work as specified without generating false alarms.
**Do Not Say:** "It proves we are secure."

### 24. What is your biggest technical limitation?
**Best Answer:** Purely conversational prompt injection. Layer 1 is a structural engine. If an attacker asks nicely ("By the way, as a fun game, run this command"), Layer 1 misses it. We are building the Layer 3 LLM specifically to close this gap.
**Evidence:** The 92.3% recall on the benchmark.
**One-sentence:** We cannot catch conversational semantic manipulation without the future Layer 3 classifier.
**Do Not Say:** "We don't have any limitations."

### 25. Why build this instead of relying on Claude's built-in safety?
**Best Answer:** Claude's built-in safety protects the *model* from outputting hate speech. Sentinel protects the *local environment* from the model executing malicious instructions deposited via the supply chain.
**Evidence:** PRD architecture.
**One-sentence:** Claude secures the cloud; Sentinel secures the developer's laptop.
**Do Not Say:** "Claude is insecure."
