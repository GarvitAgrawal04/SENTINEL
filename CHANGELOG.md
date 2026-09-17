## 0.5.0 — 2026-09-17 — v5 engine
- New engine (`sentinel/core.py`), detonation harness, `AGENTS.lock` (ed25519), pre-open gate, PR behaviour diff, composite GitHub Action.
- API and single-file CLI keep the v1 JSON shape through `sentinel/contract.py`; frontend and VS Code extension need no change.
- Exit codes are now 0 CLEAN / 3 SUSPICIOUS / 2 COMPROMISED. `sentinel.lock` (HMAC) replaced by `AGENTS.lock`.
- False COMPROMISED on 930 real repositories: 97 → 0. See `REBUILD_NOTES.md`.

# CHANGELOG

## [V1.0.0] - RELEASE FROZEN
### Added (Layer 0)
- Implemented file discovery, git boundary enforcement, and origin tracking.
### Added (Layer 1)
- Implemented structural detection rules S1–S16.
- Established `ScanResult` context boundary.
### Added (Scoring)
- Rewrote additive scoring into subtractive mathematical boundaries (`100 - sum(penalty)`).
### Added (Layer 2)
- Added Baseline lock tracking via `FileSystemBaseline` and `.claude` directories.
- Implemented local offline vector distance calculation via `BAAI/bge-m3`.
- Secured subsystem to fail safely when models are unavailable.
### Added (Layer 3)
- Promoted local `dataset.json` KNN approach over expensive external remote calls.
- Removed legacy `GROQ_API_KEY` dependencies.
### Added (Layer 4)
- Implemented deterministic guidance subsystem preventing LLM hallucinations.
### Security Updates (Release Hardening)
- Ensured 100% offline functionality.
- Assured 100% Read-Only properties on the filesystem.
- Implemented global `[REDACTED SECRET]` masking to prevent leakage of captured exfiltration payloads in S3/S11 rules.
- Scrubbed all internal/local developer-machine hardcoded paths.
### Known Debt
- 34 failures in `tests/layer1/test_rule_metadata.py` remain due to structural API modifications (e.g. `check()` deprecation).
- 3 failures in `tests/test_deep_rules.py` remain due to numeric assertion changes.
