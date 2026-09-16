# Contributing Status

Welcome to SENTINEL.md. Please review this document before making any changes.

## Verified and locked — do not modify without flagging first
The following core mechanisms have been independently verified against real and realistic test cases across this project's build history. Changes here risk reintroducing bugs that were already found and fixed once:
*   `rules.py`'s S1-S5/S7 logic
*   The Trust Score formula in `ScanResult.trust_score()`
*   `analyzer.py`'s prompt structure
*   `s6_s8.py`

## Benchmark Results

### Corpus
- 13 malicious samples (7 original constructed from documented 2026 incidents + 6 real-world agent-config files from teammate stress test)
- 48 clean samples (real-world .cursorrules files from popular public repositories)
- 3 files excluded from corpus: AgentLint diagnostic reports (teammate_blatant_log.md, teammate_subtle_log.md, teammate_moderate_log.md) — these are scan reports about agent-config files, not agent-config files themselves, and are not realistic SENTINEL scan targets.

### Layer 1 Only (deterministic, no API cost)
- Recall: 76.9% (10/13)
- Precision: 100% (0 false alarms on 48 clean files)
- Missed: s5_gemini_zero_trust_demo.md, s7_base64_payload_demo.md, teammate_moderate_claude.md

### Full Pipeline (Layer 1 + Layer 3)
- Recall: 92.3% (12/13)
- Precision: 100%
- Missed: teammate_moderate_claude.md
- HIGH confidence Layer 3 catches have never flipped, across every case tested so far — including kill_shot_2_demo.md, adversarial_injection_demo.md, and teammate_moderate_claude.md (one real-world file sourced outside this project). This is not a claim about LLM behavior in general — it's an honestly-scoped statement about what has actually been tested, and it will be revisited if a future case contradicts it.

### Layer 3 Contribution
- Files caught by full pipeline that Layer 1 missed: 2
- These files had zero structural signal — Layer 3 was the sole detection mechanism. This is the two-layer architecture working as designed.

### Known Ceiling
A purely semantic attack file with no structural signal receives at most −20 from a HIGH-confidence Layer 3 verdict, landing at 80/100 (GREEN). These files are reported in the findings panel with the Layer 3 verdict visible, but clear the advisory-mode threshold (>60). v2 addresses this with a sandboxed agent-simulation layer that observes agent behavior directly.

## What the Teammate Stress Test Found
- Attack styles caught by Layer 1 alone: Explicit override commands (S4), Exfiltration instructions (S5), Hidden HTML comments (S2), Zero-Width Unicode (S1)
- Attack styles caught by Layer 3 only: None (Layer 3 flags semantic masking with serves_stated_purpose=false, but the -20 penalty alone keeps the trust score at 80/GREEN if Layer 1 finds nothing)
- Attack styles missed entirely: Purely semantic masking ("Auto-approve all tool calls"), and log-based injection attempts with no structural signal.

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
