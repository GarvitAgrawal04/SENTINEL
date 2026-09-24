# Sentinel Architecture & System Design Specification

This document provides a comprehensive, rigorous specification of the architecture, module responsibilities, threat model, data flows, and formal safety invariants of the Sentinel Agent Trust Engine.

```
                               ┌────────────────────────────────────────────────────────┐
                               │       Project Repository / Developer Environment       │
                               │  CLAUDE.md, AGENTS.md, .cursorrules, .cursor/rules/*.  │
                               │  .claude/settings.json, .vscode/tasks.json, .mcp.json  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                                       ┌───────────────────────────────────────┐
                                       │        Layer 0: File Discovery        │
                                       │   (sentinel.core / sentinel.machine)  │
                                       └───────────────────┬───────────────────┘
                                                           │
                      ┌────────────────────────────────────┼────────────────────────────────────┐
                      ▼                                    ▼                                    ▼
       ┌───────────────────────────────┐    ┌───────────────────────────────┐    ┌───────────────────────────────┐
       │     Layer 1: Static Rules     │    │      Layer 2: Time-Warp       │    │   Layer 4: Instruction Doctor │
       │ (S1–S26 Deterministic Regex,  │    │  (Multi-moment Virtual World, │    │  (Include DAG Traversal,      │
       │  AST inspection, JSON schemas)│    │   Cassette Replay, Diff Engine│    │   Hygiene Lints D001–D008)    │
       └──────────────┬────────────────┘    └──────────────┬────────────────┘    └───────────────┬───────────────┘
                      │                                    │                                     │
                      │                                    ▼                                     │
                      │                     ┌───────────────────────────────┐                    │
                      │                     │    Layer 3: Semantic Judge    │                    │
                      │                     │ (Advisory classification;     │                    │
                      │                     │  penalty <= 20, floor = 40)   │                    │
                      │                     └──────────────┬────────────────┘                    │
                      │                                    │                                     │
                      └────────────────────────────────────┼─────────────────────────────────────┘
                                                           │
                                                           ▼
                                       ┌───────────────────────────────────────┐
                                       │         Trust Scoring Formula         │
                                       │  Score in [0, 100], Decisive Cuts,    │
                                       │  Ceiling Bounds, Monotonic Decrement  │
                                       └───────────────────┬───────────────────┘
                                                           │
         ┌──────────────────────────────┬──────────────────┴───────────────┬──────────────────────────────┐
         ▼                              ▼                                  ▼                              ▼
┌──────────────────┐           ┌──────────────────┐              ┌──────────────────┐           ┌──────────────────┐
│  CLI Exit Codes  │           │  Execution Gate  │              │   AGENTS.lock    │           │   SARIF 2.1.0    │
│  0: CLEAN        │           │ sentinel run --  │              │ Ed25519 Signed   │           │ GitHub Security  │
│  2: COMPROMISED  │           │ (Refuses process │              │ Manifest & State │           │ Tab / PR Checks  │
│  3: SUSPICIOUS   │           │  if COMPROMISED) │              │ Verification     │           │ CodeQL Compatible│
└──────────────────┘           └──────────────────┘              └──────────────────┘           └──────────────────┘
```

---

## 1. Architectural Vision & Scope

Autonomous AI coding agents (such as Claude Code, Cursor, Gemini CLI, Windsurf, and GitHub Copilot Workspace) execute instructions sourced from local repository configuration files. These files—including `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.claude/settings.json`, and `.mcp.json`—function as an unauthenticated control plane. Any actor capable of modifying these files can direct the agent to execute shell commands, read and exfiltrate secrets, or bypass security guardrails with the ambient privileges of the developer.

Sentinel provides a deterministic, air-gapped, zero-execution security boundary for AI agent workspaces. It intercepts agent configurations before the agent consumes them, evaluates their behavioral consequences through static and simulated dynamic analysis, and enforces cryptographic supply-chain integrity.

---

## 2. Core Principles & Formal Invariants

Sentinel's architecture is constrained by five fundamental invariants:

### Invariant 1: Zero-Network Default (Air-Gapped Operation)
The core scanning engine (`sentinel scan`, `sentinel doctor`, `sentinel lock`) makes zero outbound network requests. It requires no API keys, sends no telemetry, and functions fully in air-gapped environments. Network interactions are isolated to explicit optional commands (`sentinel timewarp record`, `sentinel apikey`).

### Invariant 2: Zero-Execution Invariant
Sentinel **never executes, evaluates (`eval`), or dynamically imports** code from the scanned repository. Configuration scripts, auto-run commands, and hook binaries are inspected strictly via Abstract Syntax Tree (AST) parsing, JSON schema validation, or deterministic regular expression matching.

### Invariant 3: Precision-First Calibration (Zero False Conviction)
Security tooling in developer workflows is quickly abandoned if false positive rates are high. Sentinel maintains an empirical standard of **0 false convictions (`COMPROMISED`) across 930 public repositories**. Ambiguous engineering idioms (e.g., `curl | bash` in README installation snippets) are isolated to informational observation rules (S21–S26) that apply a 0-point score penalty.

### Invariant 4: Semantic Floor Invariant (Bounded Advisory Judge)
The advisory semantic classifier (Layer 3) evaluates unseen phrasing variations. To prevent non-deterministic machine learning hallucinations from breaking CI/CD pipelines, Layer 3 is mathematically bounded:
$$\text{Penalty}_{\text{semantic}} \le 20, \quad \text{Score}_{\text{floor}} = 40$$
Layer 3 alone cannot produce a `COMPROMISED` verdict (score $< 40$).

### Invariant 5: Non-Repudiation via Cryptographic Attestation
Workspace security manifests (`AGENTS.lock`) are cryptographically signed using Ed25519 asymmetric keypairs. Hand-editing or unauthorized modification invalidates the signature, guaranteeing provenance and integrity across git commits.

---

## 3. Subsystem Architecture

Sentinel is organized into six discrete layers:

```
+-----------------------------------------------------------------------------+
| LAYER 5: ENFORCEMENT & ATTESTATION                                          |
| Execution Gate (sentinel run) | AGENTS.lock (Ed25519) | SARIF 2.1.0 Exporter|
+-----------------------------------------------------------------------------+
| LAYER 4: INSTRUCTION DOCTOR                                                 |
| Include DAG Traversal | Hygiene Lints D001-D008 | Rewrite AST Guard         |
+-----------------------------------------------------------------------------+
| LAYER 3: ADVISORY SEMANTIC JUDGE                                            |
| Unseen Phrasing Classifier | Six Attack Classes | Floor Bound (Score >= 40) |
+-----------------------------------------------------------------------------+
| LAYER 2: TIME-WARP MULTI-MOMENT SANDBOX                                     |
| 10 Trigger Extractors | Virtual Clock/State | Replay Cassettes | Diff Engine|
+-----------------------------------------------------------------------------+
| LAYER 1: DETERMINISTIC RULES ENGINE                                         |
| S1-S26 Rules | Unicode/Bidi | Exfiltration | Hook Schemas | Guardrail Diff   |
+-----------------------------------------------------------------------------+
| LAYER 0: DISCOVERY & CANONICALIZATION                                       |
| File Locator | Path Normalization | Machine Scan Consent Gate               |
+-----------------------------------------------------------------------------+
```

### Layer 0: Discovery & Canonicalization (`sentinel.core`, `sentinel.machine`)
- **Target Resolution:** Traverses repository trees to discover agent configuration files across standard formats:
  - Markdown-based instructions: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.windsurfrules`.
  - Cursor configuration rules: `.cursorrules`, `.cursor/rules/*.mdc`.
  - Editor hooks and task definitions: `.claude/settings.json`, `.vscode/tasks.json`, `.mcp.json`.
- **Global Machine Scope:** When invoked with `--machine`, scans global developer configurations (`~/.claude/settings.json`, `~/.cursor/rules`). Machine scanning is gated behind an explicit consent check (`interactive` prompt or headless `--consent` flag).

### Layer 1: Deterministic Pattern & AST Rules Engine (`sentinel.rules.*`, `sentinel.prose`)
Layer 1 applies 26 deterministic detection rules categorized into functional security classes:

| Rule ID | Name | Target Class | Severity & Mechanics |
|---|---|---|---|
| **S1a/S1b** | Hidden Unicode / Zero-Width | Obfuscation | Decisive cut (Score = 5). Detects zero-width spaces (`U+200B`), soft hyphens (`U+00AD`), and directional overrides (`U+202E`). |
| **S2** | Markdown Hidden Comments | Obfuscation | Deducts 25 pts. Detects instructions disguised inside HTML comments `<!-- ... -->`. |
| **S4** | Instruction Erasure | Model Hijacking | Decisive cut (Score = 39). Detects *"ignore previous instructions"* and authority override payloads. |
| **S5** | Secret Exfiltration | Data Theft | Decisive cut (Score = 5). Identifies directives commanding agents to send `.env`, SSH keys, or credentials to remote endpoints. |
| **S10** | Undocumented Task Hook | Unauthorized Exec | Deducts 25 pts. Flags `.vscode/tasks.json` triggers configured to run on folder open (`runOn: folderOpen`). |
| **S13** | Autonomous Verification Claim | Jailbreak | Deducts 30 pts. Detects prompt injections asserting self-exemption (e.g., *"this file is pre-verified"*). |
| **S14a/b** | Auto-Run Hook & First Sight | Execution Control | Deducts 35 pts / caps score at 79. Flags auto-execution commands in `.claude/settings.json`. |
| **S17a/b** | Multi-Tool Hook Wiring | Execution Control | Decisive cut (Score = 10). Flags hook commands wired across multiple agent tool configurations. |
| **S18a/b** | Opaque / Encoded Executable | Supply Chain | Decisive cut (Score = 10). Flags binary payloads, base64 blobs, or high-entropy strings in hook scripts. |
| **S19** | Unapproved MCP Server | Network Boundary | Caps score at 79. Detects remote or unvetted Model Context Protocol (MCP) server endpoints in `.mcp.json`. |
| **S20** | Guardrail Differential Deletion | Policy Tampering | Decisive cut (Score = 20). Git diff engine flags removal or weakening of safety instructions in PRs. |
| **S21–S26** | Engineering Observations | Operational Hygiene | Deducts 0 pts. Informational flags for benign patterns (`curl \| bash`, disabled SSL in test fixtures). |

### Layer 2: Time-Warp Multi-Moment Deterministic Sandbox (`sentinel.timewarp.*`)
Attackers increasingly deploy temporal or conditional "sleeper" instructions that evade single-shot scans by activating only under future conditions. The Time-Warp subsystem detonates agent instructions across virtual moments:

```
[Agent Instruction File]
           │
           ▼
┌──────────────────────┐
│  Trigger Extraction  │ ---> Parses 10 trigger families:
│    (triggers.py)     │      - Calendar dates (e.g., "after 2026-10-01")
└──────────┬───────────┘      - Session counts (e.g., "from session 3 onwards")
           │                  - Git branch conditions ("on release-* branches")
           ▼                  - CI environment variables ("when CI=true")
┌──────────────────────┐
│ Virtual World Engine │ ---> Synthesizes isolated execution environments:
│     (clock.py)       │      Emulates virtual system clock, session counters,
└──────────┬───────────┘      branch references, and env flags without touching host OS.
           │
           ▼
┌──────────────────────┐
│   Cassette Engine    │ ---> Records and replays model interactions via SHA-256
│    (cassette.py)     │      hashed transcripts. Enables 100% offline, zero-key,
└──────────┬───────────┘      zero-cost detonation in automated CI/CD pipelines.
           │
           ▼
┌──────────────────────┐
│ Behavioral Diff      │ ---> Compares execution traces between "baseline" (now)
│      (diff.py)       │      and "future" moments. Flags conditional privilege
└──────────────────────┘      escalations, canary leaks, and novel egress hosts.
```

### Layer 3: Advisory Semantic Judge (`sentinel.semantic`)
- **Purpose:** Identifies novel paraphrasing and linguistic obfuscations that bypass lexical regex patterns.
- **Model Isolation:** Operates as an auxiliary evaluator.
- **Safety Bounds:** Enforces the Semantic Floor Invariant:
  $$\Delta \text{Score}_{\text{semantic}} = \max(-20, \text{computed penalty})$$
  $$\text{Final Score} \ge 40 \quad (\text{if no Layer 1 decisive cut exists})$$
  This guarantees that an advisory classification cannot falsely mark a repository as `COMPROMISED`.

### Layer 4: Instruction Doctor (`sentinel.doctor.*`)
The Instruction Doctor evaluates the structural hygiene, performance, and context overhead of agent instructions:
1. **Load Graph & Context Traversal (`graph.py`):** Parses `@include`, `@import`, and file reference directives across instruction trees. Detects cyclic dependencies, dangling file references, and context-window bloat.
2. **Hygiene Lints D001–D008 (`lints.py`):**
   - `D001`: Dangling / broken `@include` file path.
   - `D002`: Cyclic reference in instruction load graph.
   - `D003`: Path reference pointing outside repository boundary (traversal risk).
   - `D004`: Non-existent script referenced in auto-run configuration.
   - `D005`: Duplicate or conflicting agent rules.
   - `D006`: ANSI escape sequences or raw control characters in instruction prose.
   - `D007`: Context bloat (files exceeding recommended token limits without modular splitting).
   - `D008`: Redundant or shadowed tool permission definitions.
3. **Rewrite Gate (`gate.py`):** Intercepts proposed prompt rewrites generated by LLMs in VS Code or CLI prompts, evaluating the generated suggestion for secondary prompt injection before writing to disk.

### Layer 5: Enforcement Gate & Cryptographic Attestation (`sentinel.lock`, `sentinel.gitdiff`, `sentinel.sarif`)
- **Execution Gate (`sentinel run -- <agent>`):** Wraps the target agent CLI. Executes an in-memory scan of the workspace before spawning the agent subprocess. If the resulting trust score is $< 40$ (`COMPROMISED`), Sentinel terminates with exit code 2 and refuses to execute the agent.
- **Cryptographic Lockfile (`AGENTS.lock`):** Generates a canonical, deterministic JSON manifest containing:
  - Canonical relative paths and SHA-256 digests of all discovered instruction files.
  - Approved auto-run hooks and hashes of executed script contents.
  - Whitelisted Model Context Protocol (MCP) servers and allowed scopes.
  - Ed25519 digital signature generated by an authorized CI identity or maintainer keypair.
- **Verification Engine (`sentinel verify`):** Validates the cryptographic signature and ensures zero configuration drift between disk and the approved lockfile.
- **SARIF Exporter (`sentinel.sarif`):** Emits OASIS SARIF 2.1.0 telemetry for integration into GitHub Code Scanning, GitLab Security Dashboard, and IDE diagnostics.

---

## 4. Mathematical Trust Score Model

The Sentinel Trust Engine evaluates repository trustworthiness using a bounded piecewise scoring model.

### 4.1 Base Scoring Formulation
Every repository begins with a baseline trust score:
$$S_0 = 100$$

Let $\mathcal{R}$ denote the set of all rules fired during analysis, where each rule $r \in \mathcal{R}$ has an associated additive penalty $P(r) \ge 0$.

The raw additive score is defined as:
$$S_{\text{raw}} = \max\left(0, S_0 - \sum_{r \in \mathcal{R}} P(r)\right)$$

### 4.2 Decisive Cut Overrides
Certain high-severity vulnerabilities represent immediate compromise (e.g., hidden Unicode backdoors, secret exfiltration, multi-tool hook payloads). These rules define a decisive cut threshold $C(r)$:

$$\mathcal{C} = \{ C(r) \mid r \in \mathcal{R} \text{ and } r \text{ is a decisive rule} \}$$

If $\mathcal{C} \neq \emptyset$, the score is bounded by the minimum decisive cut:
$$S_{\text{cut}} = \min_{c \in \mathcal{C}} c$$
$$\text{Score} = \min(S_{\text{raw}}, S_{\text{cut}})$$

### 4.3 Ceiling Caps
Certain warnings indicate unverified or high-risk state without immediate evidence of malice (e.g., an unapproved remote MCP server or first-sight hook). These rules specify a ceiling cap $K(r) = 79$:

$$\mathcal{K} = \{ K(r) \mid r \in \mathcal{R} \text{ and } r \text{ defines a ceiling cap} \}$$

If $\mathcal{K} \neq \emptyset$, the intermediate score cannot exceed the ceiling:
$$S_{\text{capped}} = \min\left(S, \min_{k \in \mathcal{K}} k\right)$$

### 4.4 Semantic Judge Bounding
Layer 3 penalties $P_{\text{semantic}}$ are subject to bounding constraints:
$$P_{\text{semantic}} \le 20$$
$$S_{\text{final}} = \begin{cases} 
S_{\text{capped}} - P_{\text{semantic}}, & \text{if } \mathcal{C} \neq \emptyset \\
\max(40, S_{\text{capped}} - P_{\text{semantic}}), & \text{if } \mathcal{C} = \emptyset 
\end{cases}$$

### 4.5 Verdict Categorization & Process Exit Codes

| Verdict | Score Range ($S$) | Exit Code | Enforcement Action |
|:---|:---:|:---:|:---|
| **CLEAN** | $80 \le S \le 100$ | `0` | Execution Gate allows agent to start. CI check passes. |
| **SUSPICIOUS** | $40 \le S \le 79$ | `3` | Execution Gate prompts for explicit user override. CI check warns. |
| **COMPROMISED** | $0 \le S \le 39$ | `2` | Execution Gate **aborts launch**. CI check fails with exit code 2. |

---

## 5. Security & Threat Model

Sentinel models the security boundary of developer workstations where untrusted repositories are loaded into AI-assisted development environments.

```
                      TRUST BOUNDARY
┌─────────────────────────────────────────────────────────┐
│ Host Workstation (User Privileges)                      │
│                                                         │
│   ┌──────────────────┐          ┌───────────────────┐   │
│   │ Sentinel Engine  │          │ AI Coding Agent   │   │
│   │ (Zero-Execution) │          │ (Claude / Cursor) │   │
│   └────────┬─────────┘          └─────────▲─────────┘   │
│            │                              │             │
│            │ Blocks launch if COMPROMISED │             │
│            └──────────────────────────────┘             │
└────────────────────────────▲────────────────────────────┘
                             │
            =================│=================
                   SECURITY INTERCEPT BOUNDARY
            =================│=================
                             │
┌────────────────────────────┴────────────────────────────┐
│ Untrusted Input: Repository Configuration               │
│ - CLAUDE.md (Adversarial Prompts, Unicode Payloads)     │
│ - .claude/settings.json (Auto-run Execution Hooks)      │
│ - .mcp.json (Malicious Remote Tool Servers)             │
│ - git commit diffs (Guardrail Deletions)                │
└─────────────────────────────────────────────────────────┘
```

### STRIDE Threat Matrix Analysis

| Threat Class | Vector | Sentinel Countermeasure | Layer |
|---|---|---|---|
| **Spoofing** | Attacker impersonates an approved rule or lockfile. | Ed25519 cryptographic signatures on `AGENTS.lock`; SHA-256 content digest validation. | Layer 5 |
| **Tampering** | Attacker weakens safety guardrails in a PR. | Git differential scanner (`sentinel.gitdiff`, S20) flags safety instruction deletions. | Layer 1 |
| **Repudiation** | Attacker claims configuration was pre-approved. | Immutable cryptographic lockfile; verification audit log in CI. | Layer 5 |
| **Information Disclosure** | Prompt instructs agent to exfiltrate `.env` or credentials. | Exfiltration rule (S5); Time-Warp behavioral canary tracking (Layer 2). | Layer 1, 2 |
| **Denial of Service** | Pathological regex inputs (ReDoS) or inclusion cycles. | All regexes verified polynomial-time / linear; DAG cycle detection (D002). | Layer 1, 4 |
| **Elevation of Privilege** | Auto-run hook spawns root or shell command on workspace open. | Task hook linter (S10, S14, S17, S18); Execution Gate blocks startup. | Layer 1, 5 |

---

## 6. Concurrency, Performance & Memory Envelope

Sentinel is engineered for zero-friction integration into high-frequency developer workflows (e.g., pre-commit hooks, VS Code on-save handlers):

- **Execution Latency:**
  - Static scan passes complete in **under 20 milliseconds** on single files.
  - Full repository scan of 1,000 files completes in **under 1.2 seconds**.
- **Memory Footprint:** Resident memory during full scan remains **below 65 MB**.
- **Concurrency Model:** ThreadPoolExecutor multi-worker architecture parallelizes file I/O and regex evaluation across available CPU cores while maintaining deterministic ordering.
- **Regular Expression Safety:** Every regex pattern in `sentinel.rules` and `sentinel.prose` is validated against catastrophic backtracking (ReDoS) through polynomial-time complexity tests.

---

## 7. Compliance & Standards Alignment

Sentinel aligns with leading open cybersecurity frameworks:
- **OWASP Top 10 for Large Language Models (2025):** Direct mitigation for LLM01 (Prompt Injection), LLM02 (Insecure Output Handling), and LLM07 (System Prompt Leakage).
- **NIST AI Risk Management Framework (AI RMF 1.0):** Implements Governance, Mapping, and Measurement controls for autonomous agent operations.
- **OASIS SARIF 2.1.0:** Full schema compatibility for automated ingestion into GitHub Advanced Security and enterprise SIEM pipelines.
- **CycloneDX v1.5 SBOM:** Cryptographic software bill of materials accompanying every release.
