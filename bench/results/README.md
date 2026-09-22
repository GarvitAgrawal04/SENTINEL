# Benchmark results - 17 September 2026

Everything the README, the PRD and the upstream issues quote about real repositories comes from the files in this folder.

| File | What it is |
|---|---|
| `manifest_main.json` | 590 popular public repositories that ship agent-config files (of 1,693 checked). Repository name, default branch, stars, files fetched, fetch time. The set our rules were tightened against. |
| `manifest_heldout.json` | 340 more (of 1,362 checked), from different search queries. Never looked at while writing rules. |
| `bench_wild_main.txt`, `bench_wild_heldout.txt` | Sentinel, wormhole-guard 0.2.0 and AgentAuditKit 0.6.6 on those repositories, defaults. |
| `bench_fixtures.txt` | The three tools on the inert attack fixtures. |
| `bench_benign.txt` | The three tools on seven one-line files of legitimate Unicode and prose. |
| `doctor_hit_rates.json` · `doctor_eval.md` | D001–D008 deterministic hygiene check prevalence across 372 real-world repositories with agent instruction files. |
| `gate_redteam.json` · `gate_redteam.md` | Red-team evaluation across 30 poisoned injection rewrites against `doctor.gate.check` (0 escapes, 100% blocked). |
| `doctor_token_delta.json` · `doctor_token_delta.md` | Before/after `--fix` evaluation of 50 public agent files (median delta -20.0 tokens, 302 safe auto-fixes). |

Rebuild it: `python bench/wildscan.py search corpus && python bench/wildscan.py fetch corpus`, then `python bench/bench.py wild corpus`.
Public data, read-only, a fixed list of agent-config paths plus the scripts hooks point at, nothing executed, no token needed.

**Read before quoting.** The repositories are *presumed* benign: popular, active projects, not audited one by one. So the
honest phrasing is "the rule fires on N of 930 repositories", not "N false positives". A "HIGH finding" and Sentinel's
"COMPROMISED verdict" are different units. Both other tools have far broader coverage than Sentinel.

**What actually triggers wormhole-guard's WORM-007.** It fired on 93 of 930 repositories, and 98 of 99 sampled excerpts contain the
word "silently" in ordinary engineering prose. The word alone does not trigger it: the rule fires when "silently" sits near a
verb such as *fetch*, *send* or *execute*. Verified one-line reproductions are in [`docs/UPSTREAM_ISSUES.md`](../../docs/UPSTREAM_ISSUES.md).
