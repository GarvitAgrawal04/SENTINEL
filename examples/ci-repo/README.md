# Sentinel CI Example Repository

This directory demonstrates a complete GitHub Actions CI integration for Sentinel:

1. **Pull Request Behavioral Diffs (`sentinel pr`):**
   Runs against `origin/main` to detect modified agent instructions, unapproved hooks, new MCP servers, and weakened guardrails.
2. **Pull Request Comments:**
   Posts plain-English markdown summaries directly onto the PR.
3. **SARIF Code Scanning (`--format sarif`):**
   Generates a SARIF 2.1.0 document and uploads it via `github/codeql-action/upload-sarif@v3`, surfacing findings directly on GitHub's **Security $\to$ Code scanning** dashboard.
4. **Pre-commit Integration:**
   Supports local verification via `.pre-commit-hooks.yaml`.

## Usage in Your Repository

Copy `.github/workflows/sentinel-ci.yml` into your repository's `.github/workflows/` directory. Ensure your repository settings grant read and write permissions to `pull-requests` and `security-events`.
