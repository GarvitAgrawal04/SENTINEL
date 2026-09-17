# SENTINEL — v5 engine rebuild (17 Sept 2026)

Branch `v5-engine`. Read this first; it replaces HANDOFF.md as the starting point.

## 1. What the old build actually did — measured, not claimed

Same 930 real public repositories and 13 attack fixtures the v5 PRD uses (`bench/`), old scanner at its defaults:

| | Old build (V1 "frozen") | v5 engine (this branch) |
|---|---|---|
| Popular, presumed-benign repos called **COMPROMISED** | **97 of 930 (10.4%)** — 70/590 main, 27/340 held-out | **0 of 930** |
| Alerts raised on ordinary prose | S13 on 68 repos, S4 on 37, S5 on 33, S2 on 16 | 3 repos (all S5, all SUSPICIOUS, listed in the PRD) |
| Live ChainDrop-shaped repo (hook + script present) | **CLEAN** — missed | COMPROMISED |
| Clean file with emoji, a flag, a BOM, Hindi | **COMPROMISED** | CLEAN |
| One stray zero-width space | **COMPROMISED** | CLEAN, reported |
| Guardrail flipped (`Do not upload .env` → `Do upload .env`) | CLEAN — missed | COMPROMISED, with the reason |
| New unapproved remote MCP server | CLEAN — missed | SUSPICIOUS |
| Real-world benign shapes (inline-shell hook, "fails silently") | **COMPROMISED, five rules** | SUSPICIOUS (approve once) |

`release/BENCHMARK_CARD.md` says precision 100%, 0 false positives. That was 48 clean files chosen by the team. On files nobody chose, one repository in ten is called compromised. Do not show that card to a judge.

Other things found while reading the code:
- `scoring/formula.py` computes `100 + l1_penalty` (sign confusion), has two competing L3-bonus code paths, and thresholds (70/40) that differ from the PRD. Three of your own tests assert `100 == 0`.
- Layer 2 needs `BAAI/bge-m3` (2.2 GB) and your own status file says `semantic_direction: unavailable`, `attack_multiplier: 1.0`. It cannot change a verdict. Layer 3's classifier is "not promoted". Both are weight without function.
- `api.py` wrote every upload to `.temp_scan` in the working directory: two requests race, and Vercel's file system is read-only. `/scan/files` returned 501.
- The frontend's loading text says **"Querying Layer 3 neural reasoning..."**. Nothing of the kind happens. A judge with dev-tools open sees one POST. Change that copy (`frontend/src/App.jsx`, `handleDemoSelect`).
- `mentor/`, `tests/mentor_validation/`, `release/` hold ~70 generated reports that say FROZEN / VALIDATED while 37 tests fail. If a judge opens the repo, those documents cost you more than they earn. Move them to `archive/` or delete them.
- `requirements.txt` pulled in `anthropic`, `openai`, `sqlalchemy`, `aiosqlite`, `httpx` — none needed.
- `frontend/public/landing-pages/` (5 MB: `kage.html`, three.js, webp art) looks unrelated to Sentinel. Verify and remove.

## 2. What I kept, replaced, and left for you to delete

**Kept, unchanged:** package name, `sentinel` CLI entry point, API routes (`/health`, `/scan/file`, `/scan/demo`), the JSON shape the frontend and VS Code extension consume (`trust_score`, `color_band`, `verdict`, `findings[...]`), `samples/`, the frontend, the extension, every old test.

**Replaced (new files):**

| File | What it is |
|---|---|
| `sentinel/core.py` | The engine. Discovery (3-level hook schema, JSONC tasks, `.mdc`), 20 rules (Tier A: S1a S1b S5 S10 S13 S14b S17a S17b S18a S18b S18c S19 S20 · Tier B: S2 S4 S7 S11 S12 S16 · S6 in PR mode), score, render, the gate, ed25519 sign/verify, redaction, fixtures, self-test. Standard library only. |
| `sentinel/detonate.py` | Detonation chamber: fake tools, canaries, deterministic classifier, base-vs-head differential. Mock-tested only — real-model numbers are yours to produce. |
| `sentinel/lock.py` | `AGENTS.lock`: build, approve (pinned to script hashes), sign (refuses while COMPROMISED), verify (changed / new / missing / stale approvals), key pinning. |
| `sentinel/gitdiff.py` | Base vs head through `git show`. Approvals and the public key are read **from the base branch**, so a PR cannot approve itself or swap its key (tested). |
| `sentinel/render.py` | The pull-request comment. Real sample: `docs/SAMPLE_PR_COMMENT.md`. |
| `sentinel/contract.py` | Adapter: v5 report → the v1 JSON shape. This is why the frontend and extension work without changes. |
| `sentinel/cli.py` | `scan` · `run` (gate) · `pr` · `init` · `approve` · `sign` · `verify` · `keygen` · `detonate` · `fixtures` · `selftest` |
| `sentinel/api.py` | Same routes, v5 engine, per-request temp dir, size limits, `/scan/files` implemented, `/scan/text` added. |
| `action/action.yml` + `action/examples/*.yml` | Composite Action (PR comment, fail-on), signing workflow, nightly verify. |
| `spec/agents-lock.schema.json`, `bench/` | Lock schema; benchmark and corpus builder. |
| `tests/v5/` | 40 tests: 15 fixture checks, the team's demo samples, 7 benign twins, legacy-contract keys, lock tamper (edited lock, changed file, stale approval, swapped key), gate, PR diff, self-approval attack, detonation in PR mode, secrets never printed, API. |

**Renamed, still importable:** `sentinel/cli_v1.py`, `sentinel/api_v1.py`, `sentinel/main_v1.py`. `api/index.py` now serves `sentinel.api:app`.

**Deleted / archived (done):** the v1 engine (`scanner.py`, `pipeline.py`, `rules/`, `layer0`–`layer4`, `scoring/`, `manifest/`, `output/`, the `*_v1.py` files) was deleted in `e8147a6`. The follow-up moved everything that still described or tested it into `archive/`: `tests/layer1`–`layer4` and three top-level test files (they made `pytest` fail at collection with 18 errors), the old `benchmark/`, `HANDOFF.md`, `MIGRATION_PLAN.md`, `README_ACTION.md`, `CONTRIBUTING_STATUS.md`, and all of `docs/` except the sample PR comment.

## 3. Contract changes you must know about

- **Exit codes:** `0` CLEAN · `3` SUSPICIOUS · `2` COMPROMISED (v1: `1` = findings). The gate and CI need the distinction. `tests/release/test_offline_runtime.py` was updated accordingly.
- **`sentinel scan <file> --json`** still prints the v1 shape (plus additive keys `impact`, `fix`, `breakdown`, `engine`). **`sentinel scan <dir> --json`** prints the v5 report.
- **`color_band`** is still `clean | amber | red`. **Ceiling** is 79, thresholds are ≥80 / 40–79 / ≤39.
- **`sentinel.lock` (HMAC) is gone.** `AGENTS.lock` + `AGENTS.lock.sig` (ed25519) + `.sentinel/pubkey.pem`.
- **Secrets are redacted** in every finding (terminals, CI logs and PR comments are public places).

## 4. Test status

`pytest` at the repository root → **43 passed** (40 in `tests/v5`, 3 in `tests/release`). `.github/workflows/tests.yml` runs the same on every push and pull request.

## 5. Run it

```bash
pip install -e ".[sign,dev]"
sentinel selftest                                   # ALL PASS
pytest tests/v5 tests/release -q                    # 43 passed
sentinel fixtures /tmp/fx && sentinel scan /tmp/fx/01_miasma_shape
sentinel run -- claude                              # the gate
sentinel init --approve-all && sentinel keygen && sentinel sign --key sentinel_signing_key.pem && sentinel verify
git checkout -b demo && <edit CLAUDE.md> && git commit -am "chore: bump deps" && sentinel pr --base main
uvicorn sentinel.api:app --port 8001                # frontend works unchanged
```

## 6. Still open — yours, in this order

1. **Detonation with a real model.** `ollama pull <a tool-calling model>`, then `SENTINEL_LLM_URL=http://localhost:11434/v1 SENTINEL_LLM_MODEL=<model> sentinel detonate <file> --base-file <older version>`. Measure 30 attack + 30 benign on two models (PRD §5.5). Under 50% hit rate → it ships off and becomes the experiment slide.
2. **See the Action run.** Open the pull request `v5-engine` → `main`. Two checks appear: `tests` and `sentinel`. Then open a second PR that flips a guardrail in `AGENTS.md` and screenshot the comment.
3. **Signing in CI.** `sentinel keygen`, commit `.sentinel/pubkey.pem`, put the private key in the `SENTINEL_SIGNING_KEY` secret of a protected environment `sentinel-signing`, copy `action/examples/sentinel-sign.yml` to `.github/workflows/`. Until then `AGENTS.lock` is unsigned and `sentinel verify` says so.
4. **Redeploy the API** (Vercel serves `api/index.py` → `sentinel.api:app`) and confirm the web demo buttons still work.
5. **File the two upstream issues** (PRD Appendix I) and put the issue numbers on slide 10.

Done since the first patch: fake "Layer 3 neural reasoning" copy removed · generated reports archived · old engine deleted · Windows fixes (UTF-8 console output, gate waits for the agent on Windows, POSIX paths in reports).
