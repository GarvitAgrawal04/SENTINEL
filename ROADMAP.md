# Project Sentinel Technical Roadmap

**Version:** 1.0.0  
**Last Updated:** September 2026  
**Status:** Active  

This roadmap outlines the past achievements, current capabilities, and future engineering milestones for Project Sentinel.

---

## Roadmap Overview

```
 2026 Q3 (Shipped)               2026 Q4                         2027 Q1                         2027 Q2+
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│ v1.0.0: GA Core           │   │ v1.1.0: Runtime Guard     │   │ v1.2.0: Keyless & Swarms  │   │ v2.0.0: Agent Hypervisor  │
│ • Deterministic 26 rules  │──▶│ • eBPF session intercept  │──▶│ • Sigstore keyless cosign │──▶│ • MicroVM container jail  │
│ • Time-Warp sandbox replay│   │ • MCP description pinning │   │ • Cross-agent swarm trust │   │ • Network deterministic   │
│ • Instruction Doctor & L0 │   │ • Real-time rug-pull abort│   │ • Multi-model detonation  │   │ • Fine-grained seccomp/ebpf│
│ • Ed25519 AGENTS.lock     │   │ • Kernel-level audit logs │   │ • SLSA Level 3 provenance │   │ • Zero-trust mesh         │
└───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

## 1. Shipped: Version 1.0.0 (General Availability)

The v1.0.0 release establishes the production foundation for pre-execution AI coding agent defense:

- [x] **Deterministic Static Engine (Layer 0 & Layer 1):**
  - Offline discovery across `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.claude/settings.json`, `.mcp.json`.
  - 26 specialized rules (S1–S26) evaluating steganography, invisible characters, prompt overrides, credential exfiltration, and auto-exec hooks.
  - Zero false convictions (0/930) on real-world public open-source repositories.
- [x] **Time-Warp Multi-Session Sandbox (Layer 2):**
  - Extraction of 10 temporal and conditional trigger families (ordinal sessions, future clocks, release tags, CI environments).
  - Virtual world simulation across clock, session, and branch states.
  - Key-free cassette recording and deterministic replay in CI.
  - 100% detection rate (10/10) on dormant sleeper attacks (+100% advantage over single-moment sandboxes).
- [x] **Instruction Doctor & Load Graph (Layer 4):**
  - AST-driven `@import` and `@include` hierarchy resolution with cycle detection.
  - 8 deterministic hygiene checks (D001–D008) pruning dead includes, duplicate rules, and ANSI escape sequences.
  - Median context token reduction of −20 tokens across 50 real-world repositories (net −1,463 tokens pruned).
  - Gated Safe Rewrite action in VS Code protected by an offline security gate (30/30 blocked in red-team benchmark).
- [x] **Cryptographic Verification & Supply Chain:**
  - Ed25519 cryptographic signing and verification of `AGENTS.lock`.
  - Base-branch trust boundary enforcement in GitHub Actions.
  - SARIF 2.1.0 export integrated with GitHub Advanced Security (Code Scanning).
  - High-DPI dual-theme VS Code and Cursor extensions published on OpenVSX and Marketplace.

---

## 2. In Progress: Version 1.1.0 (Runtime Defense & Tool Observability)

**Target:** Q4 2026

While v1.0 audits repositories *before* the agent reads them, v1.1 extends protection to the active agent execution session:

- [ ] **Runtime MCP Tool Description Pinning:**
  - Snapshot tool schemas and descriptions returned during initial server handshake.
  - Continuously verify that approved Model Context Protocol servers do not alter schemas or inject hidden instructions mid-session (mitigating the *Deadbugz* dynamic rug-pull vector).
- [ ] **eBPF-Based Agent Subprocess Monitoring:**
  - Lightweight Linux eBPF probe monitoring file access, socket connections, and shell invocations spawned by `claude`, `cursor`, or `gemini`.
  - Instant SIGKILL signal dispatch if an agent process attempts an unapproved network connection or writes outside the workspace root.
- [ ] **Dynamic Environment Redaction Filter:**
  - PTY/terminal proxy wrapping agent sessions to filter outbound streams, stripping developer API keys and tokens before they reach agent context windows.

---

## 3. Planned: Version 1.2.0 (Supply-Chain Attestation & Swarm Governance)

**Target:** Q1 2027

- [ ] **Keyless Sigstore Attestation for `AGENTS.lock`:**
  - Transition from static Ed25519 keypairs to OpenID Connect (OIDC) identity-based signing via Sigstore / Fulcio.
  - Store public verification proofs in the Rekor transparency log, enabling third-party verification without manual public key pinning.
- [ ] **Multi-Agent Swarm Trust Protocols:**
  - Cryptographic attestation exchange between parent agents and subagents (`AGENTS-DELEGATION.json`).
  - Strict inheritance boundaries preventing subagents from executing tools or reading sensitive configuration files not authorized by the parent agent.
- [ ] **Automated Rule Extraction from Public Incidents:**
  - Continuous ingestion pipeline parsing newly reported agent security vulnerabilities (CVEs, security advisories, bug bounty write-ups) into automated benign twins and attack fixtures.

---

## 4. Future Vision: Version 2.0.0 (The Autonomous Agent Hypervisor)

**Target:** Q2 2027+

- [ ] **MicroVM Kernel Isolation:**
  - Optional zero-configuration MicroVM runner (Firecracker / Cloud-Hypervisor) for high-risk untrusted repository execution.
  - Copy-on-write workspace overlay with automatic discard on compromised score detection.
- [ ] **Cross-Framework Standard Specification (`AGENTS.lock` RFC):**
  - Propose `AGENTS.lock` as an open, vendor-neutral standard within the OpenSSF and Linux Foundation AI working groups.
  - Coordinate standardized schema adoption across Anthropic, Cursor, Google, and OpenAI.
