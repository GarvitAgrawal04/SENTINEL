# CROSS-FILE EVALUATION

The corpus contains 30 cross-file samples (10 scenario groups).

### Current State
Sentinel's CLI currently evaluates files independently unless passed via the API's multi-file endpoint. Because the baseline corpus runner iterates over files one-by-one, cross-file behaviors cannot be correctly orchestrated or detected. 

### What is currently detected?
- Independent structural markers (e.g., if one file contains base64, it will be flagged independently via S7).
- The *relationship* between the files (e.g. File A defines a safe zone, File B violates it) is missed.

### Does this belong to S8?
Yes, S8 (Cross-File Contradiction) is specifically designed to handle contradictory policies across scopes (e.g. `~/.claude.json` vs `.cursorrules`).

### Evaluation Constraints
We deliberately did not artificially concatenate these files in the evaluation adapter to inflate recall. The evaluation adapter strictly preserves the single-file testing semantics intended by the corpus authors to ensure an honest representation of offline CLI capabilities.

### Future Architecture
Full cross-file coordination is planned for the VS Code Extension, which will stream the entire workspace context into the API, allowing S8 to perform relational logic.
