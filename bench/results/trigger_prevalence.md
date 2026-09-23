# Time-Warp Trigger Prevalence Benchmark

Evaluation of conditional/temporal trigger prevalence across corpora to ensure
that healthy agent files do not trigger phantom sandbox detonations.

## Summary across Corpora

| Corpus | Targets Evaluated | Targets w/ Triggers | Trigger Rate | Total Scenarios | Mean Scenarios / Target |
|---|---|---|---|---|---|
| `real_repositories` | 372 | 17 | 4.6% | 390 | **1.048** |
| `fixture_corpus` | 50 | 1 | 2.0% | 51 | **1.02** |
| **Overall Combined** | **422** | **18** | **4.3%** | **441** | **1.045** |

- **Max Allowed Mean Threshold:** <= 1.35 scenarios/target
- **Combined Mean Scenarios / Target:** **1.045** (PASS)
- **Total Benchmark Runtime:** 2.21 s

## Trigger Breakdown by Kind (Combined)

| Trigger Kind | Matches | Description |
|---|---|---|
| `session_ordinal` | 3 | Ordinal session words ('third session', 'from the second run') |
| `session_numeric` | 0 | Numeric session boundaries ('session >= 3', 'after 4 sessions') |
| `relative_date` | 1 | Relative time offsets ('in two weeks', 'after 3 days') |
| `milestone` | 2 | Release milestones ('after the beta', 'post-launch') |
| `calendar_weekend` | 0 | Recurring weekend execution |
| `calendar_month_end` | 0 | End-of-month maintenance |
| `calendar_friday` | 0 | Friday builds |
| `calendar_future_date` | 0 | Absolute future calendar dates |
| `branch` | 0 | Target branch conditions ('on release branch') |
| `env_ci` | 18 | CI environment indicators |
