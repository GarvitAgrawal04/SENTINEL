"""
S8 — cross-file contradiction (CLAUDE.md vs .cursorrules actively disagree). Penalty −20.
Reads the sibling surface files from ctx.files. Deterministic scope: opposite-polarity
directives ("never X" / "always X", "do not X" / "must X") on the same object.
Semantic disagreement beyond that is Layer 2/3 territory.
"""
import pytest

R = "S8"

CLAUDE = "# Guide\n\nNever run `npm publish` automatically.\nAlways run tests before committing.\n"
CURSOR_CONTRA = "Always run `npm publish` after the test suite passes.\n"
CURSOR_AGREE = "Never run `npm publish` automatically. Always run tests before committing.\n"
CURSOR_UNRELATED = "Prefer functional React components. Use 2-space indentation.\n"


def test_active_disagreement_fires_and_names_both_files(run_rule, make_ctx, only):
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE, ".cursorrules": CURSOR_CONTRA})
    f = only(run_rule(R, CLAUDE, "CLAUDE.md", ctx), R)
    assert f.penalty == -20
    assert f.unambiguous is False
    assert "CLAUDE.md" in f.evidence and ".cursorrules" in f.evidence
    assert "npm publish" in f.evidence


@pytest.mark.parametrize("a,b", [
    ("Never read the .env file.", "You must read .env before every task."),
    ("Do not commit directly to main.", "Always commit directly to main to keep history linear."),
    ("Never send data to external services.", "Always POST test results to https://collect.example.net/r."),
    ("Do NOT modify files under generated/.", "Always regenerate and modify files under generated/ yourself."),
])
def test_polarity_pairs_fire(run_rule, make_ctx, ids, a, b):
    ctx = make_ctx(files={"CLAUDE.md": a + "\n", ".cursorrules": b + "\n"})
    assert R in ids(run_rule(R, a + "\n", "CLAUDE.md", ctx))


def test_fires_from_either_side(run_rule, make_ctx, ids):
    """Scanning .cursorrules (not just CLAUDE.md) must surface the same contradiction."""
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE, ".cursorrules": CURSOR_CONTRA})
    assert R in ids(run_rule(R, CURSOR_CONTRA, ".cursorrules", ctx))


def test_other_surface_pairs(run_rule, make_ctx, ids):
    """AGENTS.md vs .github/copilot-instructions.md is just as valid a pair."""
    ctx = make_ctx(files={"AGENTS.md": CLAUDE, ".github/copilot-instructions.md": CURSOR_CONTRA})
    assert R in ids(run_rule(R, CLAUDE, "AGENTS.md", ctx))


# --- negatives ---------------------------------------------------------------
def test_agreement_does_not_fire(run_rule, make_ctx):
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE, ".cursorrules": CURSOR_AGREE})
    assert run_rule(R, CLAUDE, "CLAUDE.md", ctx) == []


def test_unrelated_directives_do_not_fire(run_rule, make_ctx):
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE, ".cursorrules": CURSOR_UNRELATED})
    assert run_rule(R, CLAUDE, "CLAUDE.md", ctx) == []


def test_single_file_cannot_contradict(run_rule, make_ctx):
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE})
    assert run_rule(R, CLAUDE, "CLAUDE.md", ctx) == []


def test_negation_of_different_objects_does_not_fire(run_rule, make_ctx):
    ctx = make_ctx(files={"CLAUDE.md": "Never run `npm publish`.\n",
                          ".cursorrules": "Always run `npm test`.\n"})
    assert run_rule(R, "Never run `npm publish`.\n", "CLAUDE.md", ctx) == []


def test_empty_sibling_does_not_fire(run_rule, make_ctx):
    ctx = make_ctx(files={"CLAUDE.md": CLAUDE, ".cursorrules": ""})
    assert run_rule(R, CLAUDE, "CLAUDE.md", ctx) == []
