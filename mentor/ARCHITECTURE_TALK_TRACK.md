# ARCHITECTURE TALK TRACK

Use this script when showing the Architecture slide. Emphasize what is built (V1) versus what is planned (Future).

### 1. DISCOVER (Layer 0) - *Implemented*
"Standard static analysis fails on AI config files because it lacks context. Our Layer 0 doesn't just read text; it parses the nested Claude JSON schema. It discovers local files, merges them with global configurations like `~/.claude.json`, and determines the file's package-manager origin (D2)."

### 2. DETECT (Layer 1) - *Implemented*
"Once we have context, Layer 1 applies 16 deterministic, structural rules (S1-S16). We scan for invisible Unicode, exfiltration URLs, persona overrides, missing hook paths, and tool shadowing. This is lightning-fast and offline."

### 3. SCORE (Arithmetic Engine) - *Implemented*
"We explicitly decoupled detection from verdict. Findings feed a mathematical scoring engine starting at 100. Some rules subtract points, some enforce a ceiling of 60 (Suspicious), and severe structural attacks force an unambiguous Compromised verdict."

### 4. TRACK (Layer 2) - *Future Design*
"Today we scan statelessly. In our future Layer 2, we will introduce `sentinel.lock`. This enables Semantic Displacement—measuring how much an agent's behavior has drifted from its baseline using vector math, protected by cryptographic HMAC signatures."

### 5. EXPLAIN (Layer 3) - *Future Design*
"Layer 1 misses purely conversational prompt injection. That's by design. Our future Layer 3 will pass ambiguous findings to a specialized LLM Classifier to catch semantic manipulation that structural regex misses."

### 6. GUIDE (Layer 4) - *Future Design*
"Finally, we don't want to just block developers. Our future Layer 4 is an interactive Chatbot that will guide the developer through remediating compromised agent instructions."
