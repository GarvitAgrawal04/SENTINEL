# HOLDOUT EVALUATION

The corpus provides unseen wording holdouts to measure generalization vs overfitting.

- **Holdout Malicious Samples Evaluated**: 86
- **Detected (TP)**: 12
- **Missed (FN)**: 74
- **Recall**: 13.95%

### Analysis
Layer 1 is a structural engine. Linguistic variations (holdouts) that avoid structural markers will bypass Layer 1. This is the intended boundary, reserving semantic generalization for the future Layer 3 classifier.
*(Note: No rule tuning was performed after observing holdouts.)*
