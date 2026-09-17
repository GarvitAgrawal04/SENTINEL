# TESTING POLICY

*Refer to `docs/TESTING.md` for complete command matrices.*

SENTINEL operates under strict Release testing criteria.
Testing matrices encompass:
- **`tests/release/`**: Authoritative release gates ensuring offline operation, system mutability boundaries, and credential leak containment.
- **`tests/layer1/`**: Rigorous logic assertions (note: 34 legacy tests remain as documented API mismatch debt).
- **`tests/test_scanner.py`**: Functional integration tests mapping inputs to Verdict boundaries.

**No testing optimizations or assertions were altered to artificially modify the V1 Release metrics.**
