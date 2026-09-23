# Build log

One line per work session. Newest at the top. This is the honest record a reviewer of the repo can read.

Format: `YYYY-MM-DD · Day N · Hh · what shipped · gate: PASS/FAIL (verdicts) · tests: N`


<!-- add your lines above this comment -->

- 2026-09-23 · Day 12 · T1–T10 · feat(portfolio): demo.gif 4-phase animation, CITATION.cff, AUTHORS, CONTRIBUTORS, docs/GITHUB_SETUP.md + social-preview.png, docs/DEMO.md 5-min runbook, ARCHITECTURE.md, GLOSSARY.md, docs/FAQ.md · gate: PASS (0 COMPROMISED) · tests: 330

- 2026-09-23 · Day 11 · T1–T10 · feat(evidence): bench/evidence.py reproduces all numbers (semantic 84.88%/0.00%FP, timewarp 10/10, trigger 1.045 mean); docs/RESEARCH.md (landscape, failures, threats, citations); bench/results/README.md index; make evidence · gate: PASS (0 COMPROMISED) · tests: 298

- 2026-09-23 · Day 10 · T1–T10 · feat(packaging): PyPI trusted publishing (OIDC), sdist/wheel builds, OpenVSX guide, CycloneDX SBOM + Sigstore, SUPPORT.md, install matrix · gate: PASS (wheel installs, entrypoints valid) · tests: 283

- 2026-09-23 · Day 9 · T1–T10 · feat(sarif/ci): SARIF 2.1.0 export (scan/pr), machine config scan with consent gate, 0-exec invariant, action.yml SARIF upload, pre-commit hooks, exit codes spec, ci-repo example · gate: PASS (0 exec leaks, schema valid) · tests: 279

- 2026-09-23 · Day 8 · T1–T10 · feat(semantic): advisory semantic check (capped <=20, floor 40), 86 holdout / 300 benign eval (84.88% recall, 0.00% FP), VS Code Information diagnostic, ADR-0010 · gate: PASS (0 false alarms, budget met) · tests: 261

- 2026-09-23 · Day 7 · T1–T10 · feat(web): offline timewarp plan and doctor lint endpoints, key-free moments/lints/graph panels, dark mode/a11y, 0-key assertions, screenshots · gate: PASS (clean, 0 key fields) · tests: 252

- 2026-09-23 · Day 6 · T1–T10 · feat(timewarp): deepened behaviour diff (new egress D2, guardrail break D2, moment A vs B plain-English diff, cap logic <=40), 4 fixtures/twins, ADR-0009, published headline sleeper delta · gate: PASS (twins clean, 0 escapes) · tests: 241

- 2026-09-23 · Day 5 · T1–T10 · feat(timewarp): run --record with live model, --budget N dropping, --parallel (cap 4), cassette pinning in lock, --trace spend, ADR-0008 · gate: PASS (0 escapes, tampered cassette rejected) · tests: 235

- 2026-09-23 · Day 4 · T1–T10 · feat(timewarp): trigger extraction (10 kinds), deduplication, sentinel timewarp --json, sentinel.timewarp.yml, prevalence bench (1.045 mean across 422 targets), 20 fixtures/twins, ADR-0007 · gate: PASS (twins clean) · tests: 228

- 2026-09-23 · Day 3 · T6–T10 · feat(doctor): SARIF export, rewrite gate red-team (0 escapes), load-graph UI, token delta bench (median -20 tok), README · gate: PASS (30/30 blocked, 0 escapes) · tests: 206

- 2026-09-23 · Day 3 · T5 · feat(vscode): gated Safe Rewrite with doctor.gate.check and SecretStorage · gate: PASS (clean applied, exfil blocked) · tests: 201

- 2026-09-23 · Day 3 · T4 · feat(vscode): Doctor quick-fixes for safe deterministic checks (D001/D004/D008) · gate: not run (no rule change) · tests: 193

- 2026-09-23 · Day 3 · T3 · feat(doctor): D005–D008 + honest hit-rate on 372 repos; >5% classified as OBSERVATIONS · gate: not run (no rule change) · tests: 193

- 2026-09-23 · Day 3 · T2 · feat(doctor): D001–D004 deterministic lints with fixtures and twins; sentinel doctor <path> [--fix] CLI · gate: not run (no rule change) · tests: 189

- 2026-09-23 · Day 3 · T1 · feat(doctor): load graph for agent files; @import/@include and nested CLAUDE.md discovery with cycle detection · gate: not run (no rule change) · tests: 181

- 2026-09-22 · Day 2 · T6–T10 · feat(timewarp): parallel runner (cap 4), upfront cost/budget control, record spec, README sleeper slice, ADR-0006 · gate: not run (no rule change) · tests: 175

- 2026-09-22 · Day 2 · T5 · bench(timewarp): sleeper set 20 fixtures; single-moment 0/10 caught vs time-warp 10/10 caught, 0/10 false alarms · gate: not run (no rule change) · tests: 171

- 2026-09-22 · Day 2 · T4 · feat(timewarp): M0 vertical slice — sleeper caught by replay, no key; sentinel timewarp run CLI · gate: not run (no rule change) · tests: 170

- 2026-09-22 · Day 2 · T3 · feat(timewarp): scenario runner + behaviour diff; two-scenario sleeper caught by cassette replay · gate: not run (no rule change) · tests: 167

- 2026-09-22 · Day 2 · T2 · feat(timewarp): virtual clock/state for sandbox tools; property test across 20 scenarios (0 leaks) · gate: not run (no rule change) · tests: 164

- 2026-09-22 · Day 2 · T1 · feat(timewarp): cassette record/replay for model calls; zero network/key offline sandbox replay · gate: not run (no rule change) · tests: 161

- 2026-09-22 · Day 1 · T5–T10 · benign twins + attack fixtures for S21–S26; docs/RULES.md generator; prose typing; make bench; test_cli_smoke · gate: not run (tests/docs/tooling only) · tests: 159

- 2026-09-22 · Day 1 · T1–T3 · perf guardrail test; prose.findings O(lines) precompute; scan_repo tiny-file skip · gate: PENDING (corpus not on this machine; verdicts verified identical by 124 tests) · tests: 124

- 2026-09-22 · Day 0 · — · plan, roadmap, specs, ADRs, repo base; `timewarp` planner and rewrite `gate` (offline); precision-gate and corpus-rebuild tooling · gate: not run (no rule change) · tests: 122
