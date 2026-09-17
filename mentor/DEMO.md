# MENTOR DEMO SEQUENCE

**Duration:** ~4-5 minutes
**Tooling:** PowerShell, `sentinel.cli`

**Prerequisites:**
1. A clean checkout of the repository.
2. The `samples/demo_fixtures` folder intact.
3. No external internet or API keys required (Layer 3 disabled).

### Step 0: Execute Automated Demo Script
Run the interactive `demo.ps1` script from the repository root:
```powershell
.\demo.ps1
```
*(The script will pause after each step. Press any key to advance.)*

### Manual Fallback Sequence

If you prefer to run the commands manually to prove they aren't mocked:

**1. Clean Baseline (Verified Authentic)**
```powershell
python -m sentinel.cli scan samples/demo_fixtures/clean_claude.md
```

**2. Hook Survivability (ChainDrop Vector)**
```powershell
python -m sentinel.cli scan --hooks-only samples/demo_fixtures/chaindrop/.claude/settings.json
```

**3. Honest Boundary (S14b Formatter)**
```powershell
python -m sentinel.cli scan --hooks-only samples/demo_fixtures/s14b/.claude/settings.json
```

**4. The Text Attack (TrapDoor Vector)**
```powershell
python -m sentinel.cli scan samples/trapdoor_style_demo.md
```

**5. Persona + Encoded Payload (Miasma Vector)**
```powershell
python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc
```

**6. Tool Shadowing (Deadbugz Vector)**
```powershell
python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json
```
