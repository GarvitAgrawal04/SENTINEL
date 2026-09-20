# Security policy

Sentinel is a security tool, so problems in Sentinel itself matter more than usual. Thank you for looking.

## Report privately

Anything in the list below: please do **not** open a public issue. Use **Security → Report a vulnerability** on this
repository (GitHub private vulnerability reporting), or contact a maintainer directly. We are a small student team; expect
a first answer within a few days, and credit in the changelog unless you prefer otherwise.

- `AGENTS.lock` verification accepting a lock it should reject (signature, key pinning, coverage).
- A pull request managing to approve its own hooks or tool servers, or to swap the public key.
- `sentinel run` starting an agent in a repository it reported as COMPROMISED.
- Sentinel executing, importing or loading configuration from the repository it scans.
- A real secret printed in a finding, a log or a pull-request comment (redaction failure).
- The API reading or writing outside its temporary directory, or the web UI rendering scanned text as HTML.
- The signing workflow exposing `SENTINEL_SIGNING_KEY`.

## Report publicly

These are expected for a rule-based scanner and are best handled in the open, with a minimal file that reproduces them:

- **A bypass**: an instruction file that is clearly malicious and comes back CLEAN. Static rules catch shapes; a reworded
  instruction can pass, and our own benchmark documents 0 of 86 on unseen wordings. Every reproducible bypass becomes a fixture.
- **A false alarm** on a real, harmless file. We measure these on 930 public repositories and treat them as bugs.

## Supported versions

Only the latest commit on `main` and the latest release. Pin the GitHub Action to a release tag or a commit SHA: it runs in
your CI, and a moving `@main` is exactly the kind of thing this project exists to make people careful about.
