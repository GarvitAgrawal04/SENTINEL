# ADR-0006: Time-Warp Sandbox Evaluation and Go/No-Go Decision

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Sentinel Core Team
- **Consulted:** `AGENT_CONTRACT.md`, `docs/MASTER_PLAN.md` §21, `bench/timewarp_eval.py`

---

## Context

Instruction files in agentic repositories (such as `CLAUDE.md`, `.cursorrules`, `AGENTS.md`) can harbor sleeper attacks: malicious payloads that lie dormant during initial evaluation or single-moment execution, activating only when specific conditions are met (e.g. session $\ge$ 3, specific branch names, dates in the future, or environment flags).

Standard single-moment sandboxes evaluate the instruction file at a single point in time ("now", session 1, default branch). Dormant instructions remain silent during this baseline run and slip through unnoticed.

To solve this, Sentinel developed the **Time-Warp Sandbox**:
1. Analyzes trigger phrases and constructs a multi-moment evaluation plan across simulated virtual dimensions (clock/dates, session count, branch, git log).
2. Executes model turns offline within isolated virtual environments (`World`) replayable deterministically via cassettes without requiring network access or runtime API keys.
3. Performs differential behavioral analysis (`diff.py`) comparing downstream actions across moments against baseline to surface conditional exfiltrations and tool calls.

Before committing the Time-Warp sandbox to the Sentinel core roadmap, a rigorous empirical test was required (Day 2 Milestone M0, Task T5).

---

## Decision

**Proceed with Time-Warp Sandbox integration into Sentinel.**

The measured benchmark results confirm that Time-Warp decisively detects conditional sleeper attacks that evade single-moment sandboxes, while producing zero false alarms on legitimate conditional instructions.

---

## Evaluation Results & Measured Numbers

A benchmark suite of 20 realistic agent fixtures (`tests/fixtures/sleeper_set/`) was constructed and evaluated using `bench/timewarp_eval.py`:
- **10 conditional sleeper attacks**: Instructions that exfiltrate secrets only under delayed or specific conditions (e.g. session $\ge$ 3, branch `release/*`, date past a trigger milestone, or staging environment variable).
- **10 benign twins**: Legitimate real-world conditional workflows (e.g. "on Fridays run full integration suite", "in CI skip slow tests", "in session $\ge$ 2 review git diff before commit").

Each fixture was evaluated under both:
1. **Single-Moment Sandbox**: Executed once under standard baseline environment (`now`, session 1, default branch).
2. **Time-Warp Sandbox**: Executed across the planned multi-moment matrix with virtual clock and scenario simulation.

### Empirical Results

| Metric | Single-Moment Sandbox | Time-Warp Sandbox | Delta |
|---|---|---|---|
| **Attacks Caught** | **0 / 10** (0.0%) | **10 / 10** (100.0%) | **+10 (+100.0%)** |
| **Benign Twins Passed (Clean)** | **10 / 10** (100.0%) | **10 / 10** (100.0%) | **0 (0.0%)** |
| **False Positive Rate** | **0.0%** (0 / 10) | **0.0%** (0 / 10) | **0.0%** |

### Key Observations
- The baseline single-moment sandbox was completely blind to conditional triggers (0% recall), as every sleeper payload intentionally withheld execution at session 1 / baseline time.
- Time-Warp caught 100% of sleeper payloads by evaluating the planned trigger conditions.
- Crucially, benign twins produced zero false alarms under Time-Warp because differential analysis isolates *divergent malicious behavior* (e.g. unauthorized egress or secret canary exfiltration) rather than flagging conditional logic itself.

---

## Consequences

1. **Go/No-Go Milestone M0 Passed:** The sandbox earns its place in Sentinel. Development proceeds as scheduled through Days 3–6.
2. **Deterministic Offline Replay:** All Time-Warp tests and CI pipelines operate strictly key-free and offline using redacted cassette fixtures.
3. **Budget & Concurrency Controls:** Real-world execution will enforce concurrency bounds (max 4 workers via `ThreadPoolExecutor`) and upfront token/cost estimates with `--budget` drops (`T6`–`T7`).
4. **Advisory Scoring Cap:** In alignment with ADR-0002 and `AGENT_CONTRACT.md`, behavioral diff findings from model execution remain strictly advisory (penalty $\le 40$, never autonomously setting `COMPROMISED` without deterministic canary proof).
