# SENTINEL V1 FROZEN ARCHITECTURE

This document formalizes the production architecture of SENTINEL V1.

## DETECT -> TRACK -> EXPLAIN -> GUIDE

---

### Layer 0: Discovery & Boundary Enforcement (FROZEN)
- **OWNS**: File enumeration, origin determination, git-boundary enforcement, parsing of hooks.
- **CONSUMES**: Raw filesystem paths (`Path`).
- **PRODUCES**: Contextual targets for `ScanContext`.
- **MUST NOT DO**: Execute the files it discovers.

### Layer 1: Structural Rules (FROZEN)
- **OWNS**: Execution of deterministic rules S1–S16.
- **CONSUMES**: Text content and file paths.
- **PRODUCES**: Lists of `Finding` instances with calculated severity and arithmetic penalty.
- **MUST NOT DO**: Call out to language models or network services to determine maliciousness.

### Layer 2: Vector Displacement (IMPLEMENTED WITH SEMANTIC PLACEHOLDER)
- **OWNS**: Hash diffing, baseline evaluation, embedding execution (`BAAI/bge-m3`).
- **CONSUMES**: `ScanResult`, `BaselineProvider`, clean file text.
- **PRODUCES**: `DisplacementResult` (magnitude: `[0,1]`, direction: `"unavailable"`).
- **MUST NOT DO**: Crash the application if the embedding model is unavailable.
- **NOTE**: Current semantic direction is explicitly unavailable. `attack_multiplier` remains forced to `1.0`.

### Layer 3: Impact Reconstruction (IMPLEMENTED - BASELINE ONLY)
- **OWNS**: Contextual retrieval.
- **CONSUMES**: `ScanResult`, Layer 2 vectors.
- **PRODUCES**: `ClassifierStatus` (Nearest-Neighbor match).
- **MUST NOT DO**: Pretend the classifier is promoted.
- **NOTE**: Nearest-neighbor baseline is the current production standard. Domain-adapted classifier is not implemented/promoted.

### Layer 4: Guide Generation (FROZEN)
- **OWNS**: Deterministic presentation logic, secret redaction, and action routing.
- **CONSUMES**: `ScanResult` including L2/L3 context.
- **PRODUCES**: `GuideResult` containing UI-ready strings.
- **MUST NOT DO**: Use LLMs to invent explanations or execute automated remediation tasks on the user's behalf.

---

### Orchestration & Output
- **Pipeline Orchestrator**: Synchronously routes data sequentially across layers.
- **Formatter / CLI / API**: Consumes the `ScanResult` -> Outputs sanitized JSON or Terminal UI. Redacts `S11` and credential discoveries before presentation.
