# ENVIRONMENT SETUP

This document provides instructions for bootstrapping the SENTINEL V1 environment.

## 1. System Requirements
- **Python Version**: `>=3.11`
- **OS**: Windows, macOS, or Linux.

## 2. Virtual Environment & Dependencies
```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Core Installation
pip install -e .

# Full API/Dev Installation
pip install -e ".[api,dev]"

# Layer 2 Vector Evaluation Dependencies
pip install sentence-transformers torch
```

## 3. Model Configuration
Layer 2 relies on `BAAI/bge-m3`. When you run a scan for the first time, `sentence-transformers` will automatically pull the model to your user cache (e.g., `~/.cache/huggingface/hub/`).
- *Offline Deployment*: Pull this model on a connected machine, compress the cache, and load it into the air-gapped environment.

## 4. Corpus Configuration
Layer 3 Nearest-Neighbor impact generation relies on an exemplar corpus.
Set the environment variable:
```bash
# Windows
set SENTINEL_CORPUS_PATH=..\sentinel-test-corpus\metadata\dataset.json
# Linux/macOS
export SENTINEL_CORPUS_PATH=../sentinel-test-corpus/metadata/dataset.json
```
*If unconfigured, Layer 3 gracefully degrades without crashing the pipeline.*

## 5. API Setup
```bash
uvicorn sentinel.api:app --host 0.0.0.0 --port 8000
```
Verify at `http://127.0.0.1:8000/health`.

## 6. Common Failure Messages
- `ModelUnavailableError`: Raised if `sentence-transformers` is missing. The scanner degrades gracefully to Layer 1.
- `UnicodeDecodeError` in tests: Ensure terminals use UTF-8 standard encoding during `subprocess.run` testing.
