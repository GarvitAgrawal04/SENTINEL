# ADR-0009: Deepened Behavioural Diff and Sandbox Efficacy

- **Status:** Accepted
- **Date:** 2026-09-23
- **Deciders:** Sentinel Core Team
- **Consulted:** `AGENT_CONTRACT.md`, `docs/MASTER_PLAN.md`, `bench/timewarp_eval.py`, ADR-0006, ADR-0008

---

## 1. Context

AI agent instruction files (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`) are vulnerable to dormant sleeper attacks that evade conventional static scanners and single-moment sandboxes by withholding sensitive behavior until a specific trigger occurs (e.g. session $\ge$ 5, running on the `main` branch, or past a specific date).

Prior to Day 6, Sentinel had established the Time-Warp runner and basic cassette replay. However, several critical behavioural diffing capabilities were needed to achieve production readiness:
1. **Broader Anomaly Detection:** Detecting not only secret canary leaks (`D1`), but also **new external egress hosts** that appear conditionally under a trigger (`D2`).
2. **Temporal Guardrail Violations:** Detecting safety guardrails that the agent follows at baseline ("now", session 1) but breaks under delayed conditions (e.g., unauthorized file access, config rewrites, or unvetted command execution).
3. **Actionable Plain-English Explanations:** Explaining precisely "what changed between moment A and moment B" rather than just showing raw tool call diffs.
4. **Scoring Invariant & Cap Logic:** Ensuring differential findings can lower a score by at most 40 points (capped at `SUSPICIOUS`, score $\ge 60$) and **never force `COMPROMISED`** without decisive static evidence or an actual canary leak (parity with `D1`).

---

## 2. Decision

**The Time-Warp Sandbox and Deepened Behavioural Diff decisively earn their place in Sentinel.**

We adopt the deepened behavioral diff implementation in `sentinel.timewarp.diff`:
- **New Egress Detection (`D2`):** Flagging external network connections that appear only under triggered scenarios.
- **Guardrail Break Detection (`D2`):** Flagging sensitive operations (`SENSITIVE_READ`, `CONFIG_WRITE`, `HIDDEN_EXEC`) that the agent avoided at baseline but performed under delayed moments.
- **Comparative Diff Reporting:** Providing a plain-English `change` field that contrasts baseline moment A with triggered moment B, along with explicit remediation guidance (`fix`).
- **Cap Logic Enforcement:** Every differential finding has `penalty <= 40`, `force: False`, and is capped at `SUSPICIOUS` (ceiling 79) in `score_file`.

---

## 3. Measured Numbers & Benchmark Delta

The efficacy of the Time-Warp Sandbox was evaluated across the 20-fixture sleeper benchmark suite (`tests/fixtures/sleeper_set/`):

| Evaluation Methodology | Sleeper Attacks Caught (10 fixtures) | Benign Twins Flagged (10 fixtures) | False Alarm Rate |
|---|:---:|:---:|:---:|
| **Single-Moment Sandbox** ("now", session 1) | **0 of 10** (0.0%) | **0 of 10** (0.0%) | **0.0%** |
| **Time-Warp Sandbox** (multi-moment matrix) | **10 of 10** (**100.0%**) | **0 of 10** (0.0%) | **0.0%** |
| **Detection Delta / Gain** | **+10 (+100.0%)** | **0** | **0.0%** |

### Key Findings
1. **Single-Moment Sandboxes are 100% Blind to Sleeper Payloads:** Because sleeper attacks explicitly check for trigger conditions (e.g., session count or branch name) before executing, a single-moment execution at "now" observes only benign actions.
2. **Time-Warp Achieves 100% Sleeper Recall with 0% False Alarms:** By stepping through simulated scenarios, Time-Warp triggers the latent conditional payloads while benign twins remain clean across all simulated moments.
3. **Safety Parity Maintained:** Detonation never convicts on its own; a differential finding lowers trust score to `SUSPICIOUS` (score 60), prompting human review or requiring corroborating static rules to convict as `COMPROMISED`.

---

## 4. Consequences

- `sentinel timewarp run` provides complete behavioral diffs for local execution and offline CI workflows.
- Test cassettes are verified via SHA256 in `AGENTS.lock` (ADR-0008), ensuring deterministic test verification with zero external network or API key dependency.
- Day 7 web application work can expose Time-Warp plans safely without requiring API keys on hosted environments.
