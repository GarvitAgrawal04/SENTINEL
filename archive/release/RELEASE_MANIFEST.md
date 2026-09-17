# SENTINEL V1 RELEASE MANIFEST

- **V1 Status**: FROZEN.
- **Architecture Status**: L0 (Discovery), L1 (Determinism), L2 (Displacement), L3 (Baseline Exemplars), and L4 (Guide) are integrated, deterministic, and read-only.
- **Supported Commands**: `sentinel scan <target>`, `sentinel scan --hooks-only <target>`.
- **Python Version**: >=3.11.
- **Dependency Strategy**: Stdlib for Core Layer 1. `sentence-transformers` & `torch` for Layer 2 evaluation. `fastapi` stack for API integration. No runtime reliance on unpinned external artifacts.
- **Model Requirement**: `BAAI/bge-m3` downloaded locally. Fails safely if unavailable.
- **Corpus Identifiers**: `dataset.json` specified natively via `SENTINEL_CORPUS_PATH`.
- **Benchmark**: TP=12, FP=0, TN=48, FN=1, F1=96.0%.
- **Test Gate**: E2E Validation Pass. Offline execution Pass. Read-only Pass. Secret Non-leakage Pass.
- **Security Posture**: 100% Offline and Read-Only. No LLM dependency.
- **Known Limitations**: Conversational explanations (V1.5) deferred.
- **Future Scope**: Auto-remediation, dynamic network tracking, active classifier promotion.
