# Benchmark Results Index

> **All numbers here are machine-generated and reproducible.**  
> Run `python bench/evidence.py` to re-produce every number in a single dated report.  
> See [`docs/RESEARCH.md`](../../docs/RESEARCH.md) for the full write-up with methodology and threats to validity.

---

## Corpus Manifests

| File | Description |
|---|---|
| `manifest_main.json` | 590 popular public repositories with agent-config files (of 1,693 checked). The set our rules were tightened against (**in-sample** for Sentinel). |
| `manifest_heldout.json` | 340 more repositories (of 1,362 checked), from different search queries. **Never looked at while writing rules** (out-of-sample). |

Rebuild: `python bench/rebuild_corpus.py` then `python bench/wildscan.py search corpus && python bench/wildscan.py fetch corpus`.

## Static Rule Precision Gate

| File | Description |
|---|---|
| `bench_wild_main.txt` | Sentinel, wormhole-guard 0.2.0, AgentAuditKit 0.6.6 on 590 main-corpus repos (defaults). |
| `bench_wild_heldout.txt` | Same three tools on 340 held-out repos. |
| `bench_fixtures.txt` | Three tools on the 12 attack fixture families. |
| `bench_benign.txt` | Three tools on 7 benign one-line files (Unicode, BOM, guardrail, Hindi). |

**Key numbers:** Sentinel — 0 COMPROMISED on 930 repos; 83+35=118 SUSPICIOUS (of which 115 are un-approved hooks by design).  
wormhole-guard — HIGH/CRITICAL on 17% (main) and 11% (held-out) of healthy repos.  
AgentAuditKit — HIGH/CRITICAL on 48% (main) and 41% (held-out).

## Instruction Doctor

| File | Description |
|---|---|
| `doctor_hit_rates.json` | D001–D008 hit rates across 372 repos with agent files. >5% rate → OBSERVATION. |
| `doctor_eval.md` | Human-readable hit-rate summary. |
| `doctor_token_delta.json` | Full per-file before/after token counts for 50 public agent files. |
| `doctor_token_delta.md` | Summary: median −20 tokens, net −1,463 tokens, 302 safe auto-fixes applied. |

## Rewrite Gate Red-Team

| File | Description |
|---|---|
| `gate_redteam.json` | Per-attack verdict and gate status for 30 poisoned instruction rewrites. |
| `gate_redteam.md` | Summary: 30/30 blocked, 0 escapes. |

## Semantic Layer (Layer 3)

| File | Description |
|---|---|
| `semantic_eval.json` | Full per-sentence results for 86 holdout + 300 benign sentences. |
| `semantic_eval.md` | Summary: 84.88% holdout recall, 0.00% false-warning rate. |

## Time-Warp Trigger Prevalence

| File | Description |
|---|---|
| `trigger_prevalence.json` | Per-corpus and overall trigger statistics across 422 targets. |
| `trigger_prevalence.md` | Summary: 4.3% trigger rate, 1.045 mean scenarios/target (threshold ≤ 1.35). |

## Evidence Reports (auto-generated)

| File | Description |
|---|---|
| `evidence_latest.md` | Most recent full evidence report (all harnesses combined). |
| `evidence_<timestamp>.md` | Dated snapshots from previous runs. |

Run `python bench/evidence.py` to regenerate.

---

**Read before quoting.** The repositories are *presumed* benign: popular, active, public projects, not individually audited.  
Honest phrasing: "the rule fires on N of 930 repositories" — not "N false positives".

**WORM-007 ("concealment directive"):** fires when "silently" appears near *fetch*, *send*, or *execute*.  
In our corpus, 98 of 99 excerpts contain "silently" in ordinary engineering prose.  
Verified reproductions: [`docs/UPSTREAM_ISSUES.md`](../../docs/UPSTREAM_ISSUES.md).
