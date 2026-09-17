# SENTINEL V1 GITHUB HANDOFF

Welcome to SENTINEL. If you are picking up this repository, this document is your definitive starting point. 
Do not rely on institutional memory—everything you need is contained within this repository.

## "Where is the project now, and what do I do next?"
**Start Here Sequence:**
1. Read `README.md` (High-level context)
2. Read THIS file (`HANDOFF.md`)
3. Read `docs/ARCHITECTURE_V1.md`
4. Read `docs/TESTING.md`
5. Read `docs/NEXT_STEPS.md`
6. Examine the Code (e.g. `sentinel/pipeline.py` & `sentinel/scanner.py`)

---

## 1. What SENTINEL is
SENTINEL is the firewall for AI coding agents. It performs deterministic, offline, read-only analysis of project files to prevent Prompt Injections, TrapDoor attacks, Malicious Hooks, and Write-Intercepts from subverting the agent's behavior.

## 2. Current V1 Status
**V1 RELEASE FROZEN WITH DOCUMENTED ENGINEERING DEBT**
The scanner architecture is complete, offline-capable, and fully integrated. No further structural modifications are needed for the V1 release.

## 3. What is frozen
- **Layer 0 (Discovery):** Git-based scope boundary validation.
- **Layer 1 (Determinism):** S1–S16 structural rules.
- **Layer 4 (Guide):** Deterministic remediation generation and secret redaction.

## 4. What is actually implemented
- `sentinel.cli` and `sentinel.api` endpoints.
- A subtractive trust formula natively computing penalties.
- Layer 2 vector distances utilizing `BAAI/bge-m3`.
- Layer 3 nearest-neighbor contextual impact generation.

## 5. Architecture Diagram
See `docs/ARCHITECTURE_V1.md`.

## 6. Repository Structure
- `sentinel/` - Core engine.
  - `rules/` - S1–S16 Layer 1 detection rules.
  - `layer2/` - Vector hashing and distance.
  - `layer3/` - Nearest-neighbor execution.
  - `layer4/` - Non-LLM deterministic guidance.
- `docs/` - System architecture and boundaries.
- `tests/` - The comprehensive test suite.
- `release/` - Manifests and runbooks.

## 7. Runtime Data Flow
CLI -> Pipeline Orchestrator -> L1 (ScanResult) -> L2 (DisplacementResult) -> L3 (ClassifierStatus) -> L4 (GuideResult) -> Output.

## 8. Layer-by-layer responsibility
- **L1:** High-precision regex/AST pattern matching.
- **L2:** Measure distance of new code from trusted `sentinel.lock` baselines.
- **L3:** Frame the semantic distance into agent-specific consequences.
- **L4:** Surface mitigations securely without leaking credentials.

## 9. Current Known Limitations
- V1.5 Chatbot is explicitly deferred.
- Layer 2 Semantic Direction is officially `unavailable` (attack_multiplier defaults to `1.0`).
- Layer 3 uses the nearest-neighbor baseline because the domain-adapted classifier is not yet promoted.

## 10. Current Engineering Debt
1. **34 failures** in `tests/layer1/test_rule_metadata.py` (Old API expectations like `check()` instead of `scan()`).
2. **3 failures** in `tests/test_deep_rules.py` (Hardcoded additive math assertions violating new subtractive architecture).

## 11. Canonical Commands
- Scan: `python -m sentinel.cli scan <target>`
- Fast Scan: `python -m sentinel.cli scan --hooks-only <target>`
- Test: `python -m pytest tests/release/`

## 12. Environment Setup
See `docs/SETUP.md`. `SENTINEL_CORPUS_PATH` manages test baseline locations. No API keys are required for V1.

## 13. Model Setup
See `docs/MODEL_RUNTIME.md`. `BAAI/bge-m3` caches locally via `sentence-transformers`.

## 14. Corpus Setup
Point `SENTINEL_CORPUS_PATH` to the `dataset.json` artifact for Layer 3 evaluation.

## 15. Test Strategy
See `docs/TESTING.md`. Do not "fix" the 37 debt failures by rewriting production math.

## 16. Benchmark Procedure
See `release/BENCHMARK_CARD.md`. Goal is strictly 0 False Positives.

## 17. Mentor/Demo Procedure
See `release/DEMO_RUNBOOK.md` and `docs/DEMO_RUNBOOK.md`.

## 18. Security Invariants
See `docs/SECURITY_MODEL_V1.md`. SENTINEL is 100% Read-Only, Offline, and redacts identified credentials (like `sk-proj-...`) from all outputs.

## 19. What MUST NOT be changed
Do not re-introduce LLM execution paths into Layer 1 or Layer 4. Do not drop the FP=0 mandate to inflate TP. Do not fake semantic directions to close Layer 2 debt.

## 20. Next recommended engineering steps
See `docs/NEXT_STEPS.md`.

## 21. Troubleshooting
If the scanner crashes in `sentence-transformers`, verify your Hugging Face cache or execute `--hooks-only`.

## 22. Links
- [Architecture Details](docs/ARCHITECTURE_V1.md)
- [Debt Register](docs/ENGINEERING_DEBT.md)
- [Next Steps](docs/NEXT_STEPS.md)
