# FINAL EVIDENCE MATRIX

| Capability | PRD Reference | Implementation | Test | Demo Command | Evidence | Status |
|:---|:---|:---|:---|:---|:---|:---|
| **D1 (Discovery)** | PRD A 13.3 | `sentinel/layer0/discovery.py` | `test_scanner.py`, Self-scan | `python -m sentinel.cli scan .` | Accurately discovers local and global `.claude/settings.json` and `.mdc` structures. | VERIFIED |
| **D2 (Origin)** | PRD A 13.3 | `sentinel/layer0/origin.py` | `test_s16_postinstall`, `test_s6_new_file` | Implicit in S6/S16 tests | Deterministically tracks `node_modules` and `.package-lock.json` proximity. | VERIFIED |
| **D3 (Hooks)** | PRD A 13.3 | `sentinel/layer0/hooks.py` (via rules) | `test_s14b_write_intercept_existing` | `.\demo.ps1` (ChainDrop/S14b) | Successfully maps nested JSON Claude schema to extract commands and matchers. | VERIFIED |
| **S1 (Unicode)** | PRD A 13.2 | `sentinel/rules/s1_unicode.py` | Benchmark | `python -m sentinel.cli scan samples/trapdoor_style_demo.md` | Forces COMPROMISED upon detection. | VERIFIED |
| **S2 (Comments)** | PRD A 13.2 | `sentinel/rules/s2_comments.py` | Benchmark | N/A (Tested in benchmark) | Penalty: -35. | VERIFIED |
| **S3 (MCP Inject)** | PRD A 13.2 | `sentinel/rules/s3_mcp_injection.py` | Benchmark | `python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json` | Penalty: -35. | VERIFIED |
| **S4 (Override)** | PRD A 13.2 | `sentinel/rules/s4_override.py` | Benchmark | `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc` | Penalty: -25. | VERIFIED |
| **S5 (Exfiltration)** | PRD A 13.2 | `sentinel/rules/s5_exfiltration.py` | Benchmark | `python -m sentinel.cli scan samples/trapdoor_style_demo.md` | Penalty: -40. (0 False Positives on benchmark). | VERIFIED |
| **S6 (New File)** | PRD A 13.2 | `sentinel/rules/s6_new_file.py` | `test_s6_new_file` | N/A (Tested in pytest) | Penalty: -15. Fires dynamically on `postinstall` origin. | VERIFIED |
| **S7 (Encoding)** | PRD A 13.2 | `sentinel/rules/s7_encoding.py` | Benchmark | `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc` | Forces COMPROMISED. | VERIFIED |
| **S8 (Contradiction)**| PRD A 13.2 | `sentinel/rules/s8_contradiction.py` | Benchmark | N/A (Tested in benchmark) | Penalty: -20. | VERIFIED |
| **S9 (Shadowing)** | PRD A 13.2 | `sentinel/rules/s9_tool_shadow.py` | Benchmark | `python -m sentinel.cli scan samples/demo_fixtures/deadbugz/mcp.json` | Penalty: -30. | VERIFIED |
| **S10 (Hook Target)** | PRD A 13.2 | `sentinel/rules/s10_hook_survivability.py`| Benchmark | `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/chaindrop/.claude/settings.json` | Forces COMPROMISED. | VERIFIED |
| **S11 (Bridge)** | PRD A 13.2 | `sentinel/rules/s11_bridge_url.py` | Benchmark | N/A (Tested in benchmark) | Forces COMPROMISED. | VERIFIED |
| **S12 (Delegation)**| PRD A 13.2 | `sentinel/rules/s12_trust_delegation.py` | Benchmark | N/A (Tested in benchmark) | Penalty: -35. | VERIFIED |
| **S13 (Persona)** | PRD A 13.2 | `sentinel/rules/s13_persona_override.py`| Benchmark | `python -m sentinel.cli scan samples/demo_fixtures/miasma_multi/.cursor/rules/miasma.mdc` | Forces COMPROMISED. | VERIFIED |
| **S14a (Write Miss)**| PRD A 13.2 | `sentinel/rules/s14_write_intercept.py` | Benchmark | N/A (Tested in benchmark) | Forces COMPROMISED. | VERIFIED |
| **S14b (Write Ex)** | PRD A 13.2 | `sentinel/rules/s14_write_intercept.py` | `test_s14b_write_intercept_existing` | `python -m sentinel.cli scan --hooks-only samples/demo_fixtures/s14b/.claude/settings.json` | Score ceiling 60 (SUSPICIOUS). | VERIFIED |
| **S15 (Slash Cmd)** | PRD A 13.2 | `sentinel/rules/s15_slash_command.py` | Benchmark | N/A (Tested in benchmark) | Penalty: -55. | VERIFIED |
| **S16 (AutoMCP)** | PRD A 13.2 | `sentinel/rules/s16_mcp_autoenable.py` | `test_s16_postinstall` | N/A (Tested in pytest) | Score ceiling 60. Combined with D2 postinstall -> COMPROMISED. | VERIFIED |
| **Trust Score** | PRD A 13.2 | `sentinel/scoring/formula.py` | All Tests | `.\demo.ps1` | Arithmetic ceiling and forces applied independently of extraction. | VERIFIED |
| **CLI** | MVP | `sentinel/cli.py` | Manual | `.\demo.ps1` | `sentinel scan .` output matches PRD spec formatting. | VERIFIED |
| **Structured Findings**| MVP | `sentinel/rules/base.py` | `test_scanner.py` | `--json` | Findings object strictly defines Line, Rule, Snippet, Message. | VERIFIED |
| **Agent Impact** | PRD A 13.5 | `sentinel/rules/base.py` (Reconstruction) | Manual | `.\demo.ps1` | Human-readable explanation of how the agent would be manipulated. | VERIFIED |
| **API Compat.** | Integration| `sentinel/api.py` | Manual Boot | N/A | FastAPI backend boots. | VERIFIED |
| **GitHub Action** | Integration| `action/scan_pr.py` | Manual Review | N/A | Compatible with `--json` output. | VERIFIED |

**Note:** All dependencies on Layer 2 (Semantic Displacement, `sentinel.lock`, TOFU) or Layer 3 (LLM Classifier) are strictly marked as FUTURE in design documentation and do not affect the `VERIFIED` status of Layer 1 capabilities.
