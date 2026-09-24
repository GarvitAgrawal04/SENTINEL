# Sentinel Enterprise Integration Guide

**Version:** 1.0.0  
**Supported Platforms:** GitHub Actions · GitLab CI · Pre-Commit · VS Code · Cursor · Windsurf · Docker · REST API  

---

## 1. GitHub Actions Integration

Sentinel provides an official composite action for pull request review, behavioral differential gating, and SARIF 2.1.0 code scanning integration.

### Quick Turnkey Workflow (`.github/workflows/sentinel.yml`)

```yaml
name: Sentinel Agent Security Check

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write
  security-events: write

jobs:
  audit-agent-instructions:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262  # v4.2.2
        with:
          fetch-depth: 0  # Required for base vs head git diffing

      - name: Run Sentinel Security Check
        uses: GarvitAgrawal04/SENTINEL/action@4c24c8bbca0f19c99ec98a631bf218cb72c83c27
        with:
          fail-on: compromised
          base: ${{ github.base_ref || 'main' }}

      - name: Upload SARIF to GitHub Code Scanning
        if: always()
        uses: github/codeql-action/upload-sarif@6bb034426ac73a9b003f37aa20f7f3d3bda44976  # v3
        with:
          sarif_file: sentinel.sarif
```

### Action Configuration Parameters

| Parameter | Type | Default | Description |
|:---|:---:|:---:|:---|
| `base` | string | `main` | Git base branch reference for differential guardrail analysis. |
| `fail-on` | string | `compromised` | Failure threshold: `compromised`, `suspicious`, or `never`. |
| `detonate` | boolean | `false` | Enable the optional Time-Warp sandbox detonation layer. |
| `format` | string | `sarif` | Output format: `sarif`, `json`, or `markdown`. |

---

## 2. Pre-Commit Hooks Integration

Integrate Sentinel into local developer commit workflows to catch unhygienic or dangerous instructions before they enter git history.

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/GarvitAgrawal04/SENTINEL
    rev: v1.0.0
    hooks:
      - id: sentinel-scan
        name: Sentinel Security Gate
        entry: sentinel scan .
        language: python
        pass_filenames: false

      - id: sentinel-doctor
        name: Sentinel Instruction Hygiene
        entry: sentinel doctor . --fix
        language: python
        pass_filenames: false
```

---

## 3. IDE Integration: VS Code, Cursor & Windsurf

Sentinel provides seamless in-editor diagnostics and instant safe fixes for VS Code, Cursor, and Windsurf.

### Installation
- **VS Code:** Install from the [VS Code Marketplace](https://marketplace.visualstudio.com/) (`sentinel-md`).
- **Cursor / Windsurf:** Install from [OpenVSX Registry](https://open-vsx.org/extension/GarvitAgrawal04/sentinel-md) or install the `.vsix` release asset directly:
  ```bash
  code --install-extension sentinel-md.vsix
  ```

### Key IDE Capabilities
1. **On-Save Diagnostics:** High-entropy exfiltration strings and unapproved hook scripts are underlined in real time.
2. **Status Bar Verdict:** Live security posture indicator (`Clean 100/100`, `Suspicious`, `Compromised`).
3. **One-Click Quick Fixes:** Instant automated remediation for D001 (broken includes), D004 (duplicate rules), and D008 (ANSI escapes).
4. **Gated Safe Rewrite:** Interactively suggest sanitized prompt wordings verified by the offline security gate before insertion.

---

## 4. Docker & Containerized Scans

For air-gapped CI/CD environments or Kubernetes admission controllers:

```bash
# Build the minimal scanner container:
docker build -t sentinel-scanner -f Dockerfile .

# Scan an arbitrary local project directory:
docker run --rm -v $(pwd):/workspace:ro sentinel-scanner sentinel scan /workspace
```

---

## 5. REST API & Programmatic Integration

Sentinel exposes a lightweight, dependency-minimal FastAPI service for centralized security portals.

### Starting the API Server
```bash
python -m uvicorn sentinel.api:app --host 127.0.0.1 --port 8000
```

### Endpoints
- `POST /scan/text`: Audit raw instruction text submitted in JSON payload.
- `POST /scan/upload`: Audit an uploaded zip archive or multi-part files.
- `GET /doctor/graph`: Retrieve interactive SVG load graph and dependency analysis.
- `GET /health`: Engine version and deterministic self-test status.

#### Example Python Client
```python
import urllib.request
import json

payload = json.dumps({"text": "CLAUDE.md instructions here"}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8000/scan/text",
    data=payload,
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print(f"Verdict: {result['verdict']}, Score: {result['score']}")
```

---

## 6. Makefile & CLI Script Automation

Sentinel returns standard exit codes suitable for automated shell scripts and Makefiles:

| Exit Code | Meaning | Shell Script Action |
|:---:|:---|:---|
| **0** | `CLEAN` | Allow build / agent launch to proceed. |
| **3** | `SUSPICIOUS` | Request manual reviewer approval. |
| **2** | `COMPROMISED` | Block execution; abort pipeline. |
| **1** | Usage Error | Check environment / CLI flags. |

#### Example Makefile Target
```makefile
.PHONY: agent-guard
agent-guard:
	@echo "Auditing agent configuration..."
	@sentinel scan . || (echo "Sentinel blocked agent execution." && exit 1)
	@sentinel run -- claude
```
