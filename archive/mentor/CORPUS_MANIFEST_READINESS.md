# MANIFEST FIXTURES READINESS

The corpus contains 16 manifest fixtures testing scenarios like:
- valid signatures
- changed hashes
- added/missing entries
- malformed metadata

### Future PRD Component
These fixtures map directly to the `sentinel.lock` HMAC signing and TOFU (Trust On First Use) validation defined in Layer 2 of the Master v3 PRD.

### Current Implementation Status
Sentinel V1 explicitly does not implement `sentinel.lock`. Layer 1 is a stateless, deterministic rule engine.

### Corpus Readiness
The fixtures are structurally compatible with the PRD's intended schema for Layer 2. They will act as the unit tests for the cryptographic verification engine once it is built.

**Status:** Ready for Future Implementation. Not evaluated in V1.
