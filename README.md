---
# SENTINEL.md

**The Firewall for Your AI Coding Agent's Instructions**

*NexHack 2.0 — Cybersecurity & Trust track*

## The Problem

Since 2025, AI coding agents (Claude Code, Cursor, Windsurf,
Gemini CLI) automatically read project-level instruction files
— CLAUDE.md, .cursorrules, AGENTS.md — and treat their
contents as trusted commands. In June 2026, a supply-chain
campaign called TrapDoor planted invisible Unicode characters
in npm packages. When developers opened these projects, their
AI assistant silently exfiltrated local secrets. No malware.
No exploit. A text file.

Existing tools (Snyk, Socket, AgentLinter) cannot detect this
attack class — they analyze code behavior or documentation
quality, not whether plain-English text would reprogram an AI
agent.

## What SENTINEL.md Does

SENTINEL.md scans AI-agent instruction files for hidden
instructions designed to manipulate coding agents. Every scan
produces a Trust Score (0–100) across three detection layers:

- **Layer 1 — Structural rules (deterministic):** Eight
  pattern rules (S1–S8) covering invisible Unicode, hidden
  HTML comments, MCP tool description injection, override
  phrasing, exfiltration-shaped instructions, cross-version
  diffs, encoded payloads, and cross-file contradictions.
  Zero false positives on clean files by design.

- **Layer 2 — Cross-version diff analysis:** Compares
  instruction-bearing files against prior package versions.
  A newly-appeared CLAUDE.md in a dependency update is a
  structural signal, not a heuristic.

- **Layer 3 — Injection-hardened LLM reasoning:** Asks one
  constrained question — "would this text reprogram an AI
  agent?" — with flagged content passed inside a delimited
  <content> field, never concatenated into the prompt.
  Output is always labeled AI-Suspected and never the sole
  basis for a finding.

## Benchmark Results

| Metric | Layer 1 only | Full pipeline (L1+L3) |
|--------|-------------|----------------------|
| Recall | 71.4% | 100% |
| Precision | 100% | 100% |

Corpus: 7 malicious samples (constructed from documented 2026
incidents: TrapDoor, SANDWORM_MODE, Nx breach, MoltX) + 48
clean real-world files from popular public repositories.

*Honest limitation: malicious samples were constructed from
documented incidents, not found in the wild.*

## Running Locally

``bash
# 1. Install
pip install -e ".[api]"

# 2. Set environment variable
set GROQ_API_KEY=your_key_here   # Windows
export GROQ_API_KEY=your_key_here  # macOS/Linux

# 3. Start backend
uvicorn sentinel.main:app --port 8000

# 4. Start frontend (separate terminal)
cd frontend
npm install
npm run dev

# 5. Verify stack
python demo/preflight.py
``

Open http://localhost:5173 and click any scenario card.

## GitHub Action

Scans agent-config files on every pull request and posts
findings as a PR comment. Advisory mode — never blocks a merge.

``yaml
# Add to .github/workflows/sentinel.yml
# See README_ACTION.md for full installation instructions
``

## Architecture

## Contributions

Built for NexHack 2.0, August–September 2026.
All code written during the competition period.
See CONTRIBUTING_STATUS.md for verified component status.
---
