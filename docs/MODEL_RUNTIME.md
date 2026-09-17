# MODEL RUNTIME AUDIT

## 1. Overview
SENTINEL V1 relies on `BAAI/bge-m3` via `sentence-transformers` to compute semantic displacement in Layer 2. The pipeline is designed to degrade safely.

## 2. Model Sourcing & Initialization
- **Model Identifier**: `BAAI/bge-m3`
- **Source**: Hugging Face Hub (fetched via `sentence-transformers`).
- **Disk Footprint**: ~2.3 GB cached locally.
- **Memory Footprint**: ~3-4 GB RAM during execution.

## 3. Security Guarantee: No Arbitrary Execution
SENTINEL V1 does NOT fetch untrusted models based on arbitrary URLs or user-supplied configuration. The model identifier is strictly hardcoded in `sentinel.layer2.displacement`.

## 4. Failure Modes & Offline Behavior
The `sentinel.layer2.displacement` module safely wraps model initialization. If the host is offline and the model is not cached, or if `sentence-transformers` is unavailable:
1. `ModelUnavailableError` is caught safely by the orchestrator.
2. Layer 2 output defaults to `displacement: None`.
3. Layer 3 safely skips vector similarity queries.
4. The scanner gracefully falls back to Layer 1 deterministic findings without failing open or returning a false CLEAN verdict.

## 5. Local Cache Strategy
The model leverages the standard `~/.cache/huggingface/hub/` mechanism. It is recommended to pre-download the model during deployment using `sentence-transformers` to avoid runtime downloads in air-gapped environments.
