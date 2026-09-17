# EXPECTED DEMO OUTPUTS

The Sentinel V1 Mentor Demo uses inert, repository-local fixtures to demonstrate exact PRD compliance. 

### 1. Clean Baseline (`clean_claude.md`)
**Expected Verdict:** `CLEAN`
**Expected Score:** `100/100`
**What it demonstrates:** Sentinel's static analysis does not hallucinate threats in standard instruction documents. 

### 2. ChainDrop Vector (`chaindrop`)
**Expected Verdict:** `COMPROMISED`
**Expected Rules Fired:** `S10 (Hook References Missing Path)`
**What it demonstrates:** A `SessionStart` hook points to an uninstalled or missing file (`setup.mjs`). This is the exact signature of a malicious package that was uninstalled but left behind its agent-triggering configuration.

### 3. S14b Boundary (`s14b`)
**Expected Verdict:** `SUSPICIOUS`
**Expected Score:** `60/100` (Ceiling capped)
**Expected Rules Fired:** `S14b (Write-Intercept Hook - Existing Script Path)`
**What it demonstrates:** Sentinel correctly refuses to call an active write-interceptor "Clean", but refuses to call it "Compromised" without semantic analysis. It honestly bounds the score at 60 and recommends human review (a legitimate formatter hook).

### 4. TrapDoor Vector (`trapdoor_style_demo.md`)
**Expected Verdict:** `COMPROMISED`
**Expected Rules Fired:** `S1 (Invisible Unicode)`, `S5 (Network-Shaped Instruction)`
**What it demonstrates:** Detects zero-width characters used to bypass human review, coupled with an explicit `curl` / HTTP client exfiltration payload.

### 5. Miasma Vector (`miasma.mdc`)
**Expected Verdict:** `COMPROMISED`
**Expected Rules Fired:** `S13 (Persona Override with Self-Concealment)`, `S7 (Encoded Payload)`
**What it demonstrates:** Catches the 0x2ai style attack combining "Act as..." + "Don't tell the user..." alongside a hex-encoded binary payload within a plain-text markdown file.

### 6. Deadbugz Vector (`mcp.json`)
**Expected Verdict:** `SUSPICIOUS`
**Expected Rules Fired:** `S9 (Tool Shadowing)`
**What it demonstrates:** Detects an MCP server attempting to shadow a known trusted tool name (`read_file`) while requesting sensitive file paths (`.ssh`, `.aws`).
