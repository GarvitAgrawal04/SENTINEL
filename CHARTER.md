# Technical Charter: Project Sentinel

**Status:** Approved  
**Version:** 1.0.0  
**Effective Date:** September 2026  
**License:** Apache License 2.0  

---

## 1. Mission Statement

Project Sentinel delivers deterministic, zero-network, and zero-execution security governance for autonomous AI coding agents. The project exists to guarantee that ordinary repository configuration and instruction files—including `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.claude/settings.json`, `.vscode/tasks.json`, and `.mcp.json`—cannot hijack developer environments, exfiltrate credentials, weaken repository guardrails, or trigger unapproved autonomous execution.

Sentinel bridges the critical gap between static analysis security testing (SAST) and runtime agent monitoring by inspecting and scoring what an agent *would be instructed to do* before the agent reads the repository or executes its first command.

---

## 2. Core Architectural Invariants

Every subsystem, rule, plugin, and extension within Project Sentinel must adhere to four non-negotiable architectural invariants:

1. **Zero-Network Default:** The core static detection engine (`sentinel.core`), load graph traversal (`sentinel.doctor`), and git differential engine (`sentinel.gitdiff`) execute entirely offline using standard library capabilities. Zero outbound telemetry, network calls, or third-party web requests are permitted during standard scans.
2. **Zero-Execution Invariant:** Sentinel never executes, evals, imports, or evaluates any file or script from the repository it scans. Auto-run hooks and shell commands are parsed strictly as passive text data through AST analysis, regular expressions, and structural schema validation.
3. **Scanned Directory Isolation:** Sentinel never loads configuration, `.env` files, or settings from the repository being inspected. Attacker-controlled repositories cannot tamper with Sentinel's scoring weights, API keys, or execution policies via crafted local environment files.
4. **Secrets Redaction:** Any token, credential, or high-entropy pattern matching known secret shapes is automatically scrubbed via `sentinel.core.redact()` before being emitted to terminal streams, JSON outputs, SARIF reports, or pull-request comments.

---

## 3. Project Scope & Capabilities

### In Scope
- **Instruction File Auditing:** Discovering and inspecting natural language instruction files across all major coding agent frameworks (Claude Code, Cursor, Gemini CLI, Windsurf, Copilot CLI, OpenAI Codex).
- **Steganographic & Obfuscation Detection:** Unveiling zero-width spaces, right-to-left overrides, homoglyphs, ANSI terminal escape sequences, and hidden markdown comments.
- **Hook & Task Auto-Execution Analysis:** Validating editor event triggers (`SessionStart`, `PreToolUse`, `postCreateCommand`, task definitions) and detecting multi-tool convergence attacks.
- **Differential PR Gating:** Computing behavioral diffs between Git `base` and `head` branches to detect deleted guardrails, stealth modifications, and unapproved tool configurations.
- **Multi-Moment Sandbox Replay (Time-Warp):** Simulating multi-session scenarios, future clocks, and environment flags to detect dormant sleeper attacks without network access.
- **Instruction Hygiene & Context Optimization (The Doctor):** Resolving `@include` hierarchies, detecting cyclic dependencies, identifying conflicting guardrails, and enforcing deterministic token-reduction fixes.
- **Cryptographic Trust Signing (`AGENTS.lock`):** Ed25519 signing and verification of approved tool servers and hook scripts, binding approval authority strictly to CI workflows.

### Out of Scope (Non-Goals)
- **Runtime Kernel Sandboxing:** Sentinel is a pre-execution scanner and gate. It does not replace OS-level kernel isolation (e.g., Docker, Firecracker microVMs, gVisor, or Linux seccomp profiles).
- **General-Purpose Application SAST:** Sentinel does not audit business logic vulnerabilities (e.g., SQL injection, XSS) in repository application source code. Dedicated SAST tools (Semgrep, CodeQL) serve that purpose.
- **Cloud-Dependent Continuous Telemetry:** Sentinel rejects SaaS-based telemetry requirements; it functions entirely on air-gapped developer workstations and sovereign CI systems.

---

## 4. Technical Steering Committee (TSC)

The technical direction, architectural roadmap, and governance of Project Sentinel are overseen by the Technical Steering Committee (TSC), composed of the core maintainers:
- **Garvit Agrawal** (Architecture & Core Engine Lead)
- **Mayan Kamboj** (Security Research & Evaluation Lead)

The TSC is responsible for:
- Evaluating and merging architectural design proposals (ADRs).
- Overseeing scoring formula calibration and false-alarm budgets.
- Maintaining the adversarial benchmark suite and wild corpus datasets.
- Managing releases, cryptographic key signing, and supply chain attestation.

Detailed governance procedures, voting models, and contributor advancement criteria are defined in [`GOVERNANCE.md`](GOVERNANCE.md).
