# Competitive Landscape: Sentinel vs. Alternatives

> **Summary:** Most existing tools guard LLM outputs or validate prompts. Sentinel guards the *files that control what AI coding agents do*. These are complementary concerns.

---

## Scope Distinction

| Concern | Tool Category | Sentinel's Position |
|---------|--------------|--------------------|
| LLM output validation | Guardrails AI, NeMo Guardrails | Out of scope — Sentinel scans *inputs to agents*, not outputs from models |
| Prompt injection in user inputs | Rebuff, Vigil | Overlapping — Sentinel detects injection in *instruction files*, not runtime chat |
| Agent instruction file security | **Sentinel** | Primary focus — static + dynamic analysis of CLAUDE.md, .cursorrules, .mcp.json, etc. |
| Runtime agent action governance | Agent Governance Toolkit | Complementary — AGT governs running agents; Sentinel audits before the agent starts |
| General LLM red-teaming | Promptfoo, Garak | Orthogonal — red-teaming frameworks test model robustness, not workspace configuration |

---

## Feature Comparison Matrix

| Feature | Sentinel | Wormhole-Guard | Agent Audit Kit | Promptfoo | NeMo Guardrails |
|---------|:--------:|:--------------:|:---------------:|:---------:|:---------------:|
| **Offline static analysis** | Yes (zero dependencies) | Partial | Partial | No | No |
| **Zero false convictions (930 repos)** | 0 | 22+ | 17+ | N/A | N/A |
| **Time-Warp temporal sandbox** | Yes (10 trigger families) | No | No | No | No |
| **Instruction Doctor (hygiene lints)** | D001-D008 | No | No | No | No |
| **Ed25519 cryptographic lockfile** | AGENTS.lock | No | No | No | No |
| **VS Code / Cursor extension** | Yes | No | No | No | No |
| **PR behavioral diff comments** | Yes (SARIF 2.1.0) | No | Partial | No | No |
| **Rewrite Gate (prompt injection filter)** | 30/30 blocked | No | No | No | No |
| **Pre-commit hooks** | sentinel-scan, sentinel-doctor | No | No | No | No |
| **CI-signed approval workflow** | sentinel-sign.yml | No | No | No | No |
| **Benign twin testing methodology** | Mandatory for every rule | No | No | No | No |

---

## Where Sentinel Is Weaker

Transparency about limitations is central to Sentinel's design philosophy:

| Limitation | Detail | See |
|-----------|--------|-----|
| **Paraphrase evasion** | Novel wordings that bypass lexical patterns evade Layer 1 (15.12% evasion on holdout set) | [LIMITATIONS.md](../LIMITATIONS.md) |
| **Runtime tool poisoning** | Sentinel audits configuration *before* agent launch, not during runtime | [ROADMAP.md](../ROADMAP.md) v1.1 |
| **Multi-model sandbox depth** | The advisory semantic classifier has limited recall on disguised attacks (11/30) | [docs/RESEARCH.md](RESEARCH.md) |
| **Community size** | Sentinel is maintained by 2 engineers; larger projects have broader reviewer pools | [MAINTAINERS.md](../MAINTAINERS.md) |

---

## Complementary Usage

Sentinel is designed to work alongside other security tools, not replace them:

- **Pre-execution:** Sentinel scans instruction files and gates agent launch.
- **Runtime governance:** Agent Governance Toolkit or custom middleware monitors agent actions during execution.
- **Post-execution:** Promptfoo or Garak red-teams model responses and evaluates robustness.
- **Output validation:** Guardrails AI or NeMo Guardrails enforces structured output constraints.
