# Project Sentinel Governance

**Version:** 1.0.0  
**Effective Date:** September 2026  
**Charter Reference:** [`CHARTER.md`](CHARTER.md)  

---

## 1. Governance Principles

Project Sentinel is governed as an open-source, meritocratic security engineering initiative. Its governance model reflects four core principles:

1. **Empirical Decision-Making:** Architectural choices and rule additions are governed by reproducible benchmarks rather than subjective preference. No security rule is merged without a published attack fixture, a benign twin, and an evaluation against the 930-repository corpus.
2. **Transparent Operations:** Technical designs, architectural decision records (ADRs), meeting summaries, and roadmap milestones are documented publicly within the repository.
3. **Meritocratic Advancement:** Maintainer responsibilities and voting privileges are granted based on sustained technical excellence, security stewardship, and constructive code review.
4. **Architectural Invariant Primacy:** The four core invariants (Zero-Network, Zero-Execution, Untrusted Input Isolation, Secrets Redaction) supersede all feature proposals.

---

## 2. Contributor & Maintainer Roles

```
  ┌──────────────────────────────────────────────────────────┐
  │         Technical Steering Committee (TSC)               │
  │     Overall Architecture, Release Signing, Roadmap       │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │                   Core Maintainers                       │
  │       PR Merge Authority, Triage, Security Review        │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │                      Reviewers                           │
  │        Domain Review, Test Verification, Benchmarks      │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │                     Contributors                         │
  │         Code, Fixes, Bug Bypasses, Documentation         │
  └──────────────────────────────────────────────────────────┘
```

### Contributor
Anyone who submits issues, pull requests, test fixtures, or documentation improvements.
- **Responsibilities:** Abide by [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Permissions:** Read access, issue creation, fork pull requests.

### Reviewer
Contributors who demonstrate deep expertise in a domain (e.g., AST parsing, Time-Warp simulation, VS Code extension, SARIF integration) and regularly review incoming pull requests.
- **Appointment:** Nominated by any Core Maintainer after 3+ merged contributions and active, high-quality review participation over at least 30 days.
- **Permissions:** PR review assignment, triage label management.

### Core Maintainer
Maintainers possess write and merge access to the repository. They are responsible for day-to-day code review, release verification, and issue triage.
- **Appointment:** Approved by unanimous vote of the Technical Steering Committee following sustained contributions (5+ substantial PRs, deep code review, understanding of security invariants).
- **Responsibilities:** Enforce testing requirements, verify CI status, review security fixes, and uphold release standards.

### Technical Steering Committee (TSC)
The TSC sets long-term technical strategy, maintains cryptographic signing keys, approves breaking API changes, and resolves architectural disputes.
- **Current Members:**
  - **Garvit Agrawal** (`@GarvitAgrawal04`) — Architecture, Core Engine & Rule Formulation Lead
  - **Mayan Kamboj** (`@kambojmayan-png`) — Security Research, Evaluation & Attack Corpus Lead

---

## 3. Decision-Making & RFC Process

### Routine Changes (Bug Fixes, Minor Enhancements)
- Requires review and approval from at least one Core Maintainer.
- Must pass all automated CI checks (`tests`, `sentinel-sign`, and self-tests).
- Maintainers merge when satisfied that tests and documentation are complete.

### Significant Changes (New Engine Layers, Rule Re-weighting, Public API Modifications)
Significant architectural modifications must follow the Request for Comments (RFC) process:
1. **Proposal:** Author creates an Architectural Decision Record in `docs/adr/ADR-XXXX-<title>.md` via a draft pull request.
2. **Review Window:** A minimum 7-day public discussion period on GitHub Issues / Pull Requests.
3. **Benchmark Proof:** If a change modifies rule weights or scoring thresholds, the author must publish an empirical delta run showing precision/recall impact across the 930-repo benchmark.
4. **Approval:** Requires consensus from the TSC.

---

## 4. Release & Signing Governance

Releases are published through a deterministic, cryptographically signed pipeline:
1. **Version Tagging:** Releases follow Semantic Versioning 2.0.0 (`vMAJOR.MINOR.PATCH`).
2. **Dual-Key Attestation:**
   - Source code commits and Git release tags must be GPG/SSH signed by a TSC member.
   - Release distribution wheels (`.whl`) and tarballs (`.tar.gz`) are signed in GitHub Actions via Sigstore keyless OIDC attestation.
   - Release binaries include a CycloneDX v1.5 JSON Software Bill of Materials (SBOM) and SHA-256 digests.
3. **`AGENTS.lock` Key Management:**
   - The private Ed25519 signing key (`SENTINEL_SIGNING_KEY`) is stored strictly in the GitHub `sentinel-signing` protected environment, restricted to execution on the `main` branch.
   - No developer or pull request can sign an `AGENTS.lock` file directly; approval must transit through CI verification.

---

## 5. Conflict Resolution & Succession

- **Consensus Preferred:** The TSC strives for rough consensus among all maintainers.
- **Dispute Resolution:** In the event of an intractable deadlock, a formal vote is called. Decisions pass with a simple majority of TSC members. In the event of a tie, the Core Architecture Lead holds the casting vote.
- **Inactivity:** A maintainer inactive for >90 days may be moved to emeritus status upon written notice. Emeritus maintainers may be reinstated upon resumption of active contributions.
