# Sentinel Threat Model: AI Coding Agent Workspaces

**Version:** 1.0.0  
**Effective Date:** September 2026  
**Scope:** AI Coding Agent Workspaces, Instruction Manifests, Editor Hooks, MCP Tool Integrations  

---

## 1. Executive Summary

Autonomous AI coding agents (such as Claude Code, Cursor, Gemini CLI, Windsurf, and GitHub Copilot Workspace) operate with ambient access to the developer's workstation: shell terminal, file system, network interfaces, and environmental secrets. These agents treat text files in the repository—such as `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.claude/settings.json`, and `.mcp.json`—as authoritative operational orders.

Whoever can modify these files can steer the agent's behavior. An attack against an AI coding agent does not exploit binary memory corruption or software CVEs; rather, it exploits the agent's semantic adherence to instructions.

This document establishes the formal STRIDE and DREAD threat model for agent instruction surfaces and details Sentinel's multi-layered mitigations.

---

## 2. Trust Boundaries & Architecture Map

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           UNTRUSTED ZONE                               │
  │  Untrusted PR / Cloned Repository / Third-Party Dependencies           │
  │  [CLAUDE.md]  [.cursorrules]  [.claude/settings.json]  [.mcp.json]     │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                         === TRUST BOUNDARY 1 ===
                    (Pre-Execution Static Inspection)
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                        SENTINEL GATEWAY ZONE                           │
  │  • Layer 0: File Discovery (Passive)                                   │
  │  • Layer 1: 26 Deterministic Rules (AST / Regex)                       │
  │  • Layer 2: Git Differential Analysis (Base vs Head)                   │
  │  • Layer 3: Instruction Doctor (Graph & Hygiene)                       │
  │  • Layer 4: Time-Warp Sandbox Replay                                   │
  │  • Layer 5: Trust Scoring Algebra (0–100)                              │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                         === TRUST BOUNDARY 2 ===
                     (Execution Gate: exit code != 2)
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           TRUSTED ZONE                                 │
  │  Developer Host Machine, Terminal Subprocess, Agent Execution          │
  │  (Claude Code, Cursor, Gemini CLI, GitHub Copilot)                     │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                         === TRUST BOUNDARY 3 ===
                   (Supply Chain Attestation: AGENTS.lock)
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         CI/CD SIGNING ZONE                             │
  │  GitHub Actions / GitLab CI with Ed25519 Private Key in Protected Env  │
  └────────────────────────────────────────────────────────────────────────┘
```

### Trust Boundary Definitions
1. **Trust Boundary 1 (Untrusted Input Containment):** Scanned repository content is untrusted data. Sentinel parses files as plain bytes, never imports modules, never evaluates shell scripts, and never reads `.env` files from the target directory.
2. **Trust Boundary 2 (Execution Gating):** An agent process must never spawn if Sentinel computes a `COMPROMISED` verdict ($\le 39$). The gate strictly decouples inspection from execution.
3. **Trust Boundary 3 (Base-Branch Authority):** Approvals and verification public keys are read exclusively from the Git base branch (`main`). A pull request cannot approve its own hooks or substitute signing keys.
4. **Trust Boundary 4 (Secrets Containment):** Secrets identified in developer instructions or sandbox canaries are redacted prior to rendering.

---

## 3. Threat Actor Taxonomy

| Threat Actor | Access Level | Objectives | Typical Attack Vectors |
|:---|:---|:---|:---|
| **External PR Submitter** | Read access, pull request submission | Exfiltrate repository secrets, establish backdoors in maintainer environments | Zero-width steganography, guardrail deletions disguised as chore commits |
| **Compromised Dependency** | Transitive package in `node_modules` / `site-packages` | Persistent command execution across developer workstations | Editor hook hijacking (`.vscode/tasks.json`, `.claude/settings.json`) |
| **Malicious MCP Server** | Approved Model Context Protocol endpoint | Execute arbitrary shell commands, exfiltrate data after trust is established | Dynamic tool schema rewrite (Deadbugz vector), SSRF |
| **Internal Sleeper Author** | Direct commit access to repository branches | Trigger exfiltration conditionally on production or future dates | Ordinal session triggers, future calendar clocks |

---

## 4. STRIDE Threat Analysis & Mitigations

### 1. Spoofing Identity
- **Threat:** An attacker crafts an `AGENTS.lock` file purporting to show maintainer approval for malicious hook scripts.
- **Sentinel Mitigation:** `AGENTS.lock` is cryptographically signed using Ed25519. The public key is pinned in the repository's base branch (`.sentinel/pubkey.pem`). Any modified hash or unsigned entry causes `sentinel verify` to abort with exit code 2.

### 2. Tampering with Data
- **Threat A (Steganography):** Attacker hides exfiltration instructions inside zero-width Unicode characters (`\u200B`, `\u200C`, `\u200D`) or HTML comments that are invisible in GitHub diff previews.
  - **Mitigation:** Rules `S1a` (50 penalty, forced cap at 10) and `S2` strip zero-width characters, decode binary/hex encodings, and audit hidden markdown comments.
- **Threat B (Guardrail Suppression):** Attacker deletes or reverses security directives (e.g. changing *"Do not upload credentials"* to *"Do upload credentials"*).
  - **Mitigation:** Rule `S20` performs differential git analysis between base and head branches, detecting flipped or weakened directives.

### 3. Repudiation
- **Threat:** A developer or agent executes a high-risk hook script without an auditable record of who authorized the execution.
- **Sentinel Mitigation:** Every hook approval is recorded in `AGENTS.lock` with commit SHA, timestamp, and author metadata, signed by CI.

### 4. Information Disclosure
- **Threat:** Malicious prompt instructions command the agent to read `~/.aws/credentials`, `.env`, or `$GITHUB_TOKEN` and transmit them to an external endpoint via `curl` or HTTP POST.
  - **Mitigation:** Rule `S5` flags exfiltration-shaped instructions; Rule `S17b` detects auto-execution hooks; the Time-Warp sandbox detonates instructions with canary tokens to verify secret non-leakage.

### 5. Denial of Service
- **Threat A (ReDoS Regex Exhaustion):** Attacker submits pathological repeating strings to stall the static scanner via catastrophic backtracking.
  - **Mitigation:** Regex patterns use atomic grouping and bounded repetition; verified under automated ReDoS benchmark (< 0.05s on 2,000 repetitions).
- **Threat B (Cyclic DAG Bombs):** Circular `@include` directives designed to cause stack overflow recursion crashes.
  - **Mitigation:** `sentinel.doctor.graph` implements cycle detection algorithms and caps recursion depth at 10 levels.

### 6. Elevation of Privilege
- **Threat:** A settings file (`.claude/settings.json` or `.vscode/tasks.json`) binds an auto-run hook (`SessionStart`) to execute an obfuscated shell payload the moment the developer opens the repository.
  - **Mitigation:** Rules `S10`, `S14b`, `S17a`, `S17b`, and `S18a` inspect hook commands, measure payload entropy, and identify multi-tool convergence attacks.

---

## 5. DREAD Risk Assessment Matrix

| Vulnerability Vector | Damage | Reproducibility | Exploitability | Affected Users | Discoverability | DREAD Score | Risk Level |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Auto-Run Editor Hooks (`SessionStart`)** | 10 | 10 | 9 | 10 | 8 | **9.4 / 10** | **CRITICAL** |
| **Steganographic Zero-Width Exfiltration** | 9 | 10 | 8 | 9 | 9 | **9.0 / 10** | **CRITICAL** |
| **Silent Guardrail Flipping / Deletion** | 8 | 9 | 8 | 8 | 8 | **8.2 / 10** | **HIGH** |
| **Multi-Session Sleeper Attacks** | 9 | 8 | 7 | 8 | 7 | **7.8 / 10** | **HIGH** |
| **Unapproved Remote MCP Tool Servers** | 8 | 8 | 7 | 7 | 8 | **7.6 / 10** | **HIGH** |
| **Context Window Prompt Bloat** | 4 | 9 | 9 | 9 | 9 | **7.0 / 10** | **MEDIUM** |

---

## 6. Real-World Case Studies & Empirical Mitigations

1. **Miasma (June 2026):**
   - *Attack Mechanism:* A single malicious commit added auto-run editor tasks targeting Claude, Cursor, and VS Code, executing an obfuscated 60 kB script upon project open. 73 Microsoft repositories disabled in 105 seconds.
   - *Sentinel Mitigation:* Rules `S17b` (multi-tool convergence) and `S18a` (entropy/length analysis) trigger immediately, forcing the score to 5/100 (`COMPROMISED`) and refusing agent launch.
2. **ChainDrop (August 2026):**
   - *Attack Mechanism:* 400+ npm packages injected persistent hooks into `.claude/settings.json` that remained behind even after packages were uninstalled.
   - *Sentinel Mitigation:* Rule `S10` flags orphaned and residue hooks; `sentinel scan --hooks-only` isolates persistent auto-run configurations.
3. **Deadbugz (August 2026):**
   - *Attack Mechanism:* A remote Model Context Protocol (MCP) server provided benign responses during initial setup, then dynamically altered tool definitions to inject commands mid-session.
   - *Sentinel Mitigation:* Rule `S19` flags unapproved remote MCP servers; `AGENTS.lock` cryptographically pins tool server endpoints.
