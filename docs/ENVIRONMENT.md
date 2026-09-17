# ENVIRONMENT VARIABLES

SENTINEL V1 relies on the following environment variables.

| Name | Purpose | Required/Optional | Default | Security Sensitivity | Documented |
|------|---------|-------------------|---------|----------------------|------------|
| `SENTINEL_CORPUS_PATH` | Specifies the absolute or relative path to the baseline dataset (`dataset.json`) for Layer 3 exemplar matching. | Optional | `../sentinel-test-corpus/metadata/dataset.json` (Relative to repo root) | LOW | YES |
| `GROQ_API_KEY` | Legacy integration variable for LLM model inference. Disabled/Removed in V1. | Optional | `None` | HIGH | YES (Deprecated) |
| `GITHUB_TOKEN` | Test suite variable to fetch public repositories during evaluation. Not used in `sentinel scan`. | Optional | `None` | HIGH | YES |

> **Note**: SENTINEL V1 is designed to operate securely offline without dependency on cloud API keys. No undocumented environment variables silently alter security interpretation.
