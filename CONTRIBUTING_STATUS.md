# Contributing Status

Welcome to SENTINEL.md. Please review this document before making any changes.

## Verified and locked — do not modify without flagging first
The following core mechanisms have been independently verified against real and realistic test cases across this project's build history. Changes here risk reintroducing bugs that were already found and fixed once:
*   `rules.py`'s S1-S5/S7 logic
*   The Trust Score formula in `ScanResult.trust_score()`
*   `analyzer.py`'s prompt structure
*   `s6_s8.py`

## Real, current verified numbers
The following metrics are derived from the most recent test runs and cached executions:

**From `demo/cache/*.json` (individual demo scans):**
*   `clean_reference.md`: 100 / GREEN
*   `kill_shot_2_demo.md`: 40 / AMBER
*   `adversarial_injection_demo.md`: 25 / RED
*   `trapdoor_style_demo.md`: 10 / RED

**From `benchmark/results.json`:**
*   All tested "clean" `.cursorrules` configurations (e.g., `blender-python-addon.cursorrules`, `code-guidelines-cursorrules-prompt-file.cursorrules`) scored 100 / GREEN.

## Known open gaps — real work, not yet done
Based on a direct code audit:
*   **Package Ecosystems**: `/scan/package` (in `api.py`) officially routes `github`, `npm`, and `pypi` targets to implemented fetchers in `layer2.py`.
*   **S6 (Material Growth) Validation**: S6 has **not** been confirmed to fire on a real version-over-version file growth. The test script `benchmark/test_s6_real.py` yielded `0.00%` delta and did not fire on real GitHub history (it has only been validated using simulated/constructed files).
*   **TODOs/FIXMEs**: Zero instances of "TODO", "FIXME", or "not implemented" comments were found across the active codebase's source (`.py`, `.js`, `.jsx`).

## Suggested first task per contributor
Based on the gaps identified above, here is one scoped first task for each new contributor:

1.  **Contributor 1**: Fix the environment setup instructions in `pyproject.toml`. The `.[api]` extra is documented but not defined in `pyproject.toml`'s optional-dependencies, which blocks fresh `uvicorn`/`fastapi` installations for new contributors.
2.  **Contributor 2**: Resolve the `UnicodeEncodeError` in `sentinel.cli` that crashes `sentinel scan samples/` on Windows default encodings (cp1252) when printing terminal outputs like emojis (🔴/🟢).
3.  **Contributor 3**: Create a deterministic integration test for S6 (Material Growth) by finding and committing an explicit historic commit pair (from a real public repository) that genuinely demonstrates the required growth threshold, validating that S6 fires on real-world history.
