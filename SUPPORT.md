# Support and Maintenance Policy

Thank you for using Sentinel! This document outlines support channels, version maintenance, security vulnerability reporting, and response expectations.

## Support Channels

- **Bug Reports & Feature Requests:** Please file an issue on GitHub at [GarvitAgrawal04/SENTINEL/issues](https://github.com/GarvitAgrawal04/SENTINEL/issues).
- **Discussions & Ideas:** Join repository discussions or open an issue labeled `question`.
- **Security Disclosures:** For sensitive security vulnerabilities or zero-day issues in agent security rules, please follow our coordinated disclosure policy below.

## Reporting Security Vulnerabilities

If you discover a vulnerability in Sentinel or an evasion technique that bypasses deterministic guardrails without detection:
1. **Do not open a public issue.**
2. Email the maintainers directly or use [GitHub Private Vulnerability Reporting](https://github.com/GarvitAgrawal04/SENTINEL/security/advisories/new).
3. Include:
   - Reproduction instructions or inert test fixture.
   - Sentinel version (`sentinel --version`).
   - Expected behavior vs observed behavior.
4. Maintainers aim to acknowledge reports within 48 hours and release patched updates swiftly.

## Supported Versions and Platforms

| Sentinel Version | Python Versions | OS Platforms | Maintenance Status |
|:---:|:---:|:---:|:---:|
| **`1.0.x`** (Latest) | 3.10, 3.11, 3.12, 3.13, 3.14 | Linux, macOS, Windows | Active Development |
| `< 1.0.0` | 3.10+ | Linux, macOS, Windows | Deprecated |

## IDE and Editor Support

- **Cursor:** Supported via OpenVSX registry and local `.vsix` installation.
- **Windsurf:** Supported via OpenVSX registry and local `.vsix` installation.
- **VS Code:** Supported via Microsoft Marketplace and local `.vsix` installation.
- **CLI / CI Environments:** Supported via `pip`, `pipx`, `uvx`, GitHub Actions, and Pre-commit.
