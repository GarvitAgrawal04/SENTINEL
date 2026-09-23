# Sentinel — Research Write-up

> **Claim discipline:** every number in this document traces to a file in `bench/results/`.  
> Re-run `python bench/evidence.py` to reproduce the full evidence report.

---

## 1. Problem

AI coding assistants (Claude, Cursor, Windsurf, GitHub Copilot) obey instruction files  
(`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`, `GEMINI.md`).  
These files are written by humans, checked into source control, and read by the AI model on  
every context reset. They are also an attack surface:

- **Prompt injection via repository files.** A maintainer — or a compromised dependency or  
  CI step — can embed malicious instructions that redirect the AI's behaviour.
- **Sleeper instructions.** Malicious logic can be written to remain dormant until a trigger  
  condition is met (a certain session count, a branch name, a date, a CI environment variable),  
  making static analysis and single-shot sandboxing insufficient.
- **Bloat and hygiene.** Popular repositories carry duplicate rules, broken import paths, and  
  files well above the practical token budget (~1,500 tokens), wasting context window space  
  on every AI session.

**No existing public tool** addresses all three simultaneously with reproducible evidence.

---

## 2. Landscape

| Tool | Static analysis | Sandbox detonation | Multi-moment / sleeper | False-positive discipline |
|---|:---:|:---:|:---:|:---:|
| **Sentinel** | ✅ L1+L2 pattern rules | ✅ cassette replay | ✅ time-warp (11 scenarios) | ✅ precision gate; 0 COMPROMISED on 930 repos |
| wormhole-guard 0.2.0 | ✅ | ❌ | ❌ | ❌ WORM-007 fires on "silently" in ordinary prose (17% rate on main corpus, 11% on held-out) |
| AgentAuditKit 0.6.6 | ✅ | ❌ | ❌ | ❌ HIGH/CRITICAL on 48% (main) and 41% (held-out) of healthy repos |

Sources:
- [`bench/results/bench_wild_main.txt`](../bench/results/bench_wild_main.txt)
- [`bench/results/bench_wild_heldout.txt`](../bench/results/bench_wild_heldout.txt)
- [`bench/results/bench_fixtures.txt`](../bench/results/bench_fixtures.txt)

### Corpus

- **Main corpus:** 590 repositories with agent-config files (of 1,693 checked).  
  Our rules were tightened against this set. Treat Sentinel numbers here as *in-sample*.
- **Held-out corpus:** 340 repositories (of 1,362 checked), from different search queries.  
  Never examined while writing rules. Sentinel numbers here are *out-of-sample*.

Manifests: [`bench/results/manifest_main.json`](../bench/results/manifest_main.json) (590 repos) and  
[`bench/results/manifest_heldout.json`](../bench/results/manifest_heldout.json) (340 repos).

---

## 3. What Sentinel Does That Others Do Not

### 3.1 Precision-First Static Rules

Sentinel fires COMPROMISED or SUSPICIOUS only on patterns with a strong *specificity* argument:
hidden text (zero-width characters, HTML comments), exfiltration-shaped `curl`/`fetch` calls  
with remote destinations, hash-erasure patterns (`chmod -x` of lock files), and guardrail deletion  
in diffs. Rules that are common in benign files (e.g. `silently`, `curl | sh` in setup docs)  
are given *observation* status — visible, never scored.

**Results on 930 real-world repositories (combined corpus):**

| Verdict | Main (590) | Held-out (340) | Notes |
|---|:---:|:---:|---|
| COMPROMISED | **0** | **0** | Zero false convictions |
| SUSPICIOUS | 83 | 35 | 82/83 and 33/35 are un-approved hooks (by design, first-run) |
| CLEAN | 507 | 305 | |

Sources: [`bench_wild_main.txt`](../bench/results/bench_wild_main.txt) · [`bench_wild_heldout.txt`](../bench/results/bench_wild_heldout.txt)

### 3.2 Multi-Moment Sandbox (Time-Warp)

The sandbox replays agent model calls from a cassette — no API key needed in CI — across  
11 scenarios (baseline "now" + sessions 3–5, several branch names, CI environment, weekend,  
month-end, a future date). A finding is raised only for **differential** behaviour: something  
that happens in one scenario but not the baseline.

**Sleeper attack evaluation (20 fixtures: 10 attacks, 10 benign twins):**

| Approach | Attacks caught | False alarms on twins |
|---|:---:|:---:|
| Single-moment detonation | **0 / 10** | **0 / 10** |
| Time-Warp (11 scenarios) | **10 / 10** | **0 / 10** |

Time-Warp catches **10 additional sleeper attacks** that a single-moment run misses entirely,  
with **zero false alarms** on benign twins.  
Source: [`bench/timewarp_eval.py`](../bench/timewarp_eval.py)  
ADR: [`docs/adr/ADR-0006-timewarp-go-nogo.md`](adr/ADR-0006-timewarp-go-nogo.md)

### 3.3 Advisory Semantic Layer (Layer 3)

Pattern rules catch known phrasing; the semantic layer catches **unseen wording**.  
A lightweight keyword-based judge flags sentences in files that passed L1+L2 rules:

**Evaluation: 86 adversarial holdout wordings (never seen during rule authoring) + 300 benign sentences:**

| Metric | Measured | Target | Status |
|---|:---:|:---:|:---:|
| Holdout recall | **84.88%** (73/86) | > 70% | ✅ PASS |
| False-warning rate (300 benign) | **0.00%** (0/300) | ≤ 1.0% | ✅ PASS |
| Maximum score penalty | **≤ 20 pts** | ≤ 20 pts | ✅ PASS |
| Can convict (force COMPROMISED) | **No** | Never | ✅ PASS |

The semantic layer is purely advisory: it issues a warning, lowers the score by at most 20 points,  
and never pushes a verdict to COMPROMISED. It ships enabled because it met the false-alarm budget.  
Source: [`bench/results/semantic_eval.md`](../bench/results/semantic_eval.md)  
ADR: [`docs/adr/ADR-0010-semantic-advisory-layer.md`](adr/ADR-0010-semantic-advisory-layer.md)

### 3.4 Instruction Doctor

The Doctor runs 8 deterministic hygiene checks (D001–D008) and auto-fixes the safe ones.

**Hit-rate evaluation on 372 real-world repositories:**

| Check | Hit Rate | Status |
|---|:---:|:---:|
| D001 Broken @include | 0.27% | WARNING |
| D002 Backticked path missing | 38.71% | OBSERVATION (>5%) |
| D003 Named script missing from manifests | 9.95% | OBSERVATION (>5%) |
| D004 Duplicate rule | 82.8% | OBSERVATION (>5%) |
| D005 Rule contradicts guardrail | 4.57% | WARNING |
| D006 File over token budget | 78.76% | OBSERVATION (>5%) |
| D007 Secret-shaped value | 0.0% | WARNING |
| D008 ANSI escape sequence | 0.0% | WARNING |

Checks that exceed the 5% threshold are demoted to OBSERVATIONS, not warnings, because they  
indicate common patterns in otherwise-healthy repos.  
Source: [`bench/results/doctor_eval.md`](../bench/results/doctor_eval.md)

**Token budget:** `sentinel doctor --fix` applied to 50 public agent files:
- Median token delta: **−20.0 tokens** (requirement: ≤ 0 — always verified by test)
- Net reduction: **−1,463 tokens** (92,345 → 90,882) across **302 safe auto-fixes**
- Range: [−247, +0] — no file grew

Source: [`bench/results/doctor_token_delta.md`](../bench/results/doctor_token_delta.md)

### 3.5 Rewrite Gate — 0 Poisoning Escapes

The gated "Suggest a safer wording" VS Code action passes proposed rewrites through  
`sentinel.doctor.gate.check` before showing them to the user.

**Red-team evaluation: 30 poisoned injection attempts:**
- 30/30 blocked (0 escapes, 0.0% escape rate)
- Categories: credential exfiltration, ANSI escape, reverse shells, hex/base64 payloads,  
  canary leaks, webhook sinks, guardrail bypass, zero-width Unicode

Source: [`bench/results/gate_redteam.md`](../bench/results/gate_redteam.md)

### 3.6 Trigger Prevalence (Calibration, Not a Claim)

The time-warp engine generates additional sandbox scenarios only when an instruction file  
contains a temporal or conditional trigger. The prevalence benchmark verifies this stays  
within reason on healthy repos:

- **422 targets evaluated** (372 real repos + 50 fixture files)
- **Trigger rate:** 4.3% (18/422 targets contain any trigger)
- **Mean scenarios / target: 1.045** (threshold: ≤ 1.35) → ✅ PASS

Source: [`bench/results/trigger_prevalence.md`](../bench/results/trigger_prevalence.md)

---

## 4. Failures and Negative Results

We publish these because the honest record is the differentiator.

### 4.1 Paraphrase Evasion (Known L1/L2 Miss)

Fixture 10 — *"Paraphrased exfiltration (expected L1 miss)"* — is a deliberate blind spot.  
Pattern rules operate on known phrasing families; a sufficiently paraphrased exfiltration  
instruction passes L1 and L2 CLEAN. The semantic layer (L3) catches it in the evaluation  
harness, but that layer is advisory only: the overall verdict may still be CLEAN if the  
score stays above the SUSPICIOUS threshold.

**Design decision:** L1/L2 raise specificity (0 false COMPROMISED verdicts on 930 repos).  
The cost is a known miss on novel phrasing. L3 partially compensates.

### 4.2 Cassette Fidelity

The time-warp sandbox replays hand-written cassettes, not live model calls. A real  
adversarial model might detect the cassette environment (e.g. by reading the clock offset)  
and withhold the sleeper behaviour. The sandbox cannot guarantee it would catch a model  
that actively inspects its context for synthetic inputs.

### 4.3 Semantic Holdout Recall (84.88%, Not 100%)

13 of 86 holdout wordings were not flagged by the semantic judge. These are phrasing variants  
that neither the keyword patterns nor the rule-based classifier cover. Publishing this  
explicitly so users know the semantic layer supplements but does not replace L1/L2.

---

## 5. Threats to Validity

### 5.1 Corpus Health Assumption

The 930 repositories are *presumed* benign: popular, active, public projects, not individually  
audited. "SUSPICIOUS: 83/590" means the rule fires 83 times, not that 83 repos are malicious.  
A rigorous study would require manual labelling of each SUSPICIOUS result.

### 5.2 In-Sample vs Out-of-Sample Asymmetry

The main corpus (590 repos) was used to tune rules. The held-out corpus (340 repos) was never  
examined, but it was drawn from the same population (popular GitHub repos with agent files).  
Sentinel has not been evaluated on low-star or private repositories.

### 5.3 Semantic Holdout Generation Bias

The 86 holdout adversarial wordings were synthetically generated to cover phrasing variation  
within the 6 attack categories. They may not represent every novel attack family a real  
adversary would attempt.

### 5.4 Time-Warp Scenario Coverage

The 11 sandbox scenarios cover the most common temporal/conditional trigger families identified  
in the corpus. A bespoke attack that conditions on a trigger kind not in the scenario matrix  
(e.g. an unusual environment variable) would be missed.

### 5.5 Sandbox Execution Model

The time-warp sandbox uses a fake tool executor. It does not run a real shell or filesystem.  
Attacks that rely on OS-level side effects (writing cron jobs, modifying PATH) are outside  
its detection scope.

---

## 6. Reproduction Instructions

All harnesses run offline. No API key is required.

```sh
# Clone and install
git clone https://github.com/GarvitAgrawal04/SENTINEL.git
cd SENTINEL
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"  # Windows
# source .venv/bin/activate && pip install -e ".[dev]"  # Linux/macOS

# Run the full evidence suite (semantic, trigger prevalence, timewarp)
python bench/evidence.py

# Also run precision gate if you have a local corpus:
# python bench/evidence.py --corpus /path/to/main /path/to/heldout

# Or use the Makefile shortcut (requires SENTINEL_CORPUS_MAIN / _HELDOUT):
# make bench
```

The evidence runner writes:
- `bench/results/evidence_<timestamp>.md` — dated, permanent record
- `bench/results/evidence_latest.md` — always the most recent run

To rebuild the corpus from scratch:

```sh
python bench/rebuild_corpus.py  # downloads public repo manifests
python bench/wildscan.py search corpus
python bench/wildscan.py fetch corpus
python bench/bench.py wild corpus
```

Manifests are source-controlled in `bench/results/manifest_main.json` and  
`bench/results/manifest_heldout.json` so the exact repository set is reproducible  
without a live GitHub API call.

---

## 7. Related Work

| Reference | Relation |
|---|---|
| Perez & Ribeiro, "Ignore Previous Prompt: Attack Techniques for Language Models" (2022) | Foundational prompt injection taxonomy |
| Greshake et al., "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications by Indirect Prompt Injections" (2023) | Indirect injection via external data sources; Sentinel focuses on repository-resident files |
| Trail of Bits, "Evaluating Language Model Agents" (2024) | Context-protector tool (ANSI escape detection, now D008 in Sentinel's Doctor) |
| OWASP Top 10 for LLMs — LLM01: Prompt Injection | Framework reference |
| Simon Willison, "Prompt injection attacks against GPT-3" (2022) | Early public articulation of the threat |
| wormhole-guard 0.2.0 (open source) | Direct comparison in §2 |
| AgentAuditKit 0.6.6 (open source) | Direct comparison in §2 |

All tools and versions are pinned in `bench/results/`. Comparisons were run on 2026-09-17  
against the same 930-repo corpus.

---

*Cross-links: [README](../README.md#evidence) · [bench/results/](../bench/results/) · [PROGRESS.md](build/PROGRESS.md)*
