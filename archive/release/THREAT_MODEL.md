# THREAT MODEL

*Refer to `docs/THREAT_MODEL_V1.md` for the comprehensive security breakdown.*

SENTINEL operates under the core assumption that AI Agent configurations (e.g. `CLAUDE.md`, `.claude.json`) are highly susceptible to malicious instruction injections (Prompt Overrides, Unicode Obfuscation, Write-Intercepts).

**Core Defensive Guarantees:**
1. **Offline & Read-Only Execution:** Scanning does not mutate the host filesystem or communicate with untrusted Command & Control channels.
2. **Deterministic Evaluation:** Rule enforcement is mathematical and avoids the hallucination risk of LLM-as-a-judge patterns.
3. **Graceful Degradation:** Should advanced Vector Similarity capabilities (Layer 2/3) crash or remain unavailable, SENTINEL defaults cleanly to rigorous Layer 1 protections rather than failing open.
4. **Secret Non-Leakage:** Embedded credentials detected in attacker payloads are redacted automatically before presentation.
