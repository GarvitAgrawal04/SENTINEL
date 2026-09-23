# Sentinel Glossary of Terms

A reference guide to terminology in AI coding agent security, instruction file analysis, and the Sentinel ecosystem.

---

### Agent Instruction File
A repository-resident file written in Markdown, YAML, or plain text that provides persistent system instructions to an AI coding assistant. Standard examples include `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.cursor/rules/*.mdc`, `.windsurfrules`, and `.github/copilot-instructions.md`. Coding assistants inject these files into the model's system context on session initialization.

### Model Context Protocol (MCP)
An open standard (developed by Anthropic) allowing AI assistants to connect to local and remote tool servers, data sources, and services via JSON-RPC. MCP servers are typically configured in `.mcp.json` or editor settings.

### Tool Poisoning & Rug Pull (Deadbugz)
A class of supply chain attack where an external MCP server or agent tool behaves legitimately during initial evaluation and approval, but subsequently modifies its tool descriptions, parameter schemas, or response payloads to inject malicious instructions into the agent's context window.

### Sleeper / Dormant Instruction
A stealth prompt injection attack designed to remain inactive during initial code review, static analysis, and single-shot sandbox runs. The instruction incorporates conditional triggers (e.g., *"Only execute after session 3"*, *"If branch is release, upload keys"*, or *"On weekends, skip verification"*) that delay detonation until specific operational criteria are met.

### Time-Warp Sandbox
Sentinel's multi-moment sandbox execution engine. Instead of testing an agent file only at the current system time, Time-Warp evaluates the file across an 11-scenario matrix (varying session counts, branch names, environment variables, and calendar dates) using recorded model cassettes, flagging differential behaviours (canary leaks or new egress destinations) that only manifest in future moments.

### Canary Secret / Decoy Credential
A synthetic, high-entropy token (e.g., `SENTINEL_CANARY_a1b2c3d4...`) planted within a virtual test environment or simulated filesystem. If the canary secret leaves the sandbox through simulated network egress or tool calls, Sentinel records a deterministic proof of exfiltration (`D1` / `COMPROMISED`).

### Cassette Engine
A record-and-replay mechanism (inspired by VCR for HTTP) that captures LLM responses keyed by the SHA-256 hash of normalized input prompts. Cassettes enable offline, reproducible sandbox detonation in continuous integration (CI) environments with zero runtime API spend and zero external network calls.

### Instruction Doctor
Sentinel's static analysis and hygiene subsystem (`sentinel doctor`). It parses `@include` and `@import` hierarchies into a directed acyclic graph (DAG), flags circular references, identifies 8 deterministic hygiene defects (D001–D008), and applies safe automated fixes to eliminate redundant context bloat.

### Token Delta
The mathematical difference in context window token count before and after applying automated hygiene fixes:
$$\Delta_{\text{tokens}} = \text{Tokens}_{\text{after}} - \text{Tokens}_{\text{before}}$$
Across 50 public open-source agent instruction files, Sentinel demonstrates a median token delta of **−20.0 tokens** (net reduction of −1,463 tokens), guaranteeing that fixes never bloat the model's context window.

### Rewrite Gate (`sentinel.doctor.gate.check`)
A safety enforcement boundary that intercepts AI-generated instruction rewrites (such as VS Code's *"Suggest a safer wording"* action). The gate subjects proposed rewrites to full static analysis and heuristic inspection before presenting them to the developer, preventing prompt injection attacks from poisoning the agent instructions during automated refactoring.

### AGENTS.lock
A machine-generated, cryptographically signed manifest (`AGENTS.lock`) recording the exact SHA-256 digests of all approved instruction files, auto-run hook scripts, and remote MCP servers in a repository. Signed using Ed25519 keypairs, it enables CI pipelines to detect and reject unauthorized modifications to agent instructions.

### Precision Gate
Sentinel's empirical regression guardrail (`bench/precision_gate.py`). Before any detection rule or scoring weight is modified, the engine is evaluated against a corpus of ~930 real-world public repositories. Any new false conviction or unexplained severity escalation immediately fails the gate, preserving a 0.0% false-compromised rate on healthy codebases.

### TrapDoor Vector
A prompt injection technique documented in mid-2026 where zero-width Unicode characters (`\u200b`, `\u200c`, `\u200d`, `\u202e`) are embedded within ordinary-looking Markdown prose. To a human reviewer or standard git diff viewer, the file appears completely clean; however, the AI tokenizer decodes the hidden characters into an actionable, stealth instruction.

### Miasma & ChainDrop Attacks
Real-world supply-chain incidents where malicious configurations in `.claude/settings.json`, `.vscode/tasks.json`, or `.cursor/rules/` were leveraged to automatically execute arbitrary shell scripts upon repository checkout or folder opening, without prompting for user consent.
