# CORPUS INTEGRATION REPORT

## 1. Corpus Inventory
- **Total samples**: 1165
- **Label counts**: {'malicious': 594, 'benign': 443, 'suspicious': 125, 'obfuscated': 3}
- **Split counts**: {'train': 735, 'test': 170, 'validation': 145, 'fixtures': 85, 'cross_file': 30}
- **Pattern families**: 177
- **Categories**: 17
- **Subcategories**: N/A
- **Obfuscation classes**: 13
- **Holdout samples**: 86
- **Benign lookalikes**: 143
- **Cross-file groups**: 10
- **Version-drift chains**: 10
- **Manifest fixtures**: 16
- **Unicode fixtures**: 9
- **Candidate rules**: 49

## 2. Quality Gate Results
- **Duplicate checks**: Passed (63 near-duplicates documented, 0 byte-identical)
- **Train/Val/Test isolation**: Passed (No instruction leakage)
- **Holdout isolation**: Passed (Holdout wordings absent from train/validation)
- **Credentials/Personal data**: Passed (None found)
- **Private endpoints**: Passed (None found)
- **Metadata validation**: Passed (1165 ids, 1165 in metadata)

## 3. Findings & Warnings
- Semantic displacement is explicitly NOT validated; the corpus provides raw test data.
- The 49 candidate rules are experimental and do not mandate new Layer 1 development.
- Holdout wording is unseen in the train/validation splits to test generalization.
