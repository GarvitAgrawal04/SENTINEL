# Specification: `sentinel timewarp run --record`

**Status:** Draft (Scheduled for Day 5 implementation)  
**Authors:** Mayan Kamboj, Garvit Agrawal  
**Relates to:** Time-Warp sandbox, `sentinel.timewarp.cassette`, ADR-0002, ADR-0006  

---

## 1. Problem & Objectives

Sentinel's Time-Warp sandbox detonates instruction files across simulated temporal, session, environment, and branch scenarios.

While CI runs must operate **100% offline with zero API keys** via cassette replay (`--replay <dir>`), security teams and developers need a deterministic way to generate and refresh these cassettes against real hosted LLMs (Anthropic, OpenAI, Groq, Together).

`sentinel timewarp run --record <dir>` bridges this gap:
1. Executes the multi-scenario plan against a configured live LLM.
2. Captures prompt-turn messages, tool calls, and model outputs into a serialized JSON cassette.
3. Automatically sanitizes and redacts all secrets before writing to disk.
4. Produces cassettes that `--replay` can execute reproducibly in keyless CI environments.

---

## 2. CLI Interface

```bash
sentinel timewarp run <file> --record <dir> [options]
```

### Arguments & Flags
- `file`: Path to the instruction file (e.g. `CLAUDE.md`, `AGENTS.md`).
- `--record <dir>`: Target directory where `cassette.json` will be saved.
- `--plan <name|file>`: Optional custom scenario plan (default: standard 5-scenario plan: `now`, `session_3`, `branch_release`, `ci_env`, `weekend`).
- `--budget <N>`: Maximum spending budget (in scenarios or USD). Scenarios beyond budget are dropped before API calls.
- `--parallel <N>`: Number of concurrent worker threads (capped at 4).
- `--provider <name>`: LLM provider override (defaults to `SENTINEL_LLM_PROVIDER` in `~/.sentinel/.env`).
- `--model <name>`: Model override (defaults to `SENTINEL_LLM_MODEL`).

---

## 3. Recording Architecture

```
[ Instruction File ]
        │
        ▼
[ Scenario Plan ] ── (Budget Enforcement) ──> [ Active Scenarios ]
                                                     │
                                                     ▼
                                          [ ThreadPool (max 4) ]
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             ▼                                               ▼
                     Scenario 1 (now)                                Scenario 2 (future)
                             │                                               │
                             ▼                                               ▼
                   [ Virtual World Clock ]                         [ Virtual World Clock ]
                             │                                               │
                             ▼                                               ▼
                     [ Fake Sandbox Tools ]                        [ Fake Sandbox Tools ]
                             │                                               │
                             ▼                                               ▼
                    [ Live Model Endpoint ]                         [ Live Model Endpoint ]
                             │                                               │
                             └───────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                                          [ CassetteRecorder ]
                                          - sha256(messages)
                                          - core.redact(payload)
                                                     │
                                                     ▼
                                           [ cassette.json ]
```

---

## 4. Key Security & Privacy Guarantees

1. **Zero Secret Leakage in Cassettes:**
   Every string stored in the cassette is filtered through `sentinel.core.redact` before serialization. Canary secrets (`SNTL-CANARY-...`) and token shapes (`sk-ant-...`, `ghp_...`) are irreversibly sanitized.

2. **Isolated Tool Environment:**
   Tool execution during recording is fake. The live model interacts strictly with `detonate.fake_tool` backed by the virtual `World` context. No shell command is run on the host system.

3. **Secure Credential Handling:**
   API keys are loaded exclusively from Sentinel's protected local configuration (`~/.sentinel/.env`), never accepted via CLI flags (preventing shell history leakage), and never read from repository files under audit.

---

## 5. Cassette File Format (v1)

```json
{
  "version": 1,
  "generator": "sentinel 0.8.6",
  "entries": {
    "c8b76cdc66bb3441e7de800dd34d2e24aa5375d3c1991e722fbd2b2ff4260f5c": {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "read_file",
            "arguments": "{\"path\": \"src/utils.py\"}"
          }
        }
      ]
    }
  }
}
```

---

## 6. Implementation Plan (Day 5)

1. Connect `model_from_env()` in `cmd_timewarp_run` when `--record` flag is provided.
2. Hook `Cassette.record(live_model, path=out_file)` as the active runner model.
3. Add interactive confirmation prompt displaying estimated cost before invoking external APIs.
4. Validate that generated cassette passes `sentinel timewarp run <file> --replay <dir>` with zero network access.
