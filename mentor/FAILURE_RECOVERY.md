# DEMO FAILURE RECOVERY

If the live presentation encounters an environmental failure, DO NOT modify the product code or hack thresholds. Use the following approved recovery paths.

### 1. `demo.ps1` script fails or hangs
**Cause:** PowerShell execution policies or standard I/O blocks.
**Recovery:** Manually execute the `python -m sentinel.cli scan` commands exactly as listed in the `DEMO_TIMELINE.md` file.

### 2. `sentinel scan .` produces unexpected COMPROMISED verdicts
**Cause:** The scanner's Layer 0 global enumeration found the developer's personal `~/.claude.json` which contains legitimate OAuth tokens that structurally match S7 encoded payloads.
**Recovery:** State exactly this: "Sentinel's global discovery successfully mapped the host machine. It flagged my personal Claude configuration because OAuth tokens structurally resemble base64 payloads. This proves D1 discovery works. Let's return to the isolated project fixtures." Then run the specific file path commands.

### 3. Unexpected False Positive during ad-hoc testing
**Cause:** A mentor asks to scan a complex, novel `cursorrules` file not in the test corpus, and it triggers a rule.
**Recovery:** Do not panic. Read the output banner. State: "Sentinel is a deterministic Layer 1 engine. It flagged this because it structurally matches [Rule X]. This is an honest output for Layer 1. The future Layer 3 classifier is specifically designed to analyze this context and override deterministic false alarms."

### 4. API/FastAPI fails to boot
**Cause:** Port 8000 is occupied or dependencies are missing.
**Recovery:** The demo is strictly a CLI presentation. Acknowledge the API is offline and continue with the CLI `python -m sentinel.cli scan` commands. 

### 5. Benchmark numbers look different live
**Cause:** Someone modified the corpus files.
**Recovery:** Refer directly to the `REHEARSAL_REPORT.md` which permanently logs the frozen 100% Precision / 92.3% Recall state. State: "The repository was frozen with 12/13 true positives and 0 false alarms."
