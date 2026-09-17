# 60-SECOND MENTOR CHEAT SHEET

**WHO WE ARE:** We built Sentinel, a deterministic security scanner for AI agent trust files.
**WHY IT MATTERS:** AI Agents read configs silently. Attackers hide malicious instructions in these configs to hijack the agent (Supply Chain Attacks).
**WHAT WE BUILT:** Layer 0 (Context Parser) + Layer 1 (Deterministic Rule Engine).
**HOW IT WORKS:** We parse the nested agent configurations (L0) and apply 16 mathematical rules (L1) to produce a severity score without needing expensive LLMs.
**WHAT THE DEMO SHOWS:** Six fixtures proving we catch invisible Unicode, hook survivability, exfiltration URLs, persona overrides, and tool shadowing at millisecond speeds.
**WHAT THE BENCHMARK SAYS:** 100% Precision, 92.3% Recall on 61 production-grade files. Zero false positives.
**BIGGEST LIMITATION:** Purely conversational prompt injection (Layer 1 is structural, not semantic).
**WHAT COMES NEXT:** Layer 2 (Semantic Displacement + `sentinel.lock` cryptography) and Layer 3 (LLM Classifier).
