# Contributing to Sentinel

Thank you for your interest in contributing to Sentinel! Sentinel is an open-source security engine dedicated to protecting developer environments and autonomous AI coding agents from prompt injection, auto-execution backdoors, and malicious tool configurations.

To maintain our empirical standard of **zero false convictions across production codebases**, all contributions adhere to rigorous engineering and testing protocols.

---

## Code of Conduct & Governance

All contributors and maintainers are expected to abide by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

For details on decision-making, project roles (Contributors, Reviewers, Maintainers, Technical Steering Committee), and the RFC process, see [GOVERNANCE.md](GOVERNANCE.md) and [CHARTER.md](CHARTER.md).

---

## 1. Development Environment Setup

Sentinel requires **Python 3.10 or newer** and **Git**. Sentinel has zero mandatory runtime dependencies for its core static scanner.

### 1.1 Clone and Initialize Virtual Environment

```bash
# Clone repository
git clone https://github.com/GarvitAgrawal04/SENTINEL.git
cd SENTINEL

# Run automated setup (creates .venv and installs dev tools)
# macOS / Linux / Git Bash:
bash setup.sh --install-only

# Windows (PowerShell):
.\setup.bat -InstallOnly
```

### 1.2 Activate Virtual Environment

```bash
# macOS / Linux / Git Bash:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 1.3 Install Pre-Commit Hooks

We use `pre-commit` to ensure code formatting, link integrity, and hygiene checks run before every commit:

```bash
pip install pre-commit
pre-commit install
```

---

## 2. Project Layout

```text
SENTINEL/
├── sentinel/                # Core engine package
│   ├── core.py              # Central scanner, scoring engine, rule dispatcher
│   ├── prose.py             # Markdown tokenization, sentence extraction, regex
│   ├── cli.py               # Command-line interface (scan, run, doctor, lock, pr)
│   ├── lock.py              # AGENTS.lock cryptographic signing and verification
│   ├── sarif.py             # OASIS SARIF 2.1.0 output exporter
│   ├── gitdiff.py           # Git differential and PR comment generator
│   ├── semantic.py          # Layer 3 bounded advisory judge
│   ├── machine.py           # Global developer configuration scanner
│   ├── doctor/              # Layer 4 Instruction Doctor & hygiene lints
│   │   ├── graph.py         # Include DAG traversal & cycle detection
│   │   ├── lints.py         # D001–D008 deterministic hygiene checks
│   │   └── gate.py          # Rewrite Gate AST prompt injection interceptor
│   ├── timewarp/            # Layer 2 Time-Warp multi-moment sandbox
│   │   ├── triggers.py      # 10 trigger families extraction
│   │   ├── clock.py         # Virtual clock, session, and env simulator
│   │   ├── cassette.py      # Deterministic offline replay engine
│   │   └── diff.py          # Multi-moment behavioral difference detector
│   └── rules/               # Modular rule implementations
├── tests/                   # Comprehensive automated test suite
│   └── v5/                  # Version 5 regression, stress, and unit tests
├── bench/                   # Empirical benchmark harness and corpora
├── docs/                    # Architectural specs, guides, threat model, runbooks
└── frontend/                # Static local web interface (HTML/CSS/JS)
```

---

## 3. Rule Authoring Lifecycle

Every detection rule in Sentinel must satisfy strict falsifiability criteria. We never deploy a rule based on intuition alone.

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  1. Real Threat  │     │ 2. Attack Vector │     │ 3. Benign Twin   │
│  Incident / CVE  │ ──> │   & Regex/AST    │ ──> │ (Negative Control│
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 6. Render & Docs │     │ 5. Wild Corpus   │     │ 4. Unit Tests    │
│ Remediation Text │ <── │  Benchmark Run   │ <── │ Fixture Pairing  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Step 1: Document the Real Threat
Identify the concrete threat pattern from published research (e.g., Pillar Security, Socket, StepSecurity) or real-world incidents.

### Step 2: Write the Rule Implementation
Implement the deterministic regex or AST pattern in `sentinel/core.py` or `sentinel/rules/`:
- Keep regex patterns linear-time to prevent ReDoS.
- Assign an appropriate penalty and classification (decisive cut, ceiling cap, or additive penalty).

### Step 3: Pair with a "Benign Twin" (Mandatory Negative Control)
For every attack fixture, you **must create a benign twin**—a realistic document that uses similar vocabulary (such as an engineering discussion, code documentation, or safe test script) without being an attack.
- *Example Attack:* A rule instructing the agent to dump `.env` to `https://attacker.example`.
- *Example Benign Twin:* A `CONTRIBUTING.md` file explaining: *"Do not commit your `.env` file to git; use `.env.example` instead."*
- If your rule fires on the benign twin, it is rejected.

### Step 4: Add Rule Metadata in `sentinel/render.py`
Every rule ID (`S1`–`S26`, `D001`–`D008`) must have a user-facing human title and actionable remediation advice in `sentinel/render.py`. A CI test will fail if metadata is omitted.

### Step 5: Benchmark Against the Wild Corpus
Run the benchmark harness against public repositories to verify zero regression:
```bash
python bench/wildscan.py search corpus
python bench/wildscan.py fetch corpus
python bench/bench.py wild corpus
```
Target: **0 false convictions (`COMPROMISED`)**.

---

## 4. Testing & Verification

Sentinel maintains a comprehensive testing matrix covering unit, integration, and adversarial stress conditions:

```bash
# Run the complete test suite (340+ tests)
pytest

# Run the README and asset verification suite
pytest tests/v5/test_readme.py

# Run extreme soak, ReDoS, and concurrency stress tests
pytest tests/v5/test_extreme_stress.py

# Run engine self-test
sentinel selftest

# Scan the Sentinel repository itself (clean invariant)
sentinel scan .
```

### 4.1 Asset Rebuilding
If documentation or diagram generators are updated, regenerate visual SVGs using the asset builder:
```bash
python docs/build_readme_assets.py
```
`tests/v5/test_readme.py` guarantees that committed SVGs match generator output byte-for-byte.

### 4.2 Link Verification
Validate that all external links answer HTTP 200:
```bash
python docs/check_readme_links.py
```

---

## 5. Coding Standards & Conventions

1. **Zero-Network Default:** Scanners and doctor utilities must never initiate outbound network connections or rely on remote services.
2. **Zero-Execution Invariant:** Never use `eval()`, `exec()`, or dynamic `__import__()` on scanned content.
3. **No Secret Leaks:** When reporting rule matches, always use `core.redact` to mask sensitive values or API tokens.
4. **Typing and Linting:**
   - Use Python 3.10+ type annotations.
   - Code must pass `ruff check .` and `black --check .`.
5. **No AI Slop / Phrasing Guardrails:**
   - Do not use hype words or marketing superlatives.
   - Strictly avoid hype terms and absolute financial superlatives. Use concrete metrics (e.g., `930 public repositories`, `340 tests passed`).

---

## 6. Git & Pull Request Workflow

1. **Fork and Branch:** Create a feature branch from `main`:
   ```bash
   git checkout -b feat/describe-your-change
   ```
2. **Commit Convention:** Use Conventional Commits formatting:
   - `feat: add S27 rule for tool parameter shadowing`
   - `fix: resolve D003 path traversal false positive on windows symlinks`
   - `docs: update integration guide for GitLab CI`
   - `test: add benign twin for temporal git trigger`
3. **Open Pull Request:**
   - Ensure all automated checks pass (`tests`, `sentinel-sign`, pre-commit).
   - Link any related issues or RFC proposals.
4. **Cryptographic Lockfile (`AGENTS.lock`):**
   - Do **not** manually edit `AGENTS.lock`.
   - If configuration files change, run `sentinel approve` locally to update. The official CI workflow will cryptographically re-sign the lockfile upon merge.

---

## 7. Security Disclosures

If you discover a security vulnerability or potential bypass in Sentinel, please review [SECURITY.md](SECURITY.md) and report it via GitHub Private Vulnerability Reporting or via email to the maintainers. Do not open public issues for zero-day vulnerabilities.
