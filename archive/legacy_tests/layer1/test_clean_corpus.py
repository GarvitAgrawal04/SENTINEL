"""
Clean corpus: every benign sample must produce ZERO Layer-1 findings.

False positives are the fastest way to lose a security tool's users, so this sweep is the
suite's specificity backstop. Each sample is presented the way a clean checkout would be:
tracked in git, unchanged, ordinary git origin — so the provenance rules (S6 new-file,
S15 deposited command) see nothing anomalous and only the CONTENT is under test.

The samples live in tests/corpus.py (CLN-01..CLN-16) and cover the shapes most likely to
trip a naive detector: URLs in instructions, Windows BOM files, git SHAs and sha256 hashes
(not base64 payloads), benign markdown/HTML comments, stdio and remote-SSE MCP configs,
path-free hooks, and a security doc that *describes* these very attacks in prose.
"""
import pytest

from tests.layer1.corpus import CLEAN

CASES = sorted(CLEAN.items())


@pytest.mark.parametrize("name", [n for n, _ in CASES])
def test_clean_sample_has_no_findings(name, run_all_rules, make_ctx):
    path, content = CLEAN[name]
    ctx = make_ctx(git_tracked={path}, files={path: content}, origin="git")
    findings = run_all_rules(content, path, ctx)
    assert findings == [], (
        f"{name} ({path}) should be CLEAN but fired: "
        f"{[(f.rule_id, f.evidence) for f in findings]}"
    )
