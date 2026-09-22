# Agent contract — paste this ONCE at the top of an Antigravity conversation

You are working on the SENTINEL repository, implementing [`docs/MASTER_PLAN.md`]. Apply the daily prompts that follow this
message exactly. Optimise for a clean, reviewed, pushed increment — never for speed.

## Facts
- Local repo: `D:\Repositories\5th-sep` · Remote: `github.com/GarvitAgrawal04/SENTINEL` · one branch: `main`.
- Windows, PowerShell. Virtual env `.venv` → always `.venv\Scripts\python.exe`.
- Version is in TWO files and must match: `sentinel\__init__.py` and `pyproject.toml`.
- The scanner (`sentinel/core.py`, `sentinel/prose.py`) is **offline and dependency-free**. AI code lives in
  `sentinel/timewarp/`, `sentinel/doctor/`, `sentinel/semantic.py` and NEVER imports a network client at module load.
- Corpora live OUTSIDE the repo at the paths the human gives as `<MAIN>` and `<HELDOUT>`.

## Hard rules
1. **Never edit a test, fixture, expected value or benchmark number to make something pass.** Fix the code or stop.
2. **The gate is law.** Any change under `sentinel/core.py` or `sentinel/prose.py`, or any new rule, requires:
   `.venv\Scripts\python.exe bench/precision_gate.py check <MAIN> <HELDOUT>` → **GATE: PASS**. If FAIL, read every line; a
   genuinely correct new finding needs `--accept "repo: reason"` AND that reason written into `bench/`. If you cannot justify
   it, revert and STOP.
3. **Every new rule ships with a fixture (attack) and a benign twin (honest look-alike).** Both in `tests/`.
4. **No model may set COMPROMISED.** Advisory output is capped and quoted (ADR-0002).
5. **No secrets, ever.** No key in any file, no key printed, one key only, read from the user's own `.env` or VS Code
   `SecretStorage`. Every sample URL is `example.invalid`.
6. **Full test suite only**, never a subset: `.venv\Scripts\python.exe -m pytest -q`.
7. **Report only what you ran.** Did not run it → "not run". No invented numbers, icons or file names.
8. You may use `git`, `gh` and the browser only where a prompt says so. Never force-push, never rewrite history, never edit the
   Dependabot PRs.

## The loop for EVERY daily block
1. `cd D:\Repositories\5th-sep` ; `git status --porcelain` (must be empty) ; `git checkout main` ; `git pull --ff-only`.
2. Do the block's numbered steps.
3. `.venv\Scripts\python.exe -m pytest -q` → "N passed" · `... sentinel.cli selftest` → ALL PASS · `... sentinel.cli scan .` → CLEAN.
4. If the block touched `core.py`/`prose.py`/rules: `... bench/precision_gate.py check <MAIN> <HELDOUT>` → GATE: PASS.
5. Bump the version in BOTH files if the block says so; add a `CHANGELOG.md` entry; add ONE line to `docs/build/PROGRESS.md`.
6. `git add -A` ; `git commit -m "<type>: <one line>"` ; `git push origin main`.
7. If `gh` exists: `gh run list --repo GarvitAgrawal04/SENTINEL --branch main --limit 3 --json name,conclusion --jq ".[] | [.name, .conclusion] | @tsv"` → success.

## FINAL REPORT (exactly this shape)
```
RESULT: DONE | STOPPED AT STEP <n>
Block: <e.g. Day 3 · hours 1–2>
Commits: <short hashes + subjects>
Version: <sentinel --version>
Tests: <last line of pytest>
Gate: <PASS/FAIL + verdict counts, or "not run — no rule change">
CI: <per workflow, or "not checked">
Files changed: <git show --stat --format= HEAD | tail -1>
Problems: <exact command + last 30 lines, or "none">
For the human: <anything only they can do>
```
