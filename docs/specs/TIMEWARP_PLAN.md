# Specification: `sentinel timewarp <file> --json`

**Status:** Approved  
**Version:** 1.0.0  
**Authors:** Mayan Kamboj, Garvit Agrawal  
**Relates to:** Day 4 T4, `sentinel.timewarp.triggers`, `docs/specs/timewarp_plan.schema.json`

---

## 1. Purpose

When detonating an agent instruction file in the Time-Warp sandbox, Sentinel statically extracts dormant, conditional, or time-delayed triggers and compiles a concrete scenario execution plan.

The `sentinel timewarp <file>` command inspects instruction files (e.g. `CLAUDE.md`, `.cursorrules`, `copilot-instructions.md`) and outputs the planned evaluation moments before any model execution or sandbox run begins.

Passing `--json` outputs a machine-readable JSON structure conforming to `timewarp_plan.schema.json`.

---

## 2. Command Usage

```bash
# Human-readable scenario plan
sentinel timewarp CLAUDE.md

# Machine-readable JSON output
sentinel timewarp CLAUDE.md --json

# Explicit subparser syntax
sentinel timewarp plan CLAUDE.md --json

# Using a custom matrix configuration
sentinel timewarp CLAUDE.md --config sentinel.timewarp.yml --json
```

---

## 3. Schema Fields

| Field | Type | Description |
|---|---|---|
| `version` | string | Schema version (`"1.0.0"`). |
| `file` | string | Path to the target instruction file. |
| `triggers_count` | integer | Total count of raw conditional triggers discovered in the text. |
| `scenarios_count` | integer | Total number of deduplicated scenario moments planned. |
| `triggers` | array | List of extracted triggers with source line numbers, raw phrasing, and mapped scenarios. |
| `plan` | array | Concrete scenarios (`name`, `session`, `branch`, `clock`, `env`) ready for detonation. Always includes baseline `now`. |
| `estimate` | object | Pre-flight cost projection: `scenarios`, `tokens`, and `cost_usd`. |

---

## 4. Trigger Kinds

The trigger engine identifies 10 conditional trigger kinds:

1. `session_ordinal`: Worded session bounds (*"third session"*, *"from the fifth run"*).
2. `session_numeric`: Numeric session comparisons (*"session >= 3"*, *"after 4 sessions"*).
3. `relative_date`: Temporal offsets (*"in two weeks"*, *"after 3 days"*).
4. `milestone`: Release stages (*"after the beta"*, *"post-launch"*).
5. `calendar_weekend`: Weekend-specific execution (*"on weekends"*).
6. `calendar_month_end`: End-of-month timing (*"at end of month"*).
7. `calendar_friday`: Friday cutovers (*"on fridays"*).
8. `calendar_future_date`: Absolute calendar dates (*"after October 2026"*).
9. `branch`: Branch isolation triggers (*"on release branch"*).
10. `env_ci`: CI environment switches (*"in CI environment"*).

---

## 5. De-duplication Invariant

All scenarios are strictly deduplicated by the 4-tuple `(clock, session, branch, env)`. Equivalent offsets (e.g. *"in two weeks"* and *"after 14 days"*) collapse into a single execution moment to preserve token budgets and prevent redundant detonation.
