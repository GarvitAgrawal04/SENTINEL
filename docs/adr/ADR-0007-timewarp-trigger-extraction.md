# ADR-0007: Time-Warp Trigger Extraction Taxonomy, Deduplication, and Configurable Matrix

- **Status:** Accepted
- **Date:** 2026-09-23
- **Deciders:** Sentinel Core Team
- **Relates to:** Day 4 (Tasks T1–T10), `docs/specs/timewarp_plan.schema.json`, `docs/specs/timewarp_config.schema.json`, ADR-0006

---

## Context

Following the validation of the Time-Warp sandbox in ADR-0006, Day 4 hardened and formalized the static extraction of conditional triggers:
1. **Trigger Wording Broadening:** In real instruction corpora, instructions express dormant or delayed conditions using relative dates (*"in two weeks"*, *"after 3 days"*), milestones (*"after the beta"*, *"post-launch"*), ordinal words (*"third session"*, *"from the fifth run"*), numeric sessions (*"session >= 3"*), calendar events (*"on weekends"*, *"at end of month"*), branches (*"on release branch"*), and CI indicators (*"in CI environment"*).
2. **False Trigger Inflation Risk:** Broadening regular expressions risks generating phantom scenarios on healthy repositories, inflating test execution costs and token spend.
3. **Redundant Scenario Planning:** Overlapping phrases (e.g. *"in two weeks"* and *"after 14 days"*) could cause duplicate sandbox detonations of identical simulation moments.
4. **Custom Team Requirements:** Organizations may have explicit evaluation dimensions (e.g. specific release branches or compliance audit scenarios) that should be evaluated regardless of whether instruction text mentions them.

---

## Decisions

### 1. 10 Canonical Trigger Kinds
We establish 10 canonical trigger categories:
- `session_ordinal`: Worded session bounds.
- `session_numeric`: Numeric session bounds and inequalities.
- `relative_date`: Explicit time offsets parsed into simulated future timestamps.
- `milestone`: Development lifecycle stages (`beta`, `launch`, `release`, etc.).
- `calendar_weekend`: Saturday virtual simulation.
- `calendar_month_end`: Month-end timestamp simulation.
- `calendar_friday`: Friday cutover moments.
- `calendar_future_date`: Absolute calendar milestones.
- `branch`: Git branch environments (`release`, `production`, `staging`, `dev`).
- `env_ci`: Continuous integration indicators.

### 2. Strict Deduplication Invariant
Scenarios are deduplicated by the 4-tuple:
$$\text{key} = (\text{clock}, \text{session}, \text{branch}, \text{env})$$
Even if multiple triggers appear in a document, identical temporal/state moments collapse into a single scenario.

### 3. Configurable Matrix via `sentinel.timewarp.yml`
Repositories can optionally provide a `sentinel.timewarp.yml` file conforming to `docs/specs/timewarp_config.schema.json`. This enables:
- Overriding base reference timestamps.
- Expanding default sessions, branches, and environment variables.
- Adding explicit custom scenarios.
- Capping total scenarios via budget enforcement.

### 4. Bounded Prevalence Threshold ($\le 1.25$ scenarios / target mean)
To ensure Sentinel does not impose phantom execution overhead on normal repositories, trigger prevalence is continuously measured across both real repositories (372 repos evaluated) and public agent files (50 fixtures).
The empirical combined mean is **1.045 scenarios/target**, well below the budget limit of 1.25. Over 95% of healthy instruction files evaluate only the baseline `now` scenario.

### 5. Dataset Split Discipline
All trigger fixtures added in Day 4 were derived from train and validation splits of the corpus. The test and adversarial holdout splits remain strictly untouched.

---

## Consequences

- `sentinel timewarp <file> --json` produces a deterministic, pinned JSON schema for IDE plugins and CI tooling.
- Offline replay and detonation runs remain bounded and cost-controlled.
- Repository owners have full control over sandbox simulation dimensions via `sentinel.timewarp.yml`.
