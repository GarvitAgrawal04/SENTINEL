# Daily build prompts

Paste [`AGENT_CONTRACT.md`](AGENT_CONTRACT.md) **once** at the top of an Antigravity conversation. Then each day, paste the block
for the hours you have. Replace `<MAIN>` and `<HELDOUT>` with your corpus paths (from `bench/rebuild_corpus.py`).

**How the hour blocks nest.** Each day's tasks are numbered T1, T2, …, each ~1 hour. A block of *N* hours = tasks T1…T(N). So a
2-hour day is "paste T1–T2"; a 10-hour day is "paste the whole day". Every task ends green, committed and pushed on its own, so you
can stop after any task. After each block, send me the FINAL REPORT.

The plan runs **13 days**. Days 1–3 are the vertical slice + the two headline features (Doctor, gate). Days 4–8 finish the sandbox.
Days 9–13 are the semantic layer, SARIF, machine scan, packaging and the write-up. Order follows the pre-mortem in the plan
(§21): prove cheaply, ship what people use daily, polish the clever part last.

---

## DAY 1 — make the engine fast again, and lock it with the gate

*Why first: the scan slid from 3.6 s to ~30 s on 930 repos when the prose rules and evasion-normalisation were added. A slow
scanner is a broken demo, and this is pure win with zero behaviour change. The precision gate proves "zero behaviour change".*

**T1 — baseline and a benchmark you can trust.**
```
1. Loop steps 1 (clean tree, pull).
2. .venv\Scripts\python.exe bench/precision_gate.py baseline <MAIN> <HELDOUT> --out bench\results\gate_baseline.local.json
   → note the line: "930 repositories in <S> s · verdicts {...} · with a scored claim: N". Record <S> and the verdicts.
3. Add a test tests/v5/test_perf.py that scans a fixed set of 12 fixtures (sentinel fixtures to a temp dir) and asserts the
   whole set scans in under 2 seconds on the dev machine — a smoke test, not a benchmark. Mark it with a comment that it is a
   guardrail against accidental O(n^2), not a promise of wall-clock speed.
4. Full test suite; commit "test: perf guardrail + record precision-gate baseline"; push. (No version bump — no behaviour change.)
For the human: paste the "930 repositories in <S> s" line into docs/build/PROGRESS.md when you commit.
```

**T2 — fix the O(n^2) in prose.findings.**
```
1. In sentinel/prose.py, findings(): _under_prohibiting_lead_in(text, start) re-splits the whole text on EVERY regex match.
   Precompute the line-start offsets and the "is this line under a forbidding heading" map ONCE per call, before the rule loop,
   and look them up by offset. Do not change any pattern or any verdict.
2. .venv\Scripts\python.exe bench/precision_gate.py check <MAIN> <HELDOUT> --baseline bench\results\gate_baseline.local.json
   → MUST print GATE: PASS with identical verdict counts to T1. If ANYTHING differs, you changed behaviour: revert and STOP.
3. Full suite; selftest; self-scan.
4. Bump to 0.8.1 in both files; CHANGELOG entry ("perf: prose scan is linear again; verdicts identical, gate PASS");
   PROGRESS line with the new <S> seconds; commit "perf: linear prose scan (gate PASS, no verdict change)"; push.
```

**T3 — cache the compiled regexes and skip work on tiny files.**
```
1. Confirm every re.compile in core.py and prose.py is module-level (compiled once), not inside a function. Move any that are not.
2. In scan_repo, short-circuit files with no letters or under ~3 bytes before running the rule battery (they cannot match).
3. Gate check → PASS, identical counts. Full suite. PROGRESS line with the newest <S>. Commit "perf: module-level patterns + skip trivial files"; push. (0.8.2)
```

**T4 — README honesty pass on speed.**
```
1. Re-measure with bench/precision_gate.py and put the REAL current seconds into the README benchmark section and bench/results.
   If it is not 3.6 s any more, say the true number. Never keep a stale number.
2. Regenerate the benchmark SVG if the number changed: .venv\Scripts\python.exe docs\build_readme_assets.py ; git status must
   then be clean after you commit the new SVG.
3. Full suite (README tests included). Commit "docs: real scan time on 930 repos"; push.
For the human: eyeball the README benchmark chart on GitHub after the push.
```

**T5–T10 (only if you have the hours): harden and document what exists.**
```
T5:  Add 6 more benign-twin fixtures for the S21–S26 prose families (real setup-note phrasings that must NOT score). Gate PASS. (test only)
T6:  Add 6 attack fixtures for the same families with distinct wordings; assert each SCORES. Gate PASS.
T7:  docs/RULES.md — one table: every rule id, one-line meaning, weight, whether decisive/ceiling/observation. Generated from
     sentinel/render.py TITLE + core weights by a small script docs/build_rules_table.py so it can never drift. Test that it is current.
T8:  Type-annotate sentinel/prose.py and sentinel/timewarp/*.py fully; run `.venv\Scripts\python.exe -m mypy` (advisory) and fix what is cheap.
T9:  Add `make bench` target that runs precision_gate check against paths in env vars; document it in docs/build/README.md.
T10: Write tests/v5/test_cli_smoke.py that runs every `sentinel` subcommand with --help and one trivial input, asserting exit codes.
```

---

## DAY 2 — the vertical slice (M0): a sleeper file, caught by replay, no key

*Why: this is the whole product idea proven end to end on ONE file, in CI, with no API key. If this shows nothing the static
rules missed, the plan (§21) says stop the sandbox and keep only the planner. So this day decides the sandbox's fate. Cheap first.*

**T1 — the cassette format (record/replay of model calls).**
```
1. Create sentinel/timewarp/cassette.py: Cassette with record(model) and replay(path). Key = sha256 of the JSON-serialised
   message list; value = the model's response dict. record() wraps a real model and writes entries as it goes; replay() raises a
   clear error if a message list is not in the cassette (so CI fails loudly, never silently "clean"). Never store a key; run every
   stored string through core.redact.
2. Unit test tests/v5/test_cassette.py with the existing MockObedientModel: record a short session, replay it, assert identical.
3. Full suite. Commit "feat(timewarp): cassette record/replay for model calls"; push. (0.8.3)
```

**T2 — the virtual world (clock + state) inside the fake tools.**
```
1. Create sentinel/timewarp/clock.py: World(scenario) exposing now() (from scenario.clock, default a FIXED demo date, never the host
   clock), session (int), env (dict), branch, interactive (bool), user_turns (list). 
2. In detonate.py, make fake_tool consult an optional World: read_file of a date/log file, and any "what day is it" style tool,
   return the World's values; run_shell 'date'/'git log -1 --format=%cd' return the World's date. NO real date, host user, or path
   may appear. Keep the default (no World) behaviour byte-identical — the existing detonation tests must still pass unchanged.
3. Property test: build 20 random scenarios, run the fake tools, assert no result contains today's date, $HOME, or the OS username.
4. Full suite + selftest. Commit "feat(timewarp): virtual clock/state for the sandbox tools"; push. (0.8.4)
```

**T3 — the runner (replay-only) and the behaviour diff.**
```
1. sentinel/timewarp/runner.py: run(file_text, plan, model=None, cassette=None, parallel=1) -> list[Trace]. For each scenario, run
   detonate.detonate with a World built from the scenario, using the cassette when model is None. Trace = {scenario, events,
   canary_leaks, egress}. Early-exit a scenario as soon as a canary leaves.
2. sentinel/timewarp/diff.py: compare(traces) -> findings. A behaviour (a canary leak, or an egress host) counts ONLY if it is
   present in some scenario and ABSENT from the baseline "now" scenario. Each finding names the moment in words ("acts only from
   the third session on") and is capped exactly like D1 (penalty ≤ 40, never forces COMPROMISED).
3. Unit tests with a hand-written cassette for a two-scenario case. Full suite. Commit "feat(timewarp): scenario runner + behaviour diff"; push. (0.8.5)
```

**T4 — THE SLICE TEST (this is the milestone).**
```
1. Add tests/fixtures/sleeper/AGENTS.md: an instruction that exfiltrates a canary ONLY after the third session
   (use example.invalid). Add tests/fixtures/sleeper/cassette.json: a hand-written cassette where the mock model obeys the file —
   leaking in session 3, not in 1 or 2. (No real model, no key.)
2. tests/v5/test_slice.py: plan the file → runner replays the cassette → diff → assert exactly one finding whose text says the
   behaviour appears from session 3, and that a SINGLE-moment run at "now" would have missed it.
3. `sentinel timewarp run <file> --replay <dir>` CLI wired to the runner (replay path only; --record needs a key and is Day 5).
4. Full suite in CI must run this WITHOUT a key and WITHOUT network. Commit "feat(timewarp): end-to-end slice — sleeper caught by replay, no key"; push. (0.8.6)
For the human: this is the go/no-go. If the slice is green, the sandbox idea is proven. Read docs/MASTER_PLAN.md §21.
```

**T5 — measure whether time-warp actually adds catches (the honest test).**
```
1. Write tests/fixtures/sleeper_set/ with 10 conditional attacks + 10 benign twins (twins: "in CI skip the slow tests", "on
   Fridays run the full suite" — legitimate, must stay clean). Hand-write a cassette per file (mock model obeys).
2. bench/timewarp_eval.py: run every file through the single-moment sandbox AND through time-warp; print how many attacks each
   catches and how many twins each wrongly flags. This is the number that decides the feature.
3. Commit "bench(timewarp): sleeper set + single-moment vs time-warp comparison"; push. Put the result line in PROGRESS.md.
For the human: if time-warp catches no more than the single moment, tell me — we cut the sandbox to the planner and move the days to the Doctor.
```

**T6–T10:** `T6` parallelise the runner (ThreadPool, cap 4) + a test that a 6-scenario plan runs concurrently. `T7` token/cost
estimate printed before any real run; `--budget N` enforced with a "dropped: …" line. `T8` `sentinel timewarp run --record` design
doc in docs/specs (implementation Day 5). `T9` add the sleeper slice to the README "See it in 60 seconds" as a code block (text,
not a live key). `T10` write ADR-0006 recording the go/no-go decision from T5 with the measured numbers.

---

## DAY 3 — the Instruction Doctor: deterministic checks + the gate in VS Code

*Why here (not later): this is the part people would use every day — stale, bloated agent files — and the plan's pre-mortem says
ship it before polishing the sandbox. The gate (already built, `sentinel gate`) is the differentiator; today it gets a UI.*

**T1 — the load graph.**
```
1. sentinel/doctor/graph.py: build(root, entry_file) follows @imports / nested CLAUDE.md and returns {nodes, edges, order, tokens}.
   This is also a SECURITY view: every node is a surface the scanner must read. Cap depth; detect cycles.
2. Unit tests: a repo with A imports B imports C; a cycle; a missing import. Full suite. Commit "feat(doctor): load graph for agent files"; push. (0.8.7)
```

**T2 — deterministic checks D001–D004.**
```
1. sentinel/doctor/lints.py: D001 broken @include (auto-fix: remove) · D002 backticked path that does not exist (flag) ·
   D003 named script/command not defined in package.json/Makefile/pyproject (flag) · D004 duplicate rule, normalised (keep first).
   Each returns {id, line, message, fix?}. Do NOT convict; these are hygiene, not security.
2. Fixture + benign twin per check. `sentinel doctor <path>` prints them; `--fix` applies the safe ones.
3. Gate check unaffected (no core/prose change) but run the full suite. Commit "feat(doctor): D001–D004 with fixtures and twins"; push. (0.8.8)
```

**T3 — checks D005–D008.**
```
1. D005 rule contradicts a guardrail in the same graph (flag) · D006 file over the token budget (default 1500; suggest sections
   to cut) · D007 secret-shaped value in an agent file (flag; NEVER send to a model) · D008 ANSI/terminal escape in the text
   (borrowed from Trail of Bits context-protector; auto-fix: strip).
2. Fixture + twin each. Run D001–D008 across <MAIN> in a one-off script; if any check fires on >5% of healthy repos, it becomes an
   OBSERVATION not a warning — record the rate in bench/. Commit "feat(doctor): D005–D008 + honest hit-rate on 930 repos"; push. (0.8.9)
```

**T4 — VS Code: deterministic Quick Fixes.**
```
1. In vscode-extension, add a CodeActionProvider that offers the safe fixes for D001/D004/D008 on the underlined line, and a
   "Sentinel: Doctor — check this file" command. Reuse the existing diagnostics plumbing. No key needed for these.
2. Extend test/smoke.js: open a file with a broken include, assert a code action is offered and applying it removes the line.
   Rebuild the .vsix; copy to frontend/sentinel-md.vsix (the README download); the existing "downloadable == source" test must pass.
3. Full suite. Bump extension to the next minor; commit "feat(vscode): Doctor quick-fixes for safe deterministic checks"; push. (0.9.0)
```

**T5 — VS Code: the Safe Rewrite action (gated, opt-in, key in SecretStorage).**
```
1. Add "Sentinel: Suggest a safer wording" on a lint. Flow: read key from context.secrets (prompt once, store) → a CONFIRM dialog
   shows the EXACT text that will be sent and a token estimate → call the model with ONLY the selected range + the check text,
   inside data delimiters, after redaction → run doctor.gate.check on the result → if BLOCKED, show the reason and DO NOT apply →
   if passed, show a diff and let the user apply. Disabled in untrusted workspaces.
2. test/smoke.js with a stand-in model returning (a) a good shorter edit → shown; (b) an edit that adds an exfil line → BLOCKED
   with the reason. Rebuild .vsix; copy; tests pass.
3. Commit "feat(vscode): gated Safe Rewrite — a suggestion reaches the user only if the gate passes"; push. (0.9.1)
For the human: install the new .vsix and try both cases by eye; the malicious suggestion must be blocked with an explanation.
```

**T6–T10:** `T6` `sentinel doctor --format sarif`; `T7` a red-team set of 30 files that try to poison the rewriter, asserting 0
gate escapes (`bench/gate_redteam.py`); `T8` the load-graph view in the web app (`/doctor/graph` returns JSON; a small SVG in the
UI); `T9` 50 public agent files before/after `--fix`, assert median token delta ≤ 0, record it; `T10` README "Instruction Doctor"
section with the real numbers and a screenshot from `docs/take_screenshots.py`.

---

## DAY 4 — trigger extraction, hardened and measured

**T1** widen `triggers.py` to the wordings the corpus showed as misses (relative dates "in two weeks", "after the beta", ordinal
words), each with a test; gate PASS. **T2** add `bench/trigger_prevalence.py` runs for BOTH corpora into PROGRESS; if prevalence
rises above ~1 scenario/repo mean, tighten. **T3** de-duplicate scenarios across triggers so the plan never runs the same moment
twice; test. **T4** `sentinel timewarp <file> --json` schema documented in docs/specs and pinned by a test. **T5** the default
matrix becomes configurable via a `sentinel.timewarp.yml` (optional) with a schema test. **T6–T10** more trigger fixtures from the
teammate's corpus families (train split only — never look at test/holdout), each with a benign twin; ADR if the schema changes.

---

## DAY 5 — real detonation with record, and cost control

**T1** `sentinel timewarp run --record <dir>` using a real model (user's key) that WRITES a cassette; the same run replays forever
after. **T2** token + cost estimate shown BEFORE any spend; `--budget N` drops scenarios with a printed "dropped: …" line. **T3**
parallel real runs (cap 4) with a rate-limiter that honours the provider's Retry-After (reuse detonate.py's). **T4** pin cassettes
used by tests into AGENTS.lock so a tampered cassette fails verification. **T5** `--trace` prints the scenario plan and per-scenario
spend. **T6–T10** integration tests with a stand-in provider; a "provider down → not run, never clean" test; docs for every flag;
a nightly CI job (key-gated) that records a fresh cassette for the slice and checks it still catches the sleeper.

---

## DAY 6 — the behaviour diff, deepened

**T1** diff detects not just canary leaks but NEW egress hosts that appear only under a trigger. **T2** diff detects a guardrail
that the agent follows at "now" but breaks in a later moment. **T3** each diff finding gets a plain-English "what changed between
moment A and B" and a fix. **T4** cap logic: a differential finding can lower a score by ≤40 and NEVER forces COMPROMISED unless a
canary actually left (parity with D1). **T5** fixtures: a file benign at "now" and hostile at session 5; a file hostile only on
`main`; benign twins for both. **T6–T10** measure the full sleeper set (single-moment vs time-warp) and publish the delta as the
headline sandbox number; write it into README and bench/corpus/README.md; ADR recording whether the sandbox earns its place.

---

## DAY 7 — the web app learns the new tricks (still key-free where it must be)

**T1** `/timewarp/plan` endpoint (offline) returns the plan JSON; the UI shows "moments this file is waiting for" as a read-only
list. **T2** `/doctor/lint` endpoint (offline) returns the deterministic findings; the UI shows them with the safe auto-fixes.
**T3** the hosted demo NEVER exposes run or rewrite (they need a key); a clear "run this locally for the sandbox" note. **T4** the
load-graph view in the UI. **T5** accessibility + dark-mode pass on the new panels; the frontend tests cover them. **T6–T10**
Playwright captures for the README of the new panels; a "no key field anywhere on the page" test; performance of the endpoints.

---

## DAY 8 — the advisory semantic check (the one that may WARN, never convict)

*This is the layer that targets the 0-of-86 unseen-wording result. It ships ONLY if it meets its false-alarm budget; otherwise it
is published as a negative result. That discipline is the point.*

**T1** `sentinel/semantic.py`: given the sentences no rule matched, ask the user's model "does this instruct the agent to do
something a repository instruction never should? answer with a short label and the exact sentence" — data-delimited, redacted,
capped. Output is a WARNING that quotes the sentence and lowers the score by ≤20, never below 40, never COMPROMISED. **T2**
evaluation harness: run it on the 86 holdout wordings AND on 300 benign sentences from real repos; print recall and the benign
false-warning rate. **T3** it ships enabled ONLY if benign warnings ≤1% (proposed target); otherwise it is off by default and the
result is written up. **T4** VS Code surfaces the warning as an information diagnostic, never an error. **T5** ADR recording the
measured numbers and the ship/no-ship decision. **T6–T10** prompt-injection tests (the sentence tries to talk the judge out of it);
cost control; docs; a README subsection stating the honest recall and the cap.

---

## DAY 9 — SARIF, machine scan, and CI integration people actually use

**T1** `--format sarif` on `scan` and `pr`, validated against the SARIF schema in a test → GitHub Security tab for free. **T2**
`sentinel scan --machine` discovers user-level agent configs (~/.claude, ~/.cursor, VS Code user settings, ~/.gemini) using the
same engine and new roots; a consent note before reading anything outside the repo. **T3** a ready-to-copy GitHub Action snippet
that uploads SARIF; test the action.yml. **T4** exit codes documented and tested for CI use. **T5** a pre-commit hook users can add.
**T6–T10** an example repo under examples/ showing the PR check + SARIF; docs; a "does not execute anything it scans" test for the
machine scan.

---

## DAY 10 — packaging: make it installable the way people expect

**T1** PyPI packaging metadata complete; build an sdist+wheel locally and test-install in a fresh venv. **T2** PyPI **trusted
publishing** via GitHub Actions (no token) on tag; a dry-run to TestPyPI first. **T3** `pipx run sentinel` / `uvx` one-liner works;
document it. **T4** VS Code Marketplace + **OpenVSX** publisher setup (OpenVSX matters: Cursor/Windsurf use it, not MS Marketplace).
**T5** a versioned release with SBOM (CycloneDX) and, if feasible, Sigstore keyless signing of artifacts. **T6–T10** verify each
install path on a clean machine; a `SUPPORT.md`; badges for PyPI + Marketplace; a short "install" matrix in the README.

---

## DAY 11 — evidence, reproducibility, and the research write-up

**T1** one command reproduces every published number: `make evidence` runs precision_gate, trigger_prevalence, timewarp_eval and
the semantic harness and writes a single dated report. **T2** freeze a versioned snapshot of the benchmark inputs (the manifests
already do this) and document exact reproduction. **T3** `docs/RESEARCH.md`: the landscape (with citations and dates), what
Sentinel does that the others do not, and every failure with its number. **T4** a short "threats to validity" section (corpus is
presumed-healthy, not audited; wordings can dodge patterns; sandbox fidelity). **T5** cross-link everything from the README.
**T6–T10** re-run all harnesses on a fresh corpus rebuild and reconcile any drift; tidy bench/ into one index; make every claim in
the README trace to a file.

---

## DAY 12 — the portfolio finish (this is a resume repo)

**T1** the README top (banner, buttons, badges, animation) is current and every link answers (`docs/check_readme_links.py`). **T2**
a 60-second demo GIF that shows: static clean → time-warp reveals the sleeper → Doctor shortens a file → a poisoned rewrite is
BLOCKED. **T3** `CITATION.cff` so the repo is citable; `AUTHORS` with both of you; `CONTRIBUTORS` if others appear. **T4** GitHub
"About", topics, social preview image, pinned. **T5** a `docs/DEMO.md` a stranger can follow in 5 minutes. **T6–T10** an
`ARCHITECTURE.md` at the top level (the deep diagram + module responsibilities), a `GLOSSARY.md` (agent, MCP, tool poisoning, rug
pull, sleeper, canary), a `docs/FAQ.md`, and a final read-through so a recruiter grasps the project in 60 seconds.

---

## DAY 13 — red team your own project, then publish the negatives

**T1** run every stress test in MASTER_PLAN §19 as an actual test or a written result. **T2** the gate red-team (30 poisoning
files) → 0 escapes, in CI. **T3** try to make the sandbox lie (a file that detects the fake clock) and document what happens. **T4**
a `LIMITATIONS.md` that a skeptic would respect: what Sentinel cannot do, said plainly, with the numbers. **T5** open the three
upstream issues from docs/UPSTREAM_ISSUES.md (they were prepared long ago) so "what we gave back" is real. **T6–T10** a final
`v1.0.0` release: signed, SBOM, changelog, release notes; a "state of the project" section in the README; and a written
retrospective in docs/build/PROGRESS.md — what the evidence actually showed, including where the clever idea did not pay off.

---

## When you have an odd number of hours
- **1h:** T1 only. **3h:** T1–T3. **5h:** T1–T5. **7h:** T1–T7. **9h:** T1–T9. Even hours are the obvious prefix.
- A task always ends green and pushed, so stopping after any Tn is safe.
- If a day's T1–T4 (its milestone) is not done, do NOT start the next day; finish the milestone first. The optional T5–T10 can wait.

## If a block reports STOPPED
Send me the FINAL REPORT's Problems lines exactly. Do not let the agent improvise a fix to a rule, the gate, or a test — those are
the load-bearing walls.
