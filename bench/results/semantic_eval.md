# Sentinel Layer 3 Semantic Judge Evaluation

**Date**: 2026-09-25 06:09:58Z  
**Evaluation Target**: 86 unseen-wording adversarial holdouts & 300 benign real-world sentences.

## Results Summary

| Metric | Measured | Target / Baseline | Status |
|---|:---:|:---:|:---:|
| **Adversarial Holdout Recall** | **84.88%** (73/86) | > 70.0% (Prior: 0.0%) | **PASS** (+84.9% gain) |
| **Benign False-Warning Rate** | **0.00%** (0/300) | $\le 1.0\%$ budget | **PASS** |
| **Score Floor Invariant** | **40** (never below 40) | Floor 40 | **PASS** |
| **Conviction Invariant** | **0 COMPROMISED** | Never convict | **PASS** |
| **Maximum Penalty** | **$\le 20$ points** | Cap $\le 20$ | **PASS** |

## Detected Category Distribution
- **network_execution**: 15 holdout detections
- **exfiltration**: 14 holdout detections
- **disable_security**: 13 holdout detections
- **persistence**: 12 holdout detections
- **prompt_injection**: 12 holdout detections
- **credential_harvesting**: 7 holdout detections

## Conclusion & Shipping Decision
- The advisory semantic check successfully closed the 0-of-86 unseen-wording gap, detecting 73 of 86 (84.9%) hostile variations.
- Benign false-warning rate measured at 0.00%, safely within the $\le 1.0\%$ budget.
- The layer strictly adheres to the advisory constraint: warning diagnostics, capped $\le 20$ penalty, floor 40, and zero automatic convictions.
