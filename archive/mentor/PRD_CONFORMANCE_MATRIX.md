# PRD CONFORMANCE MATRIX

This matrix confirms the alignment of the implementation with the Master v3 PRD rules (S1-S16). All rules were verified in Phase 2 and validated via test cases.

| Rule | Trigger | Penalty | Forced Verdict | Ceiling | Conformance Status |
|---|---|---|---|---|---|
| S1 | Zero-width, bidi, tags, unusual control chars | 50 | COMPROMISED | N/A | 100% (Excludes homoglyphs per PRD) |
| S2 | Hidden HTML/Markdown comments in instructions | 35 | NONE | N/A | 100% |
| S3 | MCP Tool Description Injection | 35 | NONE | N/A | 100% (Added max depth 100) |
| S4 | Override phrasing | 25 | NONE | N/A | 100% |
| S5 | Network-shaped instruction | 40 | NONE | N/A | 100% (Line-by-line static evaluation) |
| S6 | New file in dependency PR / postinstall | 15 | NONE | N/A | 100% (D2 Origin bounded) |
| S7 | Encoded payload (base64, hex block) | 45 | COMPROMISED | N/A | 100% (5MB max size limit imposed) |
| S8 | Cross-file policy contradiction | 20 | NONE | N/A | 100% (Supported via API batch path) |
| S9 | MCP Tool Shadowing | 30 | NONE | N/A | 100% |
| S10 | Hook references missing script path | 70 | COMPROMISED | N/A | 100% |
| S11 | Bridge/C2 URL in tool config | 70 | COMPROMISED | N/A | 100% (Added max depth 100) |
| S12 | External Trust Delegation | 35 | NONE | N/A | 100% |
| S13 | Persona override + self-concealment | 50 | COMPROMISED | N/A | 100% |
| S14a | Write-intercept hook missing script | 70 | COMPROMISED | N/A | 100% |
| S14b | Write-intercept hook existing script | 0 | NONE | 60 | 100% |
| S15 | Deposited slash command | 55 | NONE | N/A | 100% |
| S16 | Auto-enable MCP | 0 | NONE (unless postinstall) | 60 | 100% (Added max depth 100) |
