"""
S6 — new/modified surface file in a dependency PR. Penalty −15. Not unambiguous.
This is a *trigger* rule: it reads ctx.diff_status (Layer 0 populates it) and feeds Layer 2.
It is content-agnostic — a clean-looking new CLAUDE.md in a PR still fires S6.

OPEN QUESTION (PRD 13.2 says "in dependency PR"): whether S6 should be limited to PRs that
also touch a lockfile / are authored by a dependency bot is not specified. These tests only
assert on diff_status. Add a `ctx.pr_is_dependency_update` gate if the team decides on one.
"""
import pytest

from tests.layer1.corpus import CLEAN_CLAUDE_MD

R = "S6"


@pytest.mark.parametrize("status", ["added", "modified"])
def test_changed_surface_file_fires(run_rule, make_ctx, only, status):
    ctx = make_ctx(diff_status={"CLAUDE.md": status})
    f = only(run_rule(R, CLEAN_CLAUDE_MD, "CLAUDE.md", ctx), R)
    assert f.penalty == -15
    assert f.unambiguous is False
    assert status in f.evidence.lower()
    assert "CLAUDE.md" in f.evidence


def test_content_agnostic(run_rule, make_ctx, ids):
    """Even an empty new file in the diff is a Layer 2 trigger."""
    ctx = make_ctx(diff_status={".cursorrules": "added"})
    assert R in ids(run_rule(R, "", ".cursorrules", ctx))


@pytest.mark.parametrize("path", [
    ".claude/settings.json", ".mcp.json", ".cursor/rules/setup.mdc", ".github/copilot-instructions.md",
    "SKILL.md", ".claude/commands/deploy.md", "AGENTS.md",
])
def test_every_surface_type_can_trigger(run_rule, make_ctx, ids, path):
    ctx = make_ctx(diff_status={path: "added"})
    assert R in ids(run_rule(R, "{}", path, ctx))


# --- negatives ---------------------------------------------------------------
def test_unchanged_file_does_not_fire(run_rule, make_ctx):
    ctx = make_ctx(diff_status={"CLAUDE.md": "unchanged"})
    assert run_rule(R, CLEAN_CLAUDE_MD, "CLAUDE.md", ctx) == []


def test_file_absent_from_diff_status_does_not_fire(run_rule, make_ctx):
    """No diff information at all (e.g. local `sentinel scan` outside a PR) — S6 stays silent."""
    ctx = make_ctx(diff_status={})
    assert run_rule(R, CLEAN_CLAUDE_MD, "CLAUDE.md", ctx) == []


def test_other_file_changed_does_not_fire_for_this_one(run_rule, make_ctx):
    ctx = make_ctx(diff_status={".cursorrules": "modified"})
    assert run_rule(R, CLEAN_CLAUDE_MD, "CLAUDE.md", ctx) == []
