## 0.6.1 — 2026-09-18 — hosted demo fix
- Vercel returned `500 FUNCTION_INVOCATION_FAILED` for every request: with both `pyproject.toml` and `requirements.txt` present, Vercel's Python builder installs from `pyproject.toml`, which lists no dependencies, so FastAPI was never installed. `.vercelignore` now hides `pyproject.toml` (and everything the hosted app does not need); the builder falls back to the pinned `requirements.txt` and finds the app in `api/index.py`. A test guards it.

## 0.6.0 — 2026-09-18 — new web UI
- Replaced the React / three.js frontend (3.8 MB, 18 npm dependencies, WebGL) with plain HTML, CSS and JS: no framework, no npm packages, no build step, no third-party requests, strict Content-Security-Policy. Light and dark, keyboard accessible, works on a phone.
- The API serves the UI at `/`, so `bash setup.sh` gives a newcomer the whole product with no Node.js.
- Visuals that carry information: an illustrated hero that plays the story once (hidden line, scan, blocked path), a field guide to the three attack shapes, a flowchart of the pipeline, unit charts where every square is one of the 930 benchmark projects, and product shots of the real terminal and pull-request output.
- In the scanner: "Reveal hidden content" shows and decodes invisible characters and comments a preview hides; a three-zone score scale; verdict dots on the samples; scan a whole project folder (only agent-config files and the scripts their hooks point to are sent); honest offline mode with saved results when no scanner is reachable.
- API (additive): `GET /samples` (with each sample's verdict), `GET /samples/NAME`, `POST /scan/bundle`.
- README rewritten in depth: install with commands, every way to use it, supported files, each rule and the scoring, architecture diagrams, API, configuration, the measured comparison with its caveats, limits, troubleshooting. Screenshots in `docs/img/`.
- Fixed a finding that told users to run `sentinel clean`, a command that does not exist.

## 0.5.8 — 2026-09-18 — clone and run
- `bash setup.sh` / `make run`: virtual environment, pinned dependencies, `.env`, self-test, server. Python 3.10+ and Git are the only prerequisites.
- `requirements.txt` / `requirements-dev.txt` pinned and verified by the test suite; CI installs the same files.
- `.env.example` lists every variable the code reads. Sentinel loads only its own `.env`, never the scanned repository's (a hostile repo could otherwise redirect your API key).
- One port everywhere (8000). `demo/preflight.py` rewritten for v5 with the standard library. `AGENTS.md` and `CONTRIBUTING.md` no longer describe the deleted v1 engine. README rewritten for newcomers.

## 0.5.7 — 2026-09-18
- Detonation measured on two models (results in `bench/detonation/results/`): D1 recall 11/30 and 5/30, 0/30 false positives on both. Below the 50% gate, so it stays opt-in and is documented as an experiment.
- D2 (new sensitive behaviour without a leak) fired on 20/30 benign files with the small model. It is now an unscored observation; only a canary leaving the sandbox (D1) affects a verdict.

## 0.5.6 — 2026-09-17
- Detonation client: removed API-key rotation and the spoofed browser User-Agent. One key, an honest User-Agent, pacing (`SENTINEL_LLM_RPM`), and back-off that honours the provider's Retry-After.
- A model that calls `bash` is classified like `run_shell`. The evaluation runs the baseline once, saves after every file, resumes, prints 95% intervals, and refuses to call n < 20 a result.
- Eval corpus: 14 benign files replaced by hard negatives (legitimate network use, URLs) so "contains a URL" no longer separates the sets. Measured the two other tools on the same 60 files.

## 0.5.5 — 2026-09-17
- PR comment and web UI: Tier B rules (S2, S4, S7, S11, S12, S16) now show a human title instead of a bare rule id.
- `sentinel sign` is a no-op when nothing but the timestamp would change (no more signing commit after every push).
- `demo/make_flip_pr.py --hidden-comment` reproduces the hidden-HTML-comment variant.

## 0.5.4 — 2026-09-17
- Detonation now targets hosted models (OpenAI / Groq / Together / Anthropic / any OpenAI-compatible endpoint) via provider presets; removed the Ollama-first framing.
- Fixed a sandbox bug where a request to read `.env` returned "no such file" (a leading-dot path was stripped), which would have made every canary leak impossible to observe.
- Added the 30 + 30 detonation eval corpus, `run_detonation_eval.py`, and HTTP-path detonation tests (fake obedient agent, no real key needed).

## 0.5.3 — 2026-09-17
- `AGENTS.md` now carries real security guardrails; `AGENTS.lock` records them, so deleting or flipping one shows up in a PR.
- The `sentinel` workflow runs on every pull request (it was limited to PRs targeting `main`, so a PR into `v5-engine` got no comment).
- The signing workflow installs Sentinel from the checkout instead of from the default branch.

## 0.5.2 — 2026-09-17 — demo polish
- `sentinel verify` now says exactly what is wrong: SIGNATURE INVALID / KEY_CHANGED / UNSIGNED / NO LOCK / NOT COVERED (it used to print "files changed" even when none had).
- PR comment no longer lists `AGENTS.lock` as a file that changes agent behaviour.

## 0.5.1 — 2026-09-17 — follow-up
- `pytest` at the repository root works again (v1 tests, benchmark and docs moved to `archive/`).
- Windows: CLI output is UTF-8-safe; the gate waits for the agent instead of `exec`; report paths are POSIX.
- PR workflow uses the local action (`./action`) so it runs before this branch is merged; added a `tests` workflow.
- README rewritten for v5. `bench/` scripts import `sentinel.core`. `frontend/.env.local` untracked. `AGENTS.lock` added (unsigned until CI signing is set up).

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
