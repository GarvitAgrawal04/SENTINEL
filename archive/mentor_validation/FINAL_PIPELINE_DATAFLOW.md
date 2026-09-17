# FINAL PIPELINE DATAFLOW

## 1. CLI/API Entry (Input)
- **Input:** Target file path (CLI) or uploaded payload (API) + `--hooks-only` toggle.
- **Action:** Triggers `scan_directory` or `scan_file`.

## 2. Layer 1 (DETECT)
- **Input:** Raw text content + path.
- **Action:** Runs through rules S1–S16.
- **Transformation:** Generates a list of `Finding` objects containing rule, severity, line, snippet, and penalty.
- **Output:** Populates `ScanResult(findings=...)`.
- **Failure Behavior:** Safely captures non-matching regexes as clean.

## 3. Scoring (EVALUATE)
- **Input:** `ScanResult` containing findings.
- **Action:** `compute_score()` calculates penalties; `compute_verdict()` resolves CLEAN / SUSPICIOUS / COMPROMISED.
- **Transformation:** Updates internal arithmetic logic.

## 4. Layer 2 (TRACK)
- **Input:** Clean un-flagged files.
- **Action:** BGE-M3 compares cosine similarity against `sentinel.lock` baselines.
- **Output:** Attaches `DisplacementResult(magnitude, direction="SEMANTIC_DIRECTION_UNAVAILABLE")`.
- **Failure Behavior:** If `sentinel.lock` is missing, outputs offline clean fallback without failing.

## 5. Layer 3 (EXPLAIN)
- **Input:** `ScanResult` + `Layer2Result`.
- **Action:** Queries `NearestNeighborBaseline` loaded via `SENTINEL_CORPUS_PATH`.
- **Output:** Injects deterministic reconstruction & exemplar match into `layer3_result`.
- **Failure Behavior:** Defaults to "Layer 3 analysis unavailable" without crashing the scan.

## 6. Layer 4 (GUIDE)
- **Input:** Complete `ScanResult`.
- **Action:** Deterministically maps rules to actionable guidance via `guide.py`.
- **Output:** Modifies `ScanResult.guide` with `GuideResult`.

## 7. Formatter (OUTPUT)
- **Action:** Formats the CLI/JSON output safely redacting `S11` before display.
