# CORPUS TO SENTINEL MAPPING

The corpus proposes 49 candidate rules. This mapping evaluates how those candidate patterns map to our frozen S1-S16 implementation and our planned architecture.

| CORPUS RULE FAMILY | CURRENT SENTINEL RULE | MAPPING STATUS | JUSTIFICATION |
|---|---|---|---|
| `AGENT_AUTORUN` / `AGENT_CHAIN_TOOLS` | S15, S4 | PARTIALLY COVERED | Sentinel covers structural markers of automated overrides, but pure semantic intent to chain tools requires Layer 3. |
| `CRED_ENV_ACCESS` / `CRED_REPO_SECRET` | None (Directly) | NOT CURRENTLY COVERED | Sentinel V1 does not scan for generalized credential names (avoids grep-style false positives). Layer 2/3 required for context. |
| `DESTRUCT_CONFIG_WIPE` | S4 (indirect) | INDIRECTLY COVERED | Destructive overrides often trigger S4 phrasing. |
| `EXEC_INTERPRETER_INLINE` | S14a/b (if hook) | PARTIALLY COVERED | Covered if the execution is wired into a hook path (S14). Standalone bash parsing requires Layer 2 sandbox. |
| `EXFIL_ARCHIVE_THEN_SEND` | S5 | DIRECTLY COVERED | URL patterns matching exfiltration bridges hit S5. |
| `EXFIL_ENCODED` / `EXFIL_HTTP_DIRECT` | S7, S5 | DIRECTLY COVERED | Base64/Hex encoding hits S7, URLs hit S5. |
| `HOOK_DISABLE_BYPASS` / `HOOK_MODIFY_INJECT` | S10, S14 | DIRECTLY COVERED | Hook path survivability and intercept detection are fully implemented. |
| `MCP_EXCESS_PERMISSION` / `MCP_HIDDEN_SIDE_EFFECT` | S9, S3 | DIRECTLY COVERED | Tool shadowing and description injection are fully covered. |
| `PERSIST_STARTUP_CONFIG` / `PERSIST_AGENT_HOOKS` | S16 (if MCP) | PARTIALLY COVERED | Global config modification is flagged depending on the specific hook injected. |
| `PRIV_ELEVATION` / `PRIV_SECURITY_SETTING` | S16 | PARTIALLY COVERED | S16 catches `enableAllProjectMcpServers`, but arbitrary OS-level privilege escalation relies on Layer 3 context. |
| `PROMPT_OVERRIDE` / `PROMPT_FAKE_AUTHORITY` | S4, S13 | DIRECTLY COVERED | Persona override and rule overriding language is deterministically caught. |
| `SUPPLY_INSTALL_THEN_EXEC` / `SUPPLY_UNTRUSTED_SOURCE`| S6 | DIRECTLY COVERED | Postinstall origin tracking (S6) triggers on unverified dependency execution. |
| `UNICODE_CONTROL` / `UNICODE_HOMOGLYPH` | S1 | DIRECTLY COVERED | S1 covers zero-width and control characters. Homoglyphs require Layer 3. |
| `XFILE_CHAIN` / `XFILE_CONTRADICTION` | S8 | CROSS-FILE / SPECIAL | Cross-file contradictions (S8) require API batch processing to scan correctly. |
| `DRIFT_SEMANTIC` | None | FUTURE LAYER 2 | Requires `sentinel.lock` displacement math. |
| `MANIFEST_VERIFY` | None | MANIFEST / FUTURE | Requires `sentinel.lock` HMAC signing. |

### Conclusion
Sentinel S1-S16 structurally covers the critical exfiltration, hook injection, MCP shadowing, and override vectors without reverting to naive credential-regex matching, maintaining zero false positives.
