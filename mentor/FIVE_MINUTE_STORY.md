# THE FIVE-MINUTE STORY

This is the exact narrative for the 5-minute presentation. Stick to the script.

### 1. Problem
**Say:** "Developers are trusting AI agents to write code. Attackers are hijacking those agents by poisoning the instructions the agents read."
**Show:** (Slide/Diagram) An attacker PR dropping a hidden `.cursorrules` file.

### 2. Why agent trust files are different
**Say:** "You can't just grep these files. An agent configuration has global inheritance, local overrides, and nested execution hooks. You need a specialized pipeline."
**Do Not Claim:** Do not claim standard scanners are broken; claim they lack context.

### 3. Sentinel's four-stage architecture
**Say:** "Sentinel uses Layer 0 for context discovery, Layer 1 for deterministic rules, and a decoupled mathematical scoring engine. Future layers will add LLM analysis."
**Show:** `ARCHITECTURE.md` mermaid diagram.

### 4. Clean file
**Show:** `.\demo.ps1` (Step 1: Clean Baseline).
**Say:** "We don't invent threats. A standard, clean instruction file scores 100/100."

### 5. ChainDrop
**Show:** `.\demo.ps1` (Step 2: ChainDrop).
**Say:** "ChainDrop is a supply chain attack. It uninstalled its payload but left behind an agent hook pointing to a missing script. Our Layer 0 navigates Claude's JSON schema, and our Layer 1 catches the missing path, forcing COMPROMISED."
**Prove:** Point to `S10` output in the terminal.

### 6. S14b honesty boundary
**Show:** `.\demo.ps1` (Step 3: S14b).
**Say:** "This is an active write-interceptor. We cap it at 60 (Suspicious). We refuse to call this 'Compromised' because it could be a legitimate code formatter. We prioritize developer trust over scary alerts."

### 7. TrapDoor
**Show:** `.\demo.ps1` (Step 4: TrapDoor).
**Say:** "Visually, this file looks clean. But Sentinel catches the invisible Unicode used to hide the attack, plus the exfiltration URL shape, dropping the score to 0."
**Prove:** Point to the Agent-Impact reconstruction detailing the exfiltration risk.

### 8. Miasma
**Show:** `.\demo.ps1` (Step 5: Miasma).
**Say:** "Miasma re-encrypts its payload to beat hash scanners. Our Layer 1 structural fallback catches the Persona Override combined with the Hex Encoded payload."
**Do Not Claim:** Do not claim we used Semantic Displacement to catch it.

### 9. Deadbugz
**Show:** `.\demo.ps1` (Step 6: Deadbugz).
**Say:** "Deadbugz attacks MCP tool configurations. By parsing MCP JSON dynamically, we detect Tool Shadowing—naming a tool 'read_file' but asking for SSH access."
**Do Not Claim:** Do not claim we catch this dynamically in memory.

### 10. Benchmark
**Say:** "We ran our PRD rules against a 61-file corpus. We achieved 100% precision with zero false alarms. We intentionally accepted 92.3% recall because writing overly broad regex destroys developer trust."
**Prove:** Show `BENCHMARK_CARD.md`.

### 11. Limitation
**Say:** "Our biggest limitation today is conversational prompt injection. If an attacker asks nicely without using structural override language, Layer 1 misses it."

### 12. Next PRD-defined layer
**Say:** "That limitation is exactly why our architecture defines Layer 3—a dedicated LLM classifier designed to catch the semantic drift that Layer 1 misses."
