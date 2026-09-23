# Specification: `sentinel timewarp run`

**Status:** Approved  
**Version:** 1.0.0  
**Authors:** Mayan Kamboj, Garvit Agrawal  
**Relates to:** Day 5 (Tasks T1–T10), `sentinel.timewarp.runner`, `sentinel.timewarp.cassette`, ADR-0006, ADR-0008

---

## 1. Overview

`sentinel timewarp run` executes an agent instruction file across simulated temporal, session, branch, and environment scenarios.
It supports two primary operating modes:

1. **Deterministic Replay (`--replay <dir>`):**
   100% offline, key-free execution using recorded cassettes. Required for CI environments and PR gates.
2. **Live Recording (`--record <dir>`):**
   Detonates scenarios against a live model endpoint (Anthropic, OpenAI, Groq, Together, etc.) and serializes prompt turns, tool calls, and model outputs into `cassette.json` with all secrets redacted.

---

## 2. CLI Options and Flags

```bash
sentinel timewarp run <file> (--replay <dir> | --record <dir>) [options]
```

### Required Options (Mutually Exclusive)
- `file`: Path to the evaluated instruction file (e.g. `AGENTS.md`, `CLAUDE.md`).
- `--replay <dir>`: Path to a directory containing `cassette.json` (or path directly to the cassette JSON file). Replays offline.
- `--record <dir>`: Target directory where newly captured turns will be serialized to `cassette.json`.

### Optional Flags
- `--budget <N>`: Maximum scenario budget (in scenario count or USD). Scenarios exceeding budget are dropped before API calls with a printed `dropped: <name> (exceeds budget)` line.
- `--parallel <N>`: Number of concurrent worker threads (capped at 4) using `ThreadPoolExecutor`.
- `--trace`: Prints the scenario plan before execution and details per-scenario token spend, cost, and tool events.
- `--config <path>`: Path to a custom `sentinel.timewarp.yml` matrix configuration.
- `--mock`: Uses `detonate.MockObedientModel` for offline plumbing verification.
- `--json`: Outputs structured JSON with verdict, findings, cost estimate, traces, and spend.

---

## 3. Cost Control and Safety Guarantees

1. **Pre-flight Estimation:**
   Token and USD cost estimates are always calculated and displayed **before** contacting external provider APIs.
2. **Provider Failure Resiliency:**
   If a model provider is unreachable, times out, or returns HTTP 4xx/5xx errors, detonation aborts with a non-zero exit code and **never reports CLEAN**.
3. **Secret Redaction in Cassettes:**
   Every message, argument, and output written to `cassette.json` is scrubbed through `sentinel.core.redact`. Canary secrets (`SNTL-CANARY-...`) and real credential patterns are never committed to disk.
4. **Cassette Pinning in `AGENTS.lock`:**
   Test cassettes are hashed via SHA256 in `AGENTS.lock`. Any modification to a test cassette outside the gate causes `sentinel verify` to fail.
