# NEXT ENGINEER ROADMAP

## IMMEDIATE
**NEXT ENGINEERING PRIORITY:** Resolve/clean legacy test debt only if it can be done without altering frozen production semantics.
- Fix `DEBT-001` in `tests/layer1/test_rule_metadata.py` by aligning tests with the `scan()` interface.
- Fix `DEBT-002` in `tests/test_deep_rules.py` by updating the hardcoded `assert score == X` statements to reflect subtractive V1 normalization.

## NEXT
Validate whether trusted semantic centroid/reference artifacts can be introduced for Layer 2 without fabricating labels.
- Calculate average vector representations (centroids) for `clean` and `attack` manifolds using the `dataset.json` corpus.
- Plumb these centroids into `sentinel.layer2.displacement` to unblock Semantic Direction calculation.

## LATER
Evaluate whether a domain-adapted classifier can legitimately beat the nearest-neighbor baseline.
- Train the Layer 3 Classifier using Scikit-Learn (or similar) over the embedding dataset.
- Perform an A/B benchmark. If the F1 score increases without incurring False Positives, promote it over `NearestNeighborBaseline`.

## V1.5
Implement V1.5 conversational capabilities.
- Integrate an LLM loop into Layer 4 (or Layer 5) that can narrate the attack trajectory using retrieved exemplar context.
- Introduce interactive remediation approval workflows.

## OPTIONAL RESEARCH
- Network vulnerability correlation (enriching S5/S11 detections with offline passive DNS or intelligence feeds).
