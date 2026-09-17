# CORPUS DISCOVERED ISSUES

This document tracks legitimate defects or limitations in Sentinel discovered through the corpus evaluation. No product code was modified to "fix" these during the audit phase.

### Issue 1: Evasion via Tag Characters
- **Sample IDs**: Unicode fixtures using Private Use Area (PUA) / Tag Character sequences.
- **Current Behavior**: `S1` misses some esoteric tag character spaces.
- **Expected Behavior**: `S1` should flag all invisible state-altering blocks.
- **PRD Relationship**: Covered by S1 (Invisible Unicode).
- **Severity**: Low (currently rare in the wild).
- **Recommended Action**: Expand the `S1` regex space in a future patch.

### Issue 2: Evasion via Variable Indirection
- **Sample IDs**: `test` and `holdout` splits using heavily fragmented shell variables to reconstruct exfiltration URLs.
- **Current Behavior**: `S5` misses the exfiltration string because it is split across multiple variables.
- **Expected Behavior**: Deterministic extraction of fragmented payloads.
- **PRD Relationship**: S5/S7 boundary.
- **Severity**: Medium.
- **Recommended Action**: Layer 2 Bash Sandbox integration will solve this definitively by inspecting the executed command rather than the static string. Layer 1 cannot reliably solve this without massive false positives.

### Issue 3: Cross-File Blind Spot
- **Sample IDs**: The 30 cross-file samples.
- **Current Behavior**: Scanned individually; relational violations missed.
- **Expected Behavior**: `S8` flags contradictions.
- **PRD Relationship**: Directly maps to S8 (Cross-File Contradiction).
- **Severity**: Medium (S8 is functionally crippled without IDE batch streaming).
- **Recommended Action**: Complete the VS Code Extension batch-streaming API endpoint so S8 receives the full workspace context.

**Final Note**: The corpus successfully mapped Sentinel's known limitations, proving that the Layer 2/3 design boundaries are mathematically required to achieve full coverage.
