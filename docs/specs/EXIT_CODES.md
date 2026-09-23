# Sentinel Exit Codes Specification

This document defines the exit code contract returned by Sentinel CLI commands for CI/CD pipelines, pre-commit hooks, and automation workflows.

## Exit Code Taxonomy

| Code | Status | Meaning | Typical CLI Actions & Conditions |
|:---:|:---|:---|:---|
| **`0`** | **CLEAN / SUCCESS** | Target passed all checks cleanly, or findings remained below configured failure thresholds. | • `sentinel scan`: 0 findings, score ≥ 80.<br>• `sentinel pr`: verdict below `--fail-on` threshold.<br>• `sentinel run`: repository passes gate; agent process completes with 0.<br>• `sentinel doctor`: no hygiene lints found or all fixed.<br>• `sentinel verify`: signature valid, all files covered.<br>• `sentinel selftest`: all built-in regression tests pass. |
| **`1`** | **INVOCATION ERROR** | User error, invalid flags, missing files, or consent rejected. | • Target file or directory does not exist.<br>• Missing required flags (e.g., `--base` on `sentinel pr`).<br>• `sentinel scan --machine`: consent denied by user or missing `--yes` in non-interactive environments.<br>• Syntax errors in configuration files. |
| **`2`** | **COMPROMISED** | Critical security finding detected that forces a `COMPROMISED` verdict. | • Active prompt injection or exfiltration instructions (`S5`).<br>• Invisible unicode obfuscation (`S1a`).<br>• Orphaned auto-run hooks (`S10`) or unreadable scripts (`S18a`).<br>• Direct download-and-execute commands (`S18c`, `S21`).<br>• Destructive commands (`S23`) or credential store access (`S26`).<br>• In `sentinel pr`: PR verdict is `COMPROMISED` with `--fail-on compromised` (the default). |
| **`3`** | **SUSPICIOUS** | High-penalty findings or unapproved surfaces requiring human review. | • New auto-run hook not yet approved in `AGENTS.lock` (`S17a`).<br>• New MCP server definition not approved (`S19`).<br>• Guardrail weakened or inverted in pull request diff (`S20`).<br>• In `sentinel pr`: PR verdict is `SUSPICIOUS` when `--fail-on suspicious` is set. |

## CLI Failure Thresholds (`--fail-on`)

The `sentinel pr` command accepts `--fail-on` to customize gating behavior:

- `--fail-on compromised` *(default)*:
  - Returns `0` if verdict is `CLEAN` or `SUSPICIOUS`.
  - Returns `2` if verdict is `COMPROMISED`.
- `--fail-on suspicious`:
  - Returns `0` if verdict is `CLEAN`.
  - Returns `3` if verdict is `SUSPICIOUS`.
  - Returns `2` if verdict is `COMPROMISED`.
- `--fail-on never`:
  - Always returns `0` regardless of verdict (useful for auditing without breaking builds).

## Machine Scan Consent Error (`--machine`)

When executing `sentinel scan --machine`:
- Interactive terminals prompt the developer before reading paths outside the repository (`~/.claude`, `~/.cursor`, VS Code user settings, `~/.gemini`). Answering anything other than `y`/`yes` exits with **`1`**.
- Headless CI environments must supply `--yes` or `--consent`. If omitted in a non-interactive shell, Sentinel terminates immediately with exit code **`1`** without reading external files.
