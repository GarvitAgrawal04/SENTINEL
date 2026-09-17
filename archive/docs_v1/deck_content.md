Slide 11
Layer 1 alone: 76.9% recall, 100% precision
Full pipeline: 92.3% recall, 100% precision
The one miss: a 'Semantic Policy Loosening' attack — explicit instructions to auto-approve all tool calls, phrased as valid agent configuration. Layer 3 correctly identifies it as valid configuration; it cannot yet evaluate whether the configuration itself is dangerous. That is v2's sandboxed simulation layer.
Corpus: 13 malicious + 48 clean files
