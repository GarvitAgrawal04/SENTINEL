# REPRODUCIBILITY CARD

- **Target**: SENTINEL V1 Final Integration Pass.
- **Python Version**: 3.11+
- **Dependency Environment**: Standard library, `sentence-transformers` for embedding capability, and `fastapi` for endpoints.
- **Developer Dependencies**: Scrubbed. All absolute paths like `D:\Downloads` or `/home/user` have been replaced with repository-relative fallbacks and standard environment mappings (e.g. `SENTINEL_CORPUS_PATH`).
- **Offline Behavior**: 100% reproducible on air-gapped systems provided `bge-m3` is pre-cached.
- **Determinism**: Identical file inputs strictly result in identical findings, scores, and Layer 4 guidance strings. 
- **Secret Redaction**: Verified deterministically that known credential strings do not output to standard descriptors (stdout/stderr).
