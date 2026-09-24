# Release Process

This document describes the release engineering process for Sentinel.

## Versioning

Sentinel follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (`x.0.0`): Breaking changes to the scoring formula, CLI interface, or JSON contract.
- **MINOR** (`0.x.0`): New detection rules, features, or integrations.
- **PATCH** (`0.0.x`): Bug fixes, documentation updates, and dependency bumps.

## Pre-Release Checklist

Before cutting any release, verify the following:

```bash
# 1. Full test suite passes
pytest

# 2. Engine self-test passes
sentinel selftest

# 3. Self-scan reports CLEAN
sentinel scan .

# 4. All README links resolve
python docs/check_readme_links.py

# 5. SVG diagrams are current
python docs/build_readme_assets.py
pytest tests/v5/test_readme.py

# 6. CHANGELOG.md is updated
# 7. Version bumped in pyproject.toml and CITATION.cff
```

## Release Workflow

### 1. Version Bump

Update the version string in:
- `pyproject.toml` (`version = "x.y.z"`)
- `CITATION.cff` (`version: x.y.z` and `date-released`)

### 2. Update CHANGELOG.md

Add a new section at the top of `CHANGELOG.md` following the existing format.

### 3. Commit and Tag

```bash
git add pyproject.toml CITATION.cff CHANGELOG.md
git commit -m "release: vx.y.z"
git tag -a vx.y.z -m "Release vx.y.z"
git push origin main --tags
```

### 4. Automated CI Pipelines

The following workflows trigger automatically on tag push:

| Workflow | File | Action |
|----------|------|--------|
| **Tests** | `tests.yml` | Runs full pytest suite on Ubuntu |
| **Sentinel Sign** | `sentinel-sign.yml` | Re-signs `AGENTS.lock` with CI keypair |
| **PyPI Publish** | `publish-pypi.yml` | Builds sdist + wheel, uploads to PyPI via OIDC Trusted Publishing |
| **Release Artifacts** | `release-artifacts.yml` | Generates CycloneDX v1.5 SBOM, SHA256SUMS, and Sigstore signatures |
| **VS Code Extension** | `publish-extension.yml` | Publishes `.vsix` to VS Code Marketplace and OpenVSX |

### 5. Post-Release Verification

```bash
# Verify PyPI package
pip install sentinel-md==x.y.z
sentinel --version
sentinel selftest

# Verify GitHub Release page has all artifacts:
# - sentinel-md-x.y.z.tar.gz
# - sentinel_md-x.y.z-py3-none-any.whl
# - sentinel-md.sbom.json
# - SHA256SUMS
# - sentinel-md.vsix
```

## Supply-Chain Integrity

- **CycloneDX v1.5 SBOM:** Generated automatically by `scripts/generate_sbom.py`.
- **SHA-256 Checksums:** Published in `SHA256SUMS` alongside release artifacts.
- **Sigstore Keyless Signing:** Release artifacts are signed using GitHub OIDC identity via `sigstore-python`.
- **CI Action Pinning:** All GitHub Actions are pinned to immutable 40-character commit SHAs (a test enforces this).
