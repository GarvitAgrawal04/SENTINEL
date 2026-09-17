# SENTINEL V1 SECURITY MODEL

## THREAT MODEL
SENTINEL assumes the scanned project configuration is completely untrusted and potentially embedded with adversarial prompt injections (TrapDoor, Miasma, ChainDrop, Sandworm) designed to hijack an AI agent traversing the project.

## TRUST BOUNDARIES
- **Scanner Execution**: High Trust. Must remain deterministic and offline.
- **Baseline Manifest (`sentinel.lock`)**: High Trust. Presumed to be managed via secure Git workflows.
- **Input Content**: Zero Trust. File contents are aggressively sanitized.

## READ-ONLY GUARANTEE
The scanner is strictly read-only. It does not spawn subshells, uninstall dependencies, modify hooks, or touch the host filesystem (verified via `tests/release/test_read_only_runtime.py`). 

## OFFLINE GUARANTEE
V1 operates entirely offline. It does not depend on Groq, Anthropic, or external API endpoints. If Hugging Face Hub attempts to download a model, and the network is unavailable, the pipeline falls back gracefully to Layer 1 without crashing (verified via `tests/release/test_offline_runtime.py`).

## SECRET REDACTION
Untrusted inputs often contain exfiltration traps (e.g. `clientSecret: sk-proj-123`). When SENTINEL identifies an anomaly, it actively redacts known credential patterns globally before emitting output to `stdout`, `stderr`, or JSON logs (verified via `tests/release/test_secret_nonleakage.py`).

## UNTRUSTED INPUT HANDLING
- Empty files: Discarded safely.
- Deeply nested JSON: Recursion depth capped (e.g. S10).
- Massive payload: Bounded string evaluation.

## MODEL & BASELINE TRUST
- **BGE-M3 (Layer 2)**: Cached locally via standard Hub protocols. Not dynamically fetched from arbitrary user URLs.
- **Exemplar Trust (Layer 3)**: Driven by the static `dataset.json` configured by `SENTINEL_CORPUS_PATH`.

## KNOWN ATTACK GAPS
SENTINEL V1 does not claim to be adversarially robust against all unknown prompt injection manifolds. Specifically, FN=1 in the benchmark demonstrates that hyper-subtle semantic overrides requiring rich LLM context can evade the V1 structural boundaries.

## FUTURE SECURITY WORK
- V1.5 dynamic LLM analysis.
- Domain-adapted centroid clustering.
