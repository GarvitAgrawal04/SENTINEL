# CLAIM AUDIT

This document records the exact safety boundaries for claims made during the mentor presentation.

### CLAIM 1: "S1-S16 are 100% Complete"
- **Status:** TRUE
- **Why:** S6 has been fully implemented as a deterministic Layer 1 trigger using the existing Layer 0 (D2) package origin heuristics. The dependency on `sentinel.lock` (Semantic Displacement) is correctly left to Layer 2, while the S6 Layer 1 penalty operates deterministically on origin.
- **Safe Wording:** "S1-S16 are 100% implemented in Layer 1. Their outputs feed into Layer 2 for further semantic bounds, but Layer 1 operates completely deterministically today."

### CLAIM 2: "Semantic Displacement caught Miasma"
- **Status:** CONTRADICTION
- **Why:** Layer 2 Semantic Displacement is not implemented. Our current detection of Miasma in the demo relies purely on Layer 1 (S13 Persona Override + S7 Encoded Payload). 
- **Safe Wording:** "Our Layer 1 fallback caught the Miasma attack structure deterministically. Semantic Displacement is our Layer 2 design for catching the drift."

### CLAIM 3: "Sentinel detects the Deadbugz attack"
- **Status:** TRUE, BUT REQUIRES QUALIFICATION
- **Why:** We detect the Deadbugz *static manifest pattern* (Tool Shadowing via S9 and S3). We do not yet detect Deadbugz *runtime semantic drift*.
- **Safe Wording:** "Sentinel deterministically detects the Deadbugz tool-shadowing manifest pattern in Layer 1. Runtime semantic displacement is scheduled for V2."

### CLAIM 4: "Sentinel has 100% Precision and 100% Recall"
- **Status:** FALSE
- **Why:** Sentinel achieves 100% Precision but only 92.3% Recall on the benchmark corpus, as it legitimately misses a conversational prompt injection (`teammate_moderate_claude.md`).
- **Safe Wording:** "Our Layer 1 deterministic engine achieved 100% precision and 92% recall on our validation set. The missed case correctly proves the necessity of the future Layer 3 classifier."

### CLAIM 5: "Sentinel is Tamper-Proof"
- **Status:** FALSE
- **Why:** Cryptographic verification (`sentinel.lock` HMAC) is not implemented yet.
- **Safe Wording:** "Sentinel currently relies on standard file permissions. Cryptographic tamper-proofing via HMAC is scoped for Layer 2."
