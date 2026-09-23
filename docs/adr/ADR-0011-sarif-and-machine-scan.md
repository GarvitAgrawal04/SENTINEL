# ADR-0011: SARIF 2.1.0 Export, Machine Scan Discovery, and CI Integration

- **Date**: 2026-09-23
- **Status**: Accepted
- **Driver**: Day 9 Milestone — SARIF 2.1.0 for GitHub Code Scanning, machine-level agent configuration discovery with explicit consent gating, and standardized CI exit codes.

---

## 1. Context and Problem Statement

Adoption of security tools depends on friction-free integration with developer workflows:
1. **GitHub Security Integration:** Developers expect static analysis and CI checks to show up natively in the GitHub Security tab via standard SARIF (Static Analysis Results Format) rather than requiring proprietary dashboards.
2. **Global Agent Attack Surface:** AI coding tools (Claude Code, Cursor, VS Code extensions, Gemini CLI) increasingly install global instructions and auto-execution hooks in user home directories (`~/.claude`, `~/.cursor`, VS Code user settings, `~/.gemini`). A compromised global config executes across *every repository* opened on that machine.
3. **Privacy and Consent:** Reading files outside a cloned repository is a sensitive operation. Running scans across home directories without developer awareness violates developer trust.
4. **CI Predictability:** CI pipelines and pre-commit hooks need deterministic exit codes to differentiate between clean runs, syntax errors, and security failures.

---

## 2. Decision and Guiding Invariants

### Invariant 1: Standard SARIF 2.1.0 Specification Compliance
- Both `sentinel scan` and `sentinel pr` support `--format sarif`, emitting valid SARIF 2.1.0 documents.
- Output strictly validates against the OASIS SARIF 2.1.0 JSON schema.
- Findings are mapped cleanly:
  - Critical / forced findings (`forces_compromised` or penalty $\ge 35$) $\to$ `level: error`
  - Warning / suspicious findings $\to$ `level: warning`
  - Advisory / observations (`SEM01`, `D2`, observations) $\to$ `level: note`

### Invariant 2: Explicit Consent for Machine Scans
- `sentinel scan --machine` searches user-level agent roots (`~/.claude`, `~/.cursor`, VS Code user settings, `~/.gemini`).
- In interactive shells, it presents a clear disclosure of all directories to be inspected and prompts for confirmation `[y/N]`.
- In non-interactive environments (CI, automation), it strictly requires `--yes` or `--consent`, terminating with exit code 1 if omitted.

### Invariant 3: Zero Execution Guarantee
- Machine configuration discovery is strictly static analysis: text reading and JSON/JSONC parsing.
- Sentinel never executes, spawns, or evaluates any discovered auto-run script or hook.

### Invariant 4: Standardized CI Exit Code Taxonomy
- **`0`**: `CLEAN` / Success (or below `--fail-on` threshold).
- **`1`**: Invocation error (missing files, invalid flags, consent denied).
- **`2`**: `COMPROMISED` (active threat, prompt injection, unapproved malicious auto-exec).
- **`3`**: `SUSPICIOUS` (unapproved hooks/MCP servers, weakened guardrails).

---

## 3. Implementation and Verification

- Implemented `sentinel/sarif.py` providing unified SARIF generation across repository scan reports and pull request diffs.
- Implemented `sentinel/machine.py` providing cross-platform user config discovery and consent gating.
- Added pre-commit hook definitions in `.pre-commit-hooks.yaml`.
- Verified offline schema validation against `spec/sarif-schema-2.1.0.json`.
- Added test suites for SARIF, machine scan consent, zero-execution invariants, action.yml schema, and pre-commit hooks.
