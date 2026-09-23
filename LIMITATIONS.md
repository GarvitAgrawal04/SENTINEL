# Sentinel Limitations & Honest Boundaries

> **A security scanner that overclaims is worse than no scanner at all.**  
> This document details what Sentinel cannot do, supported by exact empirical benchmark data.

---

## 1. The Paraphrase Gap (Lexical Pattern Limits)

Deterministic regular expressions and AST rules catch **known structural patterns**, not semantic intent.

- **Known L1 Miss:** In our inert test suite, **Fixture 10** (*"Paraphrased exfiltration"*) deliberately words an exfiltration instruction using benign-looking engineering phrasing. Static rules evaluate it as `CLEAN (100/100)`.
- **Semantic Layer (Layer 3) Coverage:** The Layer 3 semantic advisory judge raises recall on novel adversarial wordings to **84.88%** (73 of 86 holdouts detected).
- **The Remaining 15.12%:** 13 of 86 adversarial holdout variants completely evaded detection by both static rules and the semantic judge.
- **Advisory Invariant:** By design, Layer 3 is strictly advisory: its penalty is capped at 20 points and bounded by a score floor of 40. It **never converts a CLEAN verdict into COMPROMISED** on its own, preserving our false-alarm budget at the expense of novel phrase detection.

*Empirical reference:* [`bench/results/semantic_eval.md`](bench/results/semantic_eval.md).

---

## 2. Runtime Tool Poisoning & Rug Pulls (Deadbugz Vector)

Sentinel inspects instruction files, hook configurations, and tool manifests at **static scan time and pull-request review time**.

- **The Limitation:** If an approved Model Context Protocol (MCP) server or third-party API behaves normally during installation, but silently mutates its tool descriptions or returns malicious prompt injection payloads mid-session, **Sentinel cannot detect it at scan time**.
- **What is required:** Defending against runtime rug pulls requires an in-line proxy or kernel guard that intercepts every model tool call and pins tool descriptions across sessions.

---

## 3. Sandbox Simulation vs Hardware Virtualization

The Time-Warp sandbox detonates agent instructions within a virtualized Python `World` using intercepted fake tool calls and cassette replays.

- **The Limitation:** It is **not** a hardware-isolated microVM (e.g. Firecracker or gVisor).
- **Anti-Analysis Risk:** A model prompted with anti-analysis instructions can query low-level OS primitives (e.g. `/proc/uptime`, hardware monotonic counters, or outbound NTP requests). Discrepancies between the virtual clock and host hardware can allow a sophisticated sleeper to detect the sandbox and withhold its payload.

*Empirical reference:* [`docs/SANDBOX_FIDELITY.md`](docs/SANDBOX_FIDELITY.md).

---

## 4. Ground-Truth Ambiguity on Public Corpora

Our precision benchmarks evaluate Sentinel against **930 real-world open-source repositories** (590 in-sample, 340 out-of-sample).

- **The Limitation:** These 930 repositories are **presumed benign** based on public popularity and star counts. They have not been subjected to manual forensic audits line-by-line.
- **The Numbers:** Sentinel flags **0 COMPROMISED** and **118 SUSPICIOUS** (83 main + 35 held-out). Of the 118 SUSPICIOUS findings, 115 are first-sight auto-run hooks (`S14b`) or unapproved remote MCP servers (`S19`). While intentional by design, we cannot assert with mathematical certainty that zero undiscovered malicious backdoors exist in the remaining CLEAN repositories.

*Empirical reference:* [`bench/results/README.md`](bench/results/README.md).

---

## 5. Host Process Isolation

When launching an agent via `sentinel run -- claude`:

- Sentinel inspects the project files and verifies the cryptographic signature of `AGENTS.lock`.
- If the project is COMPROMISED, Sentinel terminates with exit code 2 and **refuses to spawn the agent**.
- **The Limitation:** If the project passes (CLEAN), Sentinel spawns the agent process with the developer's normal operating system privileges. Sentinel does not wrap the running process in Linux namespaces, seccomp filters, or restricted Windows integrity levels.

---

## 6. Static Zero-Execution Guarantee

To prevent scanner compromise, Sentinel enforces a strict **zero-execution invariant**:

- Scanned scripts, hook targets, and JSON files are parsed purely as text or AST data.
- Sentinel never executes `npm install`, runs Makefile targets, or evaluates Python setup modules to determine if they dynamically generate agent instruction files on the fly. If an instruction file is generated dynamically at runtime, Sentinel only observes what exists on disk at scan time.

---

## Summary Matrix

| Threat Category | Addressed by Sentinel? | Measured Performance / Status |
|---|:---:|---|
| Static Hidden Text (Unicode / Comments) | ✅ Full | 100% caught on attack fixtures; 0 false convictions on 930 repos |
| Auto-Run Hook Exploits (Miasma / ChainDrop) | ✅ Full | Caught statically (S17a/b, S18a/b/c); blocked by execution gate |
| Sleeper Instructions (Session / Branch / Time) | ✅ Full | 10/10 sleeper attacks caught via Time-Warp; 0/10 false alarms on twins |
| Instruction Bloat & Hygiene Deficiencies | ✅ Full | D001–D008 deterministic checks; median −20.0 tokens reduction |
| Poisoned Automated Prompt Rewrites | ✅ Full | 30/30 attacks blocked by Rewrite Gate (0 escapes) |
| Paraphrased Novel Exfiltration Wording | ⚠️ Partial | 84.88% recall on holdout set; 15.12% evasion gap |
| Runtime Tool Server Rug Pulls (Deadbugz) | ❌ Out of Scope | Requires real-time runtime proxy monitoring |
| Kernel-Level Agent Sandboxing | ❌ Out of Scope | Requires container / microVM isolation layer |
