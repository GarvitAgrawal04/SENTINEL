# ADR-0008: Pinning Test Cassettes into AGENTS.lock

- **Status:** Accepted
- **Date:** 2026-09-23
- **Deciders:** Sentinel Core Team
- **Relates to:** Day 5 Task T4, `spec/agents-lock.schema.json`, `sentinel.lock`, ADR-0006, ADR-0007

---

## Context

The Time-Warp sandbox relies on deterministic, key-free cassette replay (`--replay <dir>`) to verify sleeper detection across CI runs without requiring network access or external API credentials.

Because test suites rely on these cassettes to assert that sleeper payloads are caught and that benign twins remain clean, an attacker (or a compromised model attempting to evade detection) could tamper with the cassette itself — altering recorded tool calls, omitting exfiltrations, or faking clean returns.

To protect the integrity of offline evaluation, test cassettes must be treated as security-critical assets subject to cryptographic pinning.

---

## Decisions

### 1. Schema Extension: Optional `cassettes` Mapping
We updated `spec/agents-lock.schema.json` to include an optional top-level `cassettes` field:
```json
"cassettes": {
  "type": "object",
  "description": "Deterministic simulation cassettes pinned to their sha256 hashes.",
  "additionalProperties": {
    "type": "object",
    "required": ["sha256"],
    "additionalProperties": false,
    "properties": {
      "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
      "size_bytes": { "type": "integer", "minimum": 0 }
    }
  }
}
```
Existing locks without `cassettes` remain valid.

### 2. Automated Cassette Discovery & Hashing
`sentinel.lock.discover_test_cassettes(root)` locates all `cassette.json` and `*.cassette.json` files within `tests/fixtures/`.
During `build_lock`, each discovered test cassette is hashed via `core.sha256_file()` and recorded in `lock["cassettes"]`.

### 3. Verification Enforcement
During `sentinel verify`:
- Each locked cassette is checked against the repository working tree.
- If a cassette is missing: reported under `missing_cassettes`, `ok` becomes `False`.
- If a cassette's SHA256 does not match: reported under `tampered_cassettes`, `ok` becomes `False`.
- `sentinel verify` exits with code 2 and alerts:
  `TAMPERED CASSETTE <path> (hash mismatch: cassette was modified outside gate)`.

---

## Consequences

- Test cassettes cannot be quietly modified to conceal attack behaviors or force passing tests.
- Tampering with a single character in a replay cassette breaks CI and fails PR verification.
- Re-signing cassettes requires the protected CI signing key via `sentinel sign`.
