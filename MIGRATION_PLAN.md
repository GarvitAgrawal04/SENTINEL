# SENTINEL Migration Plan — Master v3 Architecture

## Phase 0: Preserve existing API contract
- Keep `sentinel/api.py` endpoints: /scan/file, /scan/files, /scan/demo, /scan/package, /health
- Keep `sentinel/main.py` 
- Keep frontend, vscode-extension, github action untouched

## Phase 1: Canonical directory structure
Create these new directories:
- sentinel/rules/
- sentinel/layer0/
- sentinel/layer2/
- sentinel/layer3/
- sentinel/layer4/
- sentinel/scoring/
- sentinel/manifest/
- sentinel/output/

## Phase 2: Migrate S1-S8 from monolithic rules.py
- sentinel/rules/s1_unicode.py
- sentinel/rules/s2_comments.py
- sentinel/rules/s3_mcp_injection.py
- sentinel/rules/s4_override.py
- sentinel/rules/s5_exfiltration.py
- sentinel/rules/s6_new_file.py
- sentinel/rules/s7_encoding.py
- sentinel/rules/s8_contradiction.py

## Phase 3: Implement S9-S16
- sentinel/rules/s9_tool_shadow.py (-30)
- sentinel/rules/s10_hook_survivability.py (-70, forces COMPROMISED)
- sentinel/rules/s11_bridge_url.py (-70, forces COMPROMISED)
- sentinel/rules/s12_trust_delegation.py (-35)
- sentinel/rules/s13_persona_override.py (-50, forces COMPROMISED)
- sentinel/rules/s14_write_intercept.py (S14a: -70 forces COMPROMISED; S14b: caps at 60)
- sentinel/rules/s15_slash_command.py (-55)
- sentinel/rules/s16_mcp_autoenable.py (caps at 60; COMPROMISED if + postinstall origin)

## Phase 4: Implement Layer 0
- sentinel/layer0/discovery.py (D1: surface enumeration)
- sentinel/layer0/origin.py (D2: postinstall origin detection)
- sentinel/layer0/hooks.py (D3: Claude hook survivability)

## Phase 5: Scoring
- sentinel/scoring/formula.py (PRD formula with forced verdict semantics)

## Phase 6: Output/Formatter
- sentinel/output/formatter.py (human-readable terminal output)
- sentinel/output/api.py (update to consume new architecture)

## Phase 7: Layer 2/3/4 relocation
- sentinel/layer2/ (migrate from sentinel/layer2.py)
- sentinel/layer3/ (migrate from root layer3/)
- sentinel/layer4/guide.py (V1 decision tree stub)
- sentinel/manifest/sentinel_lock.py (stub)

## Phase 8: Update CLI
- sentinel/cli.py updated to support --hooks-only flag
- CLI orchestrates: Discovery → Rules → Scoring → Output

## Test Fixtures Required
- fixtures/clean_claude.md
- fixtures/s1_invisible_unicode.md
- fixtures/s5_trapdoor.md
- fixtures/chaindrop_settings.json
- fixtures/miasma_settings.json
- fixtures/s11_bridge_url.json
- fixtures/s13_persona_override.md
- fixtures/s14a_missing_path.json
- fixtures/s14b_existing_path.json
- fixtures/s16_alone.json
- fixtures/s16_postinstall.json

## Key PRD Constraints
- S1, S7, S10, S11, S13, S14a = structurally unambiguous → force COMPROMISED
- S14b alone = caps score at 60 (SUSPICIOUS)
- S16 alone = caps score at 60 (SUSPICIOUS)
- S16 + postinstall origin = COMPROMISED
- Trust Score = clamp(100 - sum(L1 penalties), 0, 100)
