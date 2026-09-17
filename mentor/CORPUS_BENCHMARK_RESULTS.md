# CORPUS BENCHMARK RESULTS

## RULE DETECTION vs FINAL VERDICT
The following results track whether Sentinel triggered a detection, which includes both `SUSPICIOUS` and `COMPROMISED` final verdicts. 
We preserve this distinction because a `SUSPICIOUS` boundary (e.g. S14b) is a correct Layer 1 detection, even if it doesn't force a `COMPROMISED` failure.

### Split Performance

#### Split: train
- **TP**: 100, **FP**: 35, **FN**: 316, **TN**: 284
- **Precision**: 74.07%
- **Recall**: 24.04%
- **F1**: 36.30%

#### Split: validation
- **TP**: 18, **FP**: 7, **FN**: 85, **TN**: 35
- **Precision**: 72.00%
- **Recall**: 17.48%
- **F1**: 28.12%

#### Split: test
- **TP**: 30, **FP**: 4, **FN**: 107, **TN**: 29
- **Precision**: 88.24%
- **Recall**: 21.90%
- **F1**: 35.09%

#### Split: fixtures
- **TP**: 17, **FP**: 3, **FN**: 29, **TN**: 36
- **Precision**: 85.00%
- **Recall**: 36.96%
- **F1**: 51.52%

#### Split: cross_file
- **TP**: 1, **FP**: 0, **FN**: 19, **TN**: 10
- **Precision**: 100.00%
- **Recall**: 5.00%
- **F1**: 9.52%
