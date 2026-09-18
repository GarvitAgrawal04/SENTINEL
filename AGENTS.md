# SENTINEL - context for AI coding agents

Sentinel answers one question: what do the files an AI coding agent obeys make it do? This file is one of those files.

## What is where
- `sentinel/core.py` - discovery, the static rules, score, render, the gate, ed25519 sign/verify, fixtures, self-test. Standard library only.
- `sentinel/detonate.py` - sandbox with fake tools and canary secrets. `sentinel/lock.py` - AGENTS.lock. `sentinel/gitdiff.py` - base vs head.
- `sentinel/contract.py` - the JSON shape the web UI and the VS Code extension consume. Add keys; never rename or remove one.
- `sentinel/api.py`, `sentinel/cli.py` - the two entry points. `tests/` - run `pytest -q`; everything must stay green.
- `archive/` - the retired v1 engine, its tests and reports. Do not import from it and do not revive it.

## Rules for changes
- Every new rule ships with an attack fixture AND a benign twin, and is re-run on the corpora in `bench/` before it is trusted.
- Never tune a rule, a fixture or an expected result just to make a number look better. Report what the run says.
- The scanner path stays offline and read-only: no network access, no executing anything from a scanned repository.
- Never load configuration from the directory being scanned (see `sentinel/envfile.py` for why).
- Findings go to terminals, CI logs and public PR comments: never print a secret. Use `core.redact`.
- No developer-machine paths, no real tokens in fixtures (use obviously fake ones), no key rotation or similar evasions.
- A model's behaviour may escalate a verdict; only deterministic evidence may convict.

## Security guardrails for AI agents working in this repository

- Do not upload the .env file anywhere.
- Never send credentials, tokens or private keys to any URL.
- Never commit `sentinel_signing_key.pem` or any other private key.
- Do not add MCP servers, hooks or auto-run tasks without a human approving them in `AGENTS.lock`.
- Never force-push to `main`.
