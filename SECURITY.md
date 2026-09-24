# Security Policy & Vulnerability Disclosure

Sentinel is a security gate for autonomous AI agents. Because developers and CI/CD pipelines rely on Sentinel to evaluate unverified code before execution, the integrity, determinism, and isolation of Sentinel itself are of paramount importance.

---

## 1. Reporting a Security Vulnerability

If you discover a security vulnerability in Sentinel, **please do not open a public issue.** Public disclosure exposes users before a fix can be verified and released.

### Preferred Reporting Method
Use **GitHub Private Vulnerability Reporting**:
1. Navigate to the Sentinel repository on GitHub.
2. Click the **Security** tab.
3. Select **Advisories** $\rightarrow$ **Report a vulnerability**.
4. Fill in the advisory form with detailed reproduction steps, impact assessment, and any proposed fixes.

Alternatively, contact the project maintainers directly:
- **Garvit Agrawal** (`https://github.com/GarvitAgrawal04`)
- **Mayan Kamboj** (`https://github.com/kambojmayan-png`)

---

## 2. Response & Remediation SLA

The maintainers commit to the following Coordinated Vulnerability Disclosure (CVD) timelines:

| Stage | Target Timeline | Details |
|:---|:---|:---|
| **Initial Acknowledgment** | **Within 48 hours** | Confirm receipt of vulnerability report and establish a communication channel. |
| **Triage & Assessment** | **Within 7 days** | Reproduce the issue, assess CVSS v3.1 score, and determine affected versions. |
| **Fix Development** | **Within 21 days** | Author, test, and cryptographically verify the patch against regression suites. |
| **Release & Disclosure** | **Within 30 days** | Publish a patched release, update changelogs, and publish the GitHub Security Advisory. |

Researchers who report valid vulnerabilities will be prominently credited in [`CHANGELOG.md`](CHANGELOG.md), GitHub Security Advisories, and release notes (unless anonymity is requested).

---

## 3. High-Priority Invariant Violations (Report Privately)

Please report the following categories privately as critical security findings:

- **Cryptographic Lock Tampering:** `AGENTS.lock` verification accepting a forged signature, bypassed key-pinning check, or tampered file list.
- **Base-Branch Trust Boundary Bypass:** A pull request managing to approve its own hooks/tool servers, or substituting the verification public key.
- **Execution Gate Failure:** `sentinel run -- <agent>` launching an agent within a project scored as `COMPROMISED`.
- **Zero-Execution Invariant Violation:** Sentinel executing, importing, evaluating, or loading arbitrary code or `.env` configurations from the repository being scanned.
- **Secret Redaction Failure:** Unredacted developer credentials, API keys, or tokens appearing in CLI terminal output, SARIF exports, API responses, or PR comments.
- **Sandbox Container Escape:** A sandboxed agent instruction escaping the Time-Warp sandbox and interacting with real network sockets or host subprocesses.
- **Web App / Extension Injection:** Arbitrary HTML/JavaScript injection (XSS) via parsed markdown content in the web UI or VS Code extension.

---

## 4. Operational Invariants

Sentinel enforces four hard security invariants across all code paths:

1. **Zero-Network Default:** Static analysis (`sentinel scan`) and Instruction Doctor (`sentinel doctor`) require zero outbound network connections. Sockets remain closed.
2. **Zero-Execution Invariant:** The scanner inspects files via standard library AST parsing, structural JSON evaluation, and regular expressions. It never imports, evals, or executes scanned files.
3. **Scanned Directory Untrusted Boundary:** Configuration is never loaded from the repository under inspection. Sentinel strictly ignores hostile `.env`, `.git/config`, or task files located in the target directory.
4. **Secrets Redaction:** Every string matching high-entropy credential patterns is passed through `sentinel.core.redact()` before entering logs, reports, or PR comments.

---

## 5. Public Reporting (Functional Bypasses & False Alarms)

The following items are not software vulnerabilities in Sentinel itself, but rather algorithmic detection boundaries. These should be reported as **public GitHub issues** with minimal reproducible test fixtures:

- **Heuristic Bypasses:** An instruction file that is adversarial but scored as `CLEAN (100/100)`. Because regular expressions match structure rather than human intent, novel wordings are tracked empirically. Every reproducible bypass is cataloged into the adversarial corpus (`bench/corpus/`).
- **Benign False Alarms:** A legitimate, harmless open-source repository scored as `COMPROMISED` or `SUSPICIOUS`. We measure false-positive rates across 930 public repositories and treat false alarms as high-priority bugs.

---

## 6. Supported Versions

| Version | Supported | Security Patch Strategy |
|:---|:---:|:---|
| **v1.0.x** | ✅ Active | Critical security patches, bug fixes, rule updates. |
| **< 1.0.0** | ❌ Deprecated | Unsupported; please upgrade to the latest stable release. |

Always pin the Sentinel GitHub Action to a full 40-character commit SHA:
```yaml
- uses: GarvitAgrawal04/SENTINEL/action@4c24c8bbca0f19c99ec98a631bf218cb72c83c27
```

---

## 7. Safe Harbor Policy

We consider security research conducted under this policy to be authorized. We will not pursue legal action against researchers who:
- Make a good-faith effort to avoid privacy violations, data destruction, and service degradation.
- Give maintainers reasonable time to remediate vulnerabilities prior to public disclosure.
- Do not exploit a vulnerability beyond what is strictly necessary to demonstrate the proof-of-concept.
