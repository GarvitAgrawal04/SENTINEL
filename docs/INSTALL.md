# Installing Sentinel

Sentinel can be installed via PyPI, executed as an ephemeral one-liner via `pipx` or `uvx`, added to `.pre-commit-config.yaml`, or run in Cursor, Windsurf, and VS Code.

## 1. Fast Ephemeral One-Liners (No install needed)

### With `uvx` (Fastest)
```bash
uvx sentinel-md scan .
uvx sentinel-md doctor .
```

### With `pipx`
```bash
pipx run sentinel-md scan .
pipx run sentinel-md doctor .
```

## 2. Standard Python Installation (`pip` / `uv`)

Install from PyPI:

```bash
pip install sentinel-md
```

With optional extras:
```bash
pip install "sentinel-md[sign]"     # cryptographic AGENTS.lock signing
pip install "sentinel-md[api]"      # local FastAPI web server
pip install "sentinel-md[dev]"      # full development and test dependencies
```

## 3. Pre-Commit Hook

Add Sentinel to your repository's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/GarvitAgrawal04/SENTINEL
    rev: v0.9.8
    hooks:
      - id: sentinel-scan
      - id: sentinel-doctor
```

Then install the hook:
```bash
pre-commit install
```

## 4. Cursor, Windsurf & VS Code Extension

### From OpenVSX (Cursor & Windsurf)
Search for `Sentinel` in the Extensions view, or install via command line:
```bash
ovsx install sentinel.sentinel-md
```

### From Visual Studio Code Marketplace
Search for `Sentinel` (`sentinel.sentinel-md`) in the VS Code marketplace.

### Offline `.vsix` Direct Installation
Download the latest `sentinel-md.vsix` release from GitHub releases, then:
```bash
code --install-extension sentinel-md.vsix
# or in Cursor:
cursor --install-extension sentinel-md.vsix
```

## 5. GitHub Actions CI Integration

Add to `.github/workflows/sentinel.yml`:

```yaml
name: Sentinel Security Check

on:
  pull_request:

jobs:
  sentinel:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      security-events: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: GarvitAgrawal04/SENTINEL/action@main
        with:
          fail-on: compromised
```
