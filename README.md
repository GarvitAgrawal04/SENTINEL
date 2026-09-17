> **v5 engine (branch `v5-engine`, 17 Sept 2026).** Static rules that say what the agent would have done, a detonation chamber, a pre-open gate (`sentinel run -- claude`) and a signed `AGENTS.lock`. Measured on 930 real repositories: 0 false COMPROMISED (the v1 engine: 97). Start with [`REBUILD_NOTES.md`](REBUILD_NOTES.md). Everything below this line describes v1 unless it says otherwise.

# SENTINEL

**V1 RELEASE FROZEN WITH DOCUMENTED ENGINEERING DEBT**

## What it does
SENTINEL is the offline, deterministic security firewall for AI Coding Agents. It intercepts adversarial prompt injections, malicious git hooks, tool shadowing, and unicode obfuscation tactics designed to subvert autonomous engineering agents (like Claude or custom MCP setups). 

## Architecture
SENTINEL runs entirely offline using a sequential pipeline:
1. **Layer 0 (Discovery):** Enforces filesystem and git-based boundary trust.
2. **Layer 1 (Determinism):** Parses files against high-precision structural rules (S1-S16).
3. **Layer 2 (Displacement):** Hashes and computes semantic vector shifts from known `sentinel.lock` baselines.
4. **Layer 3 (Impact):** Evaluates euclidean similarity against a Nearest-Neighbor exemplar baseline.
5. **Layer 4 (Guide):** Formulates deterministic, non-hallucinated mitigation steps and strictly redacts exfiltrated credentials.

## Quick Start
```bash
python -m venv venv
source venv/bin/activate
pip install .

# Setup Layer 2 Local Embeddings
pip install sentence-transformers torch
```

## Run
```bash
# Standard local scan
python -m sentinel.cli scan /path/to/project

# CI/Pre-Commit Extreme Performance Mode
python -m sentinel.cli scan --hooks-only /path/to/project
```

## Test
```bash
# Run the release criteria gate (Tests Read-Only, Offline, Secret Masking)
python -m pytest tests/release/
```

## Benchmark
```bash
python benchmark/run_benchmark.py
# Target: TP=12, FP=0, TN=48, FN=1
```

## Demo
For an end-to-end evaluation of capability:
```bash
python -m sentinel.cli scan samples/trapdoor_style_demo.md
```

## Current Limitations
- SENTINEL V1 does not utilize LLMs and explicitly defers conversational semantic reasoning to V1.5. 
- SENTINEL does not automatically modify or remediate vulnerabilities in your repository.
- Layer 2 Vector intent trajectory is unavailable pending domain-adapted ML centroids.

## Developer Handoff
If you are an engineer taking over SENTINEL V1 development, **START HERE**:
Read [HANDOFF.md](HANDOFF.md) for complete architectural context.

## Documentation Links
- [Handoff Entry Point](HANDOFF.md)
- [Architecture Details](docs/ARCHITECTURE_V1.md)
- [Testing & Release Gates](docs/TESTING.md)
- [Threat Model & Security](docs/SECURITY_MODEL_V1.md)
- [Engineering Debt](docs/ENGINEERING_DEBT.md)
