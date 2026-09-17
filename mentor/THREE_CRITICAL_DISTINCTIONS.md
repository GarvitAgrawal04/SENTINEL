# THE THREE CRITICAL DISTINCTIONS

During the presentation, use these three exact distinctions to instantly clarify any confusing boundaries.

### A. DETECTION vs VERDICT
A rule can detect an attack pattern without forcing the entire file to be `COMPROMISED`.

**Example:** Sentinel detects the S3 MCP Injection pattern and applies a -35 penalty. Because the baseline score is 100, the resulting score is 65. The verdict threshold for 65 is `SUSPICIOUS`, not `COMPROMISED`. 
**Why this matters:** We do not manipulate thresholds for marketing purposes. We mathematically bound risks to defer ambiguous semantic intent to human review.

### B. CURRENT IMPLEMENTATION vs PRD ROADMAP
Do not blur the lines between what is built today and what is designed for tomorrow.

**Current (V1):** Layer 0 Context Discovery, Deterministic Layer 1 Rules (S1-S16), Mathematical Scoring, CLI/API output.
**Future (V1.5/V2):** Layer 2 (Semantic Displacement, `sentinel.lock` HMAC signatures), Layer 3 (LLM Classifier), Layer 4 (Remediation Chatbot).
**Why this matters:** Honesty builds credibility. Claiming Layer 2 capabilities today destroys trust when the mentor asks to see the code.

### C. STRUCTURAL DETECTION vs SEMANTIC DETECTION
This is the core of Sentinel's philosophy.

**Structural (Layer 1):** Fast, deterministic markers. Examples: Invisible Unicode blocks, hex-encoded payloads, missing hook paths, tool shadowing strings.
**Semantic (Future Layer 2/3):** Context-aware behavioral intent. Examples: Measuring if a prompt drifted toward "exfiltration intent", understanding a conversational prompt injection.
**Why this matters:** When a mentor points out a subtle paraphrase attack that bypasses Layer 1, agree with them! State: "That is a semantic attack. Layer 1 is a structural engine. That exact bypass validates our design for the future Layer 3 classifier."
