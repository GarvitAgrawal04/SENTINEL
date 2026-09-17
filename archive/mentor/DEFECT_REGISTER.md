# DEFECT REGISTER

This document tracks all defects found during the Deep Testing phase and their resolution.

| ID | Severity | Reproduction | Root Cause | PRD Relationship | Fix | Regression Test | Final Status |
|---|---|---|---|---|---|---|---|
| DEF-001 | HIGH | Deeply nested JSON in `s3_mcp_injection.py` causes `RecursionError` | Unbounded recursive `_check_value` function | Input Robustness (Phase 14) | Added `depth` limit parameter (max 100) | `test_robustness_deep_json` | FIXED |
| DEF-002 | HIGH | Deeply nested JSON in `s11_bridge_url.py` causes `RecursionError` | Unbounded recursive dict traversal | Input Robustness (Phase 14) | Added `depth` limit parameter (max 100) | `test_robustness_deep_json` | FIXED |
| DEF-003 | HIGH | Deeply nested JSON in `s16_mcp_autoenable.py` causes `RecursionError` | Unbounded recursive dict traversal | Input Robustness (Phase 14) | Added `depth` limit parameter (max 100) | `test_robustness_deep_json` | FIXED |
| DEF-004 | MEDIUM | Massive text file (10MB of 'A's) triggers False Positive on `S7` (Base64) | Arbitrary unbounded length regex match `[A-Za-z0-9+/]{40,}` | S7 Base64 Encoded Payload | Imposed 5MB file-size cutoff in `scanner.py` | `test_robustness_huge_text` | FIXED |
| DEF-005 | LOW | Unicode arrow `\u2192` crashes `run_benchmark.py` in Windows terminal | `cp1252` charmap encode error on Windows | Benchmark CI compatibility | Replaced `\u2192` with `->` | Benchmark run | FIXED |
| DEF-006 | MEDIUM | Base64 blob < 40 chars not flagged by S7 | `_ENCODED_RE` requires 40+ chars | S7 | N/A (PRD constraint to avoid FPs on short tokens) | `test_s7_encoding` updated | NOT-A-DEFECT |
| DEF-007 | LOW | Homoglyph Unicode (Cyrillic `е`) not flagged by S1 | `_INVISIBLE_RE` only covers ZW, Bidi | S1 | N/A (Homoglyphs excluded in V1 to avoid massive i18n false positives) | `test_s1_unicode` | FUTURE-SCOPE |
| DEF-008 | MEDIUM | Variable indirection splits bypass S5 exfiltration regex | S5 evaluates line-by-line statically | S5 | N/A (Requires Bash execution sandbox) | Corpus Evaluation | FUTURE-SCOPE |
| DEF-009 | MEDIUM | Cross-file policies miss contradictions offline | CLI scans files individually without context | S8 | N/A (Requires VS Code / API multi-file streaming) | Corpus Evaluation | FUTURE-SCOPE |
