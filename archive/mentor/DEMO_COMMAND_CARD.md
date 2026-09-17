# MENTOR DEMO COMMAND CARD

### Primary Automated Sequence
Use this to run the entire 4-minute presentation flawlessly.
```powershell
.\demo.ps1
```

---

### Individual Manual Commands
If the mentor asks you to run a step manually to prove it isn't mocked, use these exact commands.

**1. Clean Baseline**
- **Command:** `python -m sentinel.cli scan samples/demo_fixtures/clean_claude.md`
- **Purpose:** Establishes the 100/100 baseline.
- **Expected:** `CLEAN`

**2. ChainDrop (Missing Target)**
- **Command:** `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/chaindrop/.claude/settings.json`
- **Purpose:** Demonstrates D3 hook parsing and S10 survivability.
- **Expected:** `COMPROMISED` (S10)

**3. S14b Honest Boundary**
- **Command:** `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/s14b/.claude/settings.json`
- **Purpose:** Proves we use mathematical ceilings to avoid false-flagging formatters.
- **Expected:** `SUSPICIOUS` (S14b, Score capped at 60)

**4. TrapDoor**
- **Command:** `python -m sentinel.cli scan samples/trapdoor_style_demo.md`
- **Purpose:** Proves detection of visually hidden payloads.
- **Expected:** `COMPROMISED` (S1 Unicode, S5 Exfiltration)

**5. Miasma**
- **Command:** `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc`
- **Purpose:** Proves structural detection of 0x2ai evasion techniques.
- **Expected:** `COMPROMISED` (S4, S7, S13)

**6. Deadbugz**
- **Command:** `python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json`
- **Purpose:** Proves MCP manifest parsing and tool-shadow detection.
- **Expected:** `SUSPICIOUS` (S9 Tool Shadowing)
