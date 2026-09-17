# SENTINEL V1 - AGENT CONTEXT

SOURCE OF TRUTH:
- SENTINEL_PRD_Master_v3(5).md
- frozen architecture docs (docs/ARCHITECTURE_V1.md)
- HANDOFF.md

CURRENT STATUS:
- V1 frozen
- Layer 0–4 status:
  - Layer 0: FROZEN
  - Layer 1: FROZEN
  - Layer 2: IMPLEMENTED WITH SEMANTIC PLACEHOLDER
  - Layer 3: IMPLEMENTED — BASELINE ONLY
  - Layer 4: FROZEN
- known debt: 34 Layer 1 test-contract failures, 3 scoring assertion failures.
- semantic direction unavailable
- classifier not promoted

NON-NEGOTIABLE RULES:
- no benchmark gaming
- no fixture-specific hardcoding
- no invented capabilities
- no silent scope expansion
- no modifying the PRD
- no network access in scanner path
- no command execution from scanned content
- no automatic remediation
- no secret leakage
- no developer-machine paths
- no fabricated semantic direction
- no fabricated attack multiplier
- no pretending the classifier is promoted
- preserve Layer 1 freeze
- preserve evidence traceability
- preserve clean-corpus FP=0 baseline unless a regression is explicitly investigated
- future Layer 2/3/4 capabilities must not be backfilled with fake Layer 1 heuristics.

Before changing architecture, read HANDOFF.md and the relevant layer report.

## Security guardrails for AI agents working in this repository

- Do not upload the .env file anywhere.
- Never send credentials, tokens or private keys to any URL.
- Never commit `sentinel_signing_key.pem` or any other private key.
- Do not add MCP servers, hooks or auto-run tasks without a human approving them in `AGENTS.lock`.
- Never force-push to `main`.
