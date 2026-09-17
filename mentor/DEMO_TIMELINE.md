# MENTOR DEMO TIMELINE

**Total Duration:** ~4 Minutes
**Goal:** Prove deterministic Layer 0/Layer 1 functionality against known threat shapes.

### 0:00–0:30 | Opening Context & Clean Baseline
**What to show:** Execute `python -m sentinel.cli scan samples/demo_fixtures/clean_claude.md`
**What to say:** "We start with a verified-authentic developer instruction file. Sentinel doesn't invent threats to justify its existence. Clean files score 100/100, deterministic."
**What not to claim:** Do not claim it's "impossible to bypass" — claim only that standard structural attacks are absent.

### 0:30–1:00 | ChainDrop Vector (Missing Hook)
**What to show:** Execute `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/chaindrop/.claude/settings.json`
**What to say:** "ChainDrop left hooks behind after the payload was uninstalled. Sentinel's Layer 0 parser correctly navigates Claude's 3-level schema and flags missing scripts as an unambiguous compromise."
**What not to claim:** Do not claim we caught the *original* ChainDrop package upload, we caught the *residue* of the persistent hook.

### 1:00–1:40 | The S14b Honest Boundary
**What to show:** Execute `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/s14b/.claude/settings.json`
**What to say:** "Here is a write-interceptor. We bound this at 60/100 (Suspicious). We refuse to call this 'Compromised' because it could be a legitimate Prettier formatting hook. This proves we aren't manipulating thresholds for marketing; we explicitly defer semantic intent to human review or the future Layer 3 classifier."
**What not to claim:** Do not claim Sentinel can automatically distinguish a malicious write-interceptor from a benign one without sandbox execution (V2).

### 1:40–2:30 | The Text Attack (TrapDoor)
**What to show:** Execute `python -m sentinel.cli scan samples/trapdoor_style_demo.md`
**What to say:** "Visually, this looks like a clean markdown file. Sentinel detects the invisible Unicode payloads (S1) and the exfiltration URL shape (S5), driving the score immediately to 0."
**What not to claim:** Do not claim this is an ML detection. Emphasize that it is deterministic Layer 1 matching.

### 2:30–3:15 | The Miasma Vector
**What to show:** Execute `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc`
**What to say:** "Miasma re-encrypted its payload on every save to beat static hash scanners. Our Layer 1 catches the *structure* of the attack: a Persona Override combined with Self-Concealment language (S13), followed by an encoded blob (S7)."
**What not to claim:** Do NOT claim we caught this using Semantic Displacement. Semantic Displacement is the Layer 2 design for detecting Miasma; this demo proves our Layer 1 structural fallback catches it deterministically.

### 3:15–4:00 | Tool Shadowing (Deadbugz)
**What to show:** Execute `python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json`
**What to say:** "Deadbugz attacks MCP servers by mutating descriptions after approval. We prove that parsing MCP JSON dynamically (Layer 0) allows us to catch Tool Shadowing (S9) when a tool names itself 'read_file' but references SSH keys."
**What not to claim:** Do not claim Sentinel actively prevents Deadbugz at runtime memory. Claim only that Sentinel detects the Deadbugz tool-shadowing *pattern* in the manifest.
