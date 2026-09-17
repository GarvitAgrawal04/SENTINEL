# CLAIM -> PROOF MAP

This document audits significant claims to ensure they are demonstrably true using the current implementation, and explicitly lists known boundaries.

### 1. "Sentinel detects hidden Unicode"
- **Proof:** S1 rule fires on zero-width characters and forces a `COMPROMISED` verdict.
- **How to demonstrate:** `python -m sentinel.cli scan samples/trapdoor_style_demo.md`
- **Limitation:** Detects standard zero-width invisible Unicode block; does not detect visual lookalikes (homoglyphs) without future Layer 2/3 parsing.

### 2. "Sentinel detects hook survivability"
- **Proof:** S10 rule fires when a `settings.json` hook (like `SessionStart`) targets a script path that no longer exists on disk.
- **How to demonstrate:** `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/chaindrop/.claude/settings.json`
- **Limitation:** Relies on local filesystem access during scan to verify path existence.

### 3. "Sentinel distinguishes suspicious from compromised"
- **Proof:** Scoring formula applies a ceiling (60) for ambiguous rules (S14b, S16 alone), classifying them as `SUSPICIOUS` rather than mathematically forcing a `COMPROMISED` failure.
- **How to demonstrate:** `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/s14b/.claude/settings.json`
- **Limitation:** It defers the final security determination to the human (or future Layer 3 classifier).

### 4. "Sentinel discovers global Claude configuration"
- **Proof:** `discover_global_surfaces()` in Layer 0 specifically parses `~/.claude/settings.json` and `~/.claude.json`.
- **How to demonstrate:** `python -m sentinel.cli scan .` (Will actively find and scan the presenter's `~/.claude.json`).
- **Limitation:** Hardcoded to Claude and standard OS paths (V1.5 covers Gemini/Windows).

### 5. "Sentinel produces an auditable score"
- **Proof:** The CLI output prints the exact mathematical trace mapping the 100 baseline minus penalties and forced bounds.
- **How to demonstrate:** Execute any demo command and point to the `Score arithmetic: raw=100, L1=-120...` line.
- **Limitation:** Layer 2 (displacement distance) and Layer 3 (confidence bonus) are intentionally zeroes today.

### 6. "Sentinel is offline-first for deterministic Layer 0-1"
- **Proof:** Running `demo.ps1` or any benchmark command completes locally in milliseconds without hitting the Groq API (Layer 3).
- **How to demonstrate:** Unplug network cable, run `.\demo.ps1`.
- **Limitation:** Does not query external LLMs to bypass novel evasion techniques.

### 7. "Sentinel addresses Miasma"
- **CURRENT VERIFIED CAPABILITY:** Layer 1 deterministically catches the structural markers of the Miasma payload (S13 Persona Override + S7 Encoded Payload) as long as it touches disk.
- **PRD-DESIGNED FUTURE CAPABILITY:** Layer 2 Semantic Displacement is designed to track behavioral prompt drift even if the payload's encoding or text completely changes.
- **How to demonstrate:** `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc`
- **Limitation:** A purely semantic rewrite (avoiding S4/S13 language and S7 hex) would bypass the current Layer 1 implementation.

### 8. "Sentinel addresses Deadbugz"
- **CURRENT VERIFIED CAPABILITY:** Layer 1 deterministically detects the Deadbugz tool-shadowing pattern in the static MCP manifest (S9 shadowing `read_file` + referencing `.ssh`).
- **PRD-DESIGNED FUTURE CAPABILITY:** Layer 2 Semantic Displacement is designed to monitor runtime MCP tool metadata to catch when a tool changes its description *after* approval.
- **How to demonstrate:** `python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json`
- **Limitation:** V1 only scans the static `.json` configuration file, not the live memory state of the MCP server.
