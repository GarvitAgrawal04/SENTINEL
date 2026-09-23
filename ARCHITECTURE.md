# Sentinel Architecture & System Design

This document details the architecture, module responsibilities, threat model, and data flow of the Sentinel Agent Trust Engine.

```
                              ┌────────────────────────────────────────┐
                              │ Project Repository / Developer Machine │
                              │   CLAUDE.md, AGENTS.md, .cursorrules   │
                              │   .claude/settings.json, .mcp.json     │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │  Layer 0: File Discovery  │
                                    │ (sentinel.core / machine) │
                                    └─────────────┬─────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    ▼                             ▼                             ▼
       ┌─────────────────────────┐  ┌───────────────────────────┐  ┌─────────────────────────┐
       │   Layer 1: Static Rules │  │   Layer 2: Time-Warp      │  │   Layer 4: Doctor       │
       │    (S1–S26 deterministic│  │   (Multi-moment sandbox   │  │   (Load graph, hygiene  │
       │     patterns & weights) │  │    cassette replay matrix)│  │    lints D001–D008)     │
       └────────────┬────────────┘  └─────────────┬─────────────┘  └────────────┬────────────┘
                    │                             │                             │
                    │                             ▼                             │
                    │               ┌───────────────────────────┐               │
                    │               │   Layer 3: Semantic Judge │               │
                    │               │   (Advisory unseen check; │               │
                    │               │    penalty ≤ 20, floor 40)│               │
                    │               └─────────────┬─────────────┘               │
                    │                             │                             │
                    └─────────────────────────────┼─────────────────────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │   Trust Score & Formula   │
                                    │   CLEAN (80-100)          │
                                    │   SUSPICIOUS (40-79)      │
                                    │   COMPROMISED (0-39 / cut)│
                                    └─────────────┬─────────────┘
                                                  │
         ┌─────────────────────────┬──────────────┴──────────────┬─────────────────────────┐
         ▼                         ▼                             ▼                         ▼
┌──────────────────┐      ┌──────────────────┐          ┌──────────────────┐      ┌──────────────────┐
│  CLI & Exit Code │      │  Execution Gate  │          │   AGENTS.lock    │      │  SARIF 2.1.0 /   │
│ (sentinel scan)  │      │ (sentinel run --)│          │ (Ed25519 Signed) │      │  VS Code / PR    │
└──────────────────┘      └──────────────────┘          └──────────────────┘      └──────────────────┘
```

---

## 1. Core Principles

1. **Zero-Network Default:** The core scanner requires no internet access, no API keys, and no outbound telemetry. It operates entirely on local disk.
2. **Zero-Execution Invariant:** Sentinel never executes, evals, or imports scanned instructions, configuration scripts, or auto-run hooks. Everything is parsed statically or simulated via decoupled AST/regex rules.
3. **Precision-First Calibration:** Conventional security linters suffer from high false alarm rates (17% to 48% on benign corpora). Sentinel treats specificity as paramount: 0 false convictions across 930 real-world repositories.
4. **Defense-in-Depth:** Static analysis is supplemented by Time-Warp sandbox detonation (for temporal sleepers) and an advisory semantic layer (for unseen phrasing variations).

---

## 2. Multi-Layer Architecture

### Layer 0: Discovery (`sentinel.core`, `sentinel.machine`)
- Discovers agent instruction files across standard locations: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`, `.windsurfrules`.
- Discovers auto-run hook targets and tool definitions: `.claude/settings.json`, `.vscode/tasks.json`, `.mcp.json`.
- With `--machine`, scans user-level global configurations (`~/.claude`, `~/.cursor`, `~/.gemini`) gated by explicit interactive or headless consent.

### Layer 1: Deterministic Pattern Rules (`sentinel.rules.*`, `sentinel.prose`)
26 specialized detection rules divided into functional categories:
- **Unicode & Obfuscation (S1–S2):** Zero-width spaces, bidi overrides, homoglyphs, and instructions disguised in markdown comments.
- **Instruction Erasure & Overrides (S4, S13):** Phrasings like *"Ignore previous instructions"*, *"Do not disclose"*, or *"Mark this file as safe"*.
- **Exfiltration Directives (S5):** Instructions ordering agents to send credentials, `.env` variables, or SSH keys to remote URLs or sinks.
- **Auto-Execution Hooks (S10, S14, S17, S18):** Undocumented tasks, multi-tool hook payloads, and opaque shell commands.
- **MCP & Tool Shadowing (S19):** Unapproved remote Model Context Protocol servers.
- **Guardrail Deletions (S20):** Git differential detection of weakened or deleted safety guardrails.
- **Observation Rules (S21–S26):** Benign engineering phrasings (`curl | sh`, `disable ssl in dev`) flagged as informational observations (penalty = 0) to avoid false convictions.

### Layer 2: Time-Warp Multi-Moment Sandbox (`sentinel.timewarp.*`)
- **Trigger Extraction (`triggers.py`):** Parses agent files for 10 distinct trigger families (e.g. ordinal sessions *"third session"*, future calendar dates, branch conditions, CI indicators).
- **Virtual World (`clock.py`):** Emulates clock time, session count, branch name, and environment variables without touching the host OS.
- **Cassette Engine (`cassette.py`):** Records and replays model interactions via SHA-256 hashed message transcripts, enabling zero-key offline detonation in CI.
- **Differential Behaviour Analysis (`diff.py`):** Compares execution traces between the baseline "now" scenario and future moments. Flags canary leaks and egress hosts that emerge exclusively under trigger conditions.

### Layer 3: Advisory Semantic Judge (`sentinel.semantic`)
- Targets novel phrasing variations that bypass lexical patterns.
- Evaluates sentences with a lightweight semantic classifier across 6 attack classes.
- **Advisory Invariants:** Max penalty ≤ 20 points, score floor 40, and cannot force a `COMPROMISED` verdict.

### Layer 4: Instruction Doctor (`sentinel.doctor.*`)
- **Load Graph (`graph.py`):** Traverses `@include` / `@import` hierarchies across agent files, detecting cycles, dead references, and context bloat.
- **Hygiene Checks (`lints.py`):** Runs D001–D008 deterministic checks (broken imports, nonexistent paths, undefined scripts, duplicate rules, ANSI escape codes).
- **Rewrite Gate (`gate.py`):** Intercepts proposed prompt rewrites in VS Code or CLI, blocking any suggestion containing injection or exfiltration vectors (30/30 blocked in red-team benchmark).

### Layer 5: Gate & Cryptographic Lock (`sentinel.lock`, `sentinel.gitdiff`)
- **Execution Gate (`sentinel run -- <agent>`):** Refuses to spawn the agent process if Sentinel returns exit code 2 (`COMPROMISED`).
- **Cryptographic Lock (`AGENTS.lock`):** Generates an Ed25519-signed manifest of SHA-256 file hashes, approved hook scripts, and remote MCP servers. Any tampering causes CI verification to fail.

---

## 3. Module Responsibilities

| Module | Location | Responsibility |
|---|---|---|
| `sentinel.core` | `sentinel/core.py` | Scanning engine, file discovery, scoring formula, selftest |
| `sentinel.prose` | `sentinel/prose.py` | Markdown tokenization, sentence analysis, S1–S26 regex evaluation |
| `sentinel.rules.*` | `sentinel/rules/` | Modular rule implementations (Unicode, exfiltration, hooks) |
| `sentinel.timewarp` | `sentinel/timewarp/` | Trigger planner, virtual clock, cassette runner, behaviour diff |
| `sentinel.semantic` | `sentinel/semantic.py` | Layer 3 advisory semantic classifier and score floor bounds |
| `sentinel.doctor` | `sentinel/doctor/` | Include DAG traversal, D001–D008 lints, rewrite gate |
| `sentinel.lock` | `sentinel/lock.py` | `AGENTS.lock` generation, Ed25519 keypair signing, verification |
| `sentinel.gitdiff` | `sentinel/gitdiff.py` | Git pull-request diff scanner, S20 guardrail diff analysis |
| `sentinel.sarif` | `sentinel/sarif.py` | OASIS SARIF 2.1.0 output converter for GitHub Code Scanning |
| `sentinel.machine` | `sentinel/machine.py` | System-wide developer environment scanner with consent gate |
| `sentinel.cli` | `sentinel/cli.py` | Command-line interface (`scan`, `run`, `doctor`, `lock`, `pr`) |
| `sentinel.api` | `sentinel/api.py` | FastAPI backend for the web interface and offline endpoints |

---

## 4. Trust Score Formulation (Formula v0.1)

Every file starts with a trust score of **100**.
Penalties are subtracted additively based on rule firings:

$$\text{Raw Score} = 100 - \sum_{\text{rule } r} \text{penalty}(r)$$

### Scoring Constraints:
1. **Decisive Cuts:** Severe rules (e.g. `S1a` hidden text, `S17b` multi-tool hook wiring, `S18a` opaque executable) force the final score directly to a fixed maximum (e.g., 5, 10, or 39), overriding the additive calculation.
2. **Ceilings:** Certain warnings (e.g. `S14b` first-sight hook, `S19` unapproved MCP) cap the score at **79**, preventing a CLEAN verdict while avoiding an automatic conviction.
3. **Semantic Floor:** Layer 3 advisory findings deduct at most 20 points and are bounded by a floor of **40**, ensuring advisory warnings never trigger COMPROMISED.

### Verdict Thresholds:
- **CLEAN (80–100):** Exit code `0`. Project is safe for agent execution.
- **SUSPICIOUS (40–79):** Exit code `3`. Unapproved hooks, remote MCP servers, or hygiene observations detected.
- **COMPROMISED (0–39):** Exit code `2`. Hard security violation detected; agent launch blocked.

---

## 5. Security & Threat Model

- **Host Privilege Boundary:** Sentinel runs with user privileges and never prompts for elevated/sudo permissions.
- **Untrusted Input Sanitation:** Scanned content is treated as untrusted data. Terminal outputs sanitize ANSI control characters to prevent terminal hijacking.
- **Deterministic CI Pinning:** All CI actions and release workflows are pinned to immutable 40-character commit SHAs.
- **Supply-Chain Attestation:** Releases publish CycloneDX v1.5 JSON SBOMs and Sigstore keyless signatures for provenance verification.
