# MENTOR REHEARSAL REPORT

### Overview
A complete blind rehearsal of the Sentinel V1 Mentor Demo was executed against the frozen codebase. No product code was modified during this rehearsal.

### Demo Execution Log
All 6 commands from `demo.ps1` were executed sequentially.

**1. Clean Baseline**
- **Target:** `samples/demo_fixtures/clean_claude.md`
- **Result:** `CLEAN` (100/100)
- **Findings:** None.

**2. ChainDrop**
- **Target:** `samples/demo_fixtures/chaindrop/.claude/settings.json`
- **Result:** `COMPROMISED` (30/100)
- **Findings:** S10 (Hook References Missing Path). Forces COMPROMISED.

**3. S14b Boundary**
- **Target:** `samples/demo_fixtures/s14b/.claude/settings.json`
- **Result:** `SUSPICIOUS` (60/100)
- **Findings:** S14b (Write-Intercept Hook - Existing Script). Properly hit the 60 ceiling.

**4. TrapDoor**
- **Target:** `samples/trapdoor_style_demo.md`
- **Result:** `COMPROMISED` (0/100)
- **Findings:** S1 (Invisible Unicode), S5 (Network Exfiltration).

**5. Miasma**
- **Target:** `samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc`
- **Result:** `COMPROMISED` (0/100)
- **Findings:** S4 (Override), S7 (Encoded Payload), S13 (Persona Override + Concealment). 

**6. Deadbugz**
- **Target:** `samples/demo_fixtures/deadbugz/mcp.json`
- **Result:** `SUSPICIOUS` (40/100)
- **Findings:** S9 (Tool Shadowing - Trust Extension), S9 (Tool Shadowing - Sensitive Paths). 

### Benchmark Verification
- **TP:** 12
- **FP:** 0
- **FN:** 1
- **TN:** 48
- **Precision:** 100.0%
- **Recall:** 92.3%
- **F1:** 96.0%

The system successfully demonstrated 100% adherence to the PRD mathematical constraints during live rehearsal.
