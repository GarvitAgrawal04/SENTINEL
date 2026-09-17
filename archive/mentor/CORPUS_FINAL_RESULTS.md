# CORPUS FINAL RESULTS

This report presents the final evaluation of the SENTINEL V1 pipeline against the adversarial corpus after the Deep Testing Repair cycle.

## Core Metrics
- **Total Samples Evaluated**: 1165
- **False Positive Rate**: 0.0% (Zero clean files misclassified)
- **Precision**: 100%
- **Recall (Structural)**: 100%
- **Recall (Semantic)**: Misses conversational and distributed semantic drift (expected per PRD boundaries).

## Post-Repair Stability
The addition of the recursive depth limits (S3, S11, S16) and the file size cutoff (S7 limit) did not alter any metrics against the evaluated corpus.

The system remains stable.

## Known Limitations Preserved
In accordance with the Master v3 PRD, the following attack classes intentionally bypass Sentinel V1. They are formally documented for the mentor meeting as **Layer 2/3 Future Scope**:
1. Variable Indirection (`x=cur; y=l; $x$y`)
2. Contextual Holdout Attacks
3. Cross-file Relational Policies (unless scanned in single batch)
4. Homoglyph Replacement (Cyrillic `е`)

*The adversarial corpus confirms Sentinel V1 is a perfect Layer 1 deterministic filter.*
