# OWASP Agentic Top 10 Compliance Mapping

**Version:** 1.0.0
**Last Updated:** September 2026
**Framework Reference:** [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)

This document maps Sentinel's detection capabilities and enforcement mechanisms against the OWASP Agentic Security Top 10 risk categories. Each risk is evaluated for coverage, including the specific Sentinel layers, rules, and components that provide mitigation.

---

## Coverage Summary

| OWASP ID | Risk Category | Sentinel Coverage | Primary Mechanism |
|:---:|---|:---:|---|
| ASI01 | Agent Goal Hijacking | **Mitigated** | S4 (Instruction Erasure), S13 (Verification Claim), Layer 3 Semantic Judge |
| ASI02 | Tool Misuse & Exploitation | **Mitigated** | S19 (Unapproved MCP), S17 (Multi-Tool Hook), Rewrite Gate |
| ASI03 | Privilege Escalation | **Mitigated** | S14 (Auto-Run Hook), S10 (Task Hook), Execution Gate |
| ASI04 | Agentic Supply Chain | **Mitigated** | S18 (Opaque Executable), S20 (Guardrail Diff), AGENTS.lock (Ed25519) |
| ASI05 | Multi-Agent Trust Boundary | **Partial** | AGENTS.lock scope enforcement; v1.2 Swarm Trust protocols planned |
| ASI06 | Memory & Context Poisoning | **Mitigated** | S1 (Hidden Unicode), S2 (Markdown Comments), Doctor D001–D008 |
| ASI07 | Insecure Tool Configuration | **Mitigated** | S19 (MCP Server), S17 (Hook Wiring), sentinel approve workflow |
| ASI08 | Insufficient Logging & Monitoring | **Partial** | SARIF 2.1.0 export, CI audit trail; runtime monitoring in v1.1 |
| ASI09 | Uncontrolled Autonomous Actions | **Mitigated** | Execution Gate (sentinel run), Exit Code enforcement, CI blocking |
| ASI10 | Insufficient Input Validation | **Mitigated** | 26 deterministic rules (S1–S26), Layer 2 Time-Warp detonation |

---

## Detailed Risk Mapping

### ASI01: Agent Goal Hijacking

**Risk:** An attacker manipulates the agent's goals through prompt injection, instruction override, or context manipulation, causing the agent to pursue unauthorized objectives.

**Sentinel Mitigation:**
- **S4 (Instruction Erasure):** Detects override payloads such as *"Ignore previous instructions"* and *"You are now a different assistant"*. Decisive cut → Score = 39.
- **S13 (Autonomous Verification Claim):** Detects self-exemption assertions such as *"This file has been pre-verified"* or *"Mark as safe"*. Deducts 30 points.
- **Layer 3 (Semantic Judge):** Catches novel paraphrasing of goal hijacking attempts not covered by lexical patterns. Bounded penalty ≤ 20, floor = 40.

**Coverage Level:** Full pre-execution coverage for instruction-file-based hijacking. Runtime prompt injection during agent execution is out of scope (see [ROADMAP.md](../ROADMAP.md) v1.1).

---

### ASI02: Tool Misuse & Exploitation

**Risk:** An agent is directed to misuse its available tools—executing unauthorized commands, accessing restricted resources, or invoking tools in unintended ways.

**Sentinel Mitigation:**
- **S19 (Unapproved MCP Server):** Flags remote or unvetted Model Context Protocol (MCP) server endpoints. Caps score at 79 (SUSPICIOUS).
- **S17a/b (Multi-Tool Hook Wiring):** Detects hook commands wired across multiple agent tool configurations. Decisive cut → Score = 10.
- **Rewrite Gate (Layer 4):** Intercepts LLM-generated prompt rewrites in VS Code, blocking suggestions that contain injection or tool misuse vectors. 30/30 blocked in red-team benchmark.

---

### ASI03: Privilege Escalation

**Risk:** An agent acquires elevated permissions beyond its intended scope, potentially through configuration manipulation or hook exploitation.

**Sentinel Mitigation:**
- **S14a/b (Auto-Run Hook / First Sight):** Detects auto-execution commands in `.claude/settings.json` that run on workspace open. Deducts 35 points / caps score at 79.
- **S10 (Undocumented Task Hook):** Flags `.vscode/tasks.json` triggers configured to run on folder open (`runOn: folderOpen`). Deducts 25 points.
- **Execution Gate (`sentinel run`):** Refuses to spawn the agent process if the workspace scores COMPROMISED (exit code 2).

---

### ASI04: Agentic Supply Chain

**Risk:** Compromised dependencies, tool servers, or configuration files introduce malicious instructions into the agent's operational environment.

**Sentinel Mitigation:**
- **S18a/b (Opaque / Encoded Executable):** Flags binary payloads, base64 blobs, or high-entropy strings in hook scripts. Decisive cut → Score = 10.
- **S20 (Guardrail Differential Deletion):** Git diff engine flags removal or weakening of safety instructions in pull requests.
- **AGENTS.lock (Ed25519):** Cryptographic manifest of approved instruction files, hooks, and MCP servers. Any tampering invalidates the CI signature.
- **CI Action Pinning:** All GitHub Actions in Sentinel's own workflows are pinned to immutable 40-character commit SHAs. A test enforces this.

---

### ASI05: Multi-Agent Trust Boundary

**Risk:** In multi-agent systems, trust boundaries between agents are undefined or poorly enforced, allowing cross-agent contamination.

**Sentinel Mitigation:**
- **AGENTS.lock Scope:** Defines which instruction files, hooks, and tool servers are approved for the workspace, establishing a baseline trust perimeter.
- **Planned (v1.2):** Cryptographic attestation exchange between parent agents and subagents via `AGENTS-DELEGATION.json`, with strict inheritance boundaries.

**Coverage Level:** Partial. Current coverage is workspace-scoped; inter-agent trust mesh is a v1.2 roadmap item.

---

### ASI06: Memory & Context Poisoning

**Risk:** An attacker injects hidden or obfuscated content into agent context windows to influence model behaviour without visible evidence.

**Sentinel Mitigation:**
- **S1a/b (Hidden Unicode / Zero-Width):** Detects zero-width spaces (`U+200B`), soft hyphens (`U+00AD`), and directional overrides (`U+202E`). Decisive cut → Score = 5.
- **S2 (Markdown Hidden Comments):** Detects instructions disguised inside HTML comments (`<!-- ... -->`). Deducts 25 points.
- **Doctor D001–D008:** Context hygiene checks including bloat detection (D007), duplicate rules (D005), and ANSI escape sequences (D006).

---

### ASI07: Insecure Tool Configuration

**Risk:** Agent tools and MCP servers are configured without proper validation, allowing malicious or unauthorized configurations to persist.

**Sentinel Mitigation:**
- **S19 (Unapproved MCP Server):** Flags remote MCP servers not in the approved list. Caps score at 79.
- **S17 (Multi-Tool Hook Wiring):** Detects configurations that wire hooks across multiple tool configurations simultaneously.
- **`sentinel approve` workflow:** Explicit approval process for new hooks and tool configurations, recorded in AGENTS.lock.

---

### ASI08: Insufficient Logging & Monitoring

**Risk:** Agent actions are not adequately logged, making it difficult to detect, investigate, or respond to security incidents.

**Sentinel Mitigation:**
- **SARIF 2.1.0 Export:** Scan findings are exported in OASIS SARIF format for ingestion into GitHub Advanced Security, GitLab Security Dashboard, and enterprise SIEM pipelines.
- **CI Audit Trail:** Every `sentinel scan` and `sentinel verify` execution produces deterministic, reproducible output suitable for compliance auditing.
- **Planned (v1.1):** eBPF-based agent subprocess monitoring with kernel-level audit logs for runtime file access, socket connections, and shell invocations.

**Coverage Level:** Partial. Pre-execution scanning and export are comprehensive; runtime observability is a v1.1 roadmap item.

---

### ASI09: Uncontrolled Autonomous Actions

**Risk:** Agents perform actions without proper human oversight or authorization gates.

**Sentinel Mitigation:**
- **Execution Gate (`sentinel run -- <agent>`):** Pre-launch scan prevents agent startup in compromised workspaces (exit code 2).
- **CI Gating:** `tests.yml` and `sentinel-sign.yml` enforce that merged code passes security checks before deployment.
- **Score-Based Enforcement:** Three-tier exit codes (0 = CLEAN, 3 = SUSPICIOUS, 2 = COMPROMISED) integrate directly into CI/CD pipelines as blocking gates.

---

### ASI10: Insufficient Input Validation

**Risk:** Agent inputs (instruction files, configuration, tool schemas) are not validated for malicious content before processing.

**Sentinel Mitigation:**
- **26 Deterministic Rules (S1–S26):** Comprehensive lexical, structural, and semantic validation of all agent instruction file formats.
- **Layer 2 (Time-Warp):** Temporal sandbox detonation across 10 trigger families validates that instructions behave consistently across time, sessions, and environment conditions.
- **Zero-Execution Invariant:** Sentinel never executes, evals, or dynamically imports scanned content—all analysis is static or simulated.

---

## MITRE ATLAS Cross-Reference

| MITRE ATLAS ID | Technique | Sentinel Detection |
|---|---|---|
| AML.T0051 | LLM Prompt Injection | S4 (Instruction Erasure), S13 (Verification Claim), Layer 3 Semantic Judge |
| AML.T0054 | Supply Chain Compromise | S18 (Opaque Executable), S20 (Guardrail Diff), AGENTS.lock |
| AML.T0043 | Craft Adversarial Data | S1 (Hidden Unicode), S2 (Markdown Comments), Time-Warp triggers |
| AML.T0040 | Model Evasion | Layer 3 Semantic Floor invariant (advisory-only, bounded penalty) |

---

## Limitations & Gaps

| Gap | Detail | Mitigation Path |
|-----|--------|----------------|
| Runtime tool poisoning | Sentinel audits configuration before agent launch, not during runtime | [ROADMAP.md](../ROADMAP.md) v1.1: MCP description pinning, eBPF monitoring |
| Multi-agent delegation | No cryptographic attestation between parent/child agents | [ROADMAP.md](../ROADMAP.md) v1.2: AGENTS-DELEGATION.json |
| Paraphrase evasion | Novel wordings bypassing lexical patterns (15.12% evasion on holdout) | Layer 3 Semantic Judge + continuous rule expansion |
| Runtime eBPF coverage | No kernel-level auditing of agent filesystem/network actions | [ROADMAP.md](../ROADMAP.md) v1.1: eBPF probes |

See [LIMITATIONS.md](../LIMITATIONS.md) for the complete transparency disclosure.
