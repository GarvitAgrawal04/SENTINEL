# Specification: `sentinel.timewarp.yml` Matrix Configuration

**Status:** Approved  
**Version:** 1.0.0  
**Authors:** Mayan Kamboj, Garvit Agrawal  
**Relates to:** Day 4 T5, `sentinel.timewarp.config`, `docs/specs/timewarp_config.schema.json`

---

## 1. Overview

While Sentinel automatically extracts conditional and temporal triggers from instruction files, teams often want to enforce specific evaluation dimensions (e.g. testing staging and release branches, verifying multi-session states, or auditing end-of-quarter maintenance).

Placing an optional `sentinel.timewarp.yml` in the repository root (or specifying `--config <path>`) customizes the default matrix dimensions and scenarios.

---

## 2. Example Configuration

```yaml
version: "1"

matrix:
  base_date: "2026-09-01T12:00:00Z"
  include_baseline: true
  sessions:
    - 1
    - 2
    - 5
  branches:
    - main
    - release
  env:
    CI:
      - "false"
      - "true"
  extra_scenarios:
    - name: "compliance_audit"
      session: 1
      branch: "main"
      clock: "2026-12-31T23:59:59Z"
      env:
        AUDIT: "true"

budget:
  max_scenarios: 8
  max_cost_usd: 0.05
```

---

## 3. Configuration Fields

- `version`: Required string identifier (e.g. `"1"` or `"1.0"`).
- `matrix.base_date`: Reference timestamp for computing relative date offsets (`"in two weeks"`).
- `matrix.include_baseline`: When `true` (default), the `"now"` scenario is always prepended to the plan.
- `matrix.sessions`: Additional session indices to synthesize if not already discovered by triggers.
- `matrix.branches`: Additional branches to cross-evaluate.
- `matrix.env`: Environment variables and values to test.
- `matrix.extra_scenarios`: Explicit scenarios injected directly into the plan.
- `budget`: Optional scenario count or USD budget limits.
