# SENTINEL.md GitHub Action

Runs SENTINEL.md on every pull request that touches an agent-config file, posting findings as a PR comment.

## Installation
Copy `.github/workflows/sentinel.yml` to your repo's `.github/workflows/` directory, and copy `action/scan_pr.py` to your repo's `action/` directory. That's it!

## Enabling Layer 3 Analysis (Optional)
To enable the LLM-powered Layer 3 cognitive firewall, add your `GROQ_API_KEY` as an Action Secret in your repository settings. If absent, SENTINEL still runs Layer 1 structural rules perfectly.

## Reading the PR Comment
The action leaves an easy-to-read table on your PR:
- 🟢 **CLEAN (61-100)**: No structural indicators of hidden instructions detected.
- 🟡 **SUSPICIOUS (31-60)**: Findings detected. Warrants manual review.
- 🔴 **COMPROMISED (0-30)**: Severe or multiple malicious findings detected. Review immediately.

## Advisory Mode
This check runs in **Advisory Mode**. It never fails the CI build or blocks a merge, ensuring it never disrupts your team's workflow.
