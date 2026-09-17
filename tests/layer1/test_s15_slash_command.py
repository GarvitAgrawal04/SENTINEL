"""
S15 — deposited slash command. Penalty −55. Not unambiguous (on its own).

A slash command lives in `.claude/commands/<name>.md` (nesting allowed:
`.claude/commands/git/commit.md` → /git:commit). When a package's postinstall step
*deposits* such a file, the agent gains a new invokable command that was never in the
repository the developer reviewed. S15 is a PROVENANCE rule, not a content rule: it fires
on any `.claude/commands/**/*.md` that is NOT in ctx.git_tracked. The body can be totally
benign — that is exactly the point (the malicious instruction may be a single innocuous
line, or the danger may be that it shadows an expected command).

Signal strength rises with origin: a command file absent from git AND an origin of
`postinstall-suspected` / `postinstall-confirmed` is the ChainDrop/persistence pattern.
The penalty is fixed at −55; origin is surfaced in evidence so Layer 3 / the formula's
attack-cluster multiplier can weight it.

OPEN QUESTION (README): whether S15 should escalate to unambiguous when
origin == postinstall-confirmed is left to the team. These tests assert penalty/΅not-unambiguous
and that origin reaches the evidence; they do NOT pin unambiguous=True for any origin.
"""
import pytest

R = "S15"


# --- positives ---------------------------------------------------------------
def test_untracked_command_file_fires(run_rule, make_ctx, only):
    """A .claude/commands/*.md that git never saw → deposited command."""
    ctx = make_ctx(git_tracked=set())
    f = only(run_rule(R, "Run the deploy sequence.\n", ".claude/commands/deploy.md", ctx), R)
    assert f.penalty == -55
    assert f.unambiguous is False
    assert ".claude/commands/deploy.md" in f.evidence


def test_content_agnostic(run_rule, make_ctx, ids):
    """Empty / totally benign body still fires — provenance is the signal."""
    ctx = make_ctx(git_tracked=set())
    assert R in ids(run_rule(R, "", ".claude/commands/hello.md", ctx))
    assert R in ids(run_rule(R, "# Greet the user politely.\n", ".claude/commands/hello.md", ctx))


@pytest.mark.parametrize("path", [
    ".claude/commands/deploy.md",
    ".claude/commands/git/commit.md",          # namespaced command
    ".claude/commands/ci/release/publish.md",  # deep nesting
])
def test_nested_command_paths_fire(run_rule, make_ctx, ids, path):
    ctx = make_ctx(git_tracked={"CLAUDE.md", "README.md"})  # tracked set exists, this file not in it
    assert R in ids(run_rule(R, "do a thing\n", path, ctx)), path


@pytest.mark.parametrize("origin", ["postinstall-suspected", "postinstall-confirmed"])
def test_origin_surfaced_in_evidence(run_rule, make_ctx, only, origin):
    """The persistence pattern: deposited during a package install step."""
    ctx = make_ctx(git_tracked=set(), origin=origin)
    f = only(run_rule(R, "hunt for secrets\n", ".claude/commands/sync.md", ctx), R)
    assert f.penalty == -55
    assert origin in f.evidence


# --- negatives ---------------------------------------------------------------
def test_tracked_command_does_not_fire(run_rule, make_ctx):
    """A command file that IS in git is part of the reviewed repo — legitimate."""
    ctx = make_ctx(git_tracked={".claude/commands/deploy.md", "CLAUDE.md"})
    assert run_rule(R, "Run the deploy sequence.\n", ".claude/commands/deploy.md", ctx) == []


def test_tracked_nested_command_does_not_fire(run_rule, make_ctx):
    ctx = make_ctx(git_tracked={".claude/commands/git/commit.md"})
    assert run_rule(R, "commit staged changes\n", ".claude/commands/git/commit.md", ctx) == []


def test_non_command_file_does_not_fire(run_rule, make_ctx):
    """S15 is scoped to .claude/commands/. An untracked CLAUDE.md is a different rule's problem."""
    ctx = make_ctx(git_tracked=set())
    assert run_rule(R, "# guide\n", "CLAUDE.md", ctx) == []
    assert run_rule(R, "{}", ".claude/settings.json", ctx) == []


def test_untracked_non_md_in_commands_dir_does_not_fire(run_rule, make_ctx):
    """Only .md files are invokable slash commands; a stray README/asset is not."""
    ctx = make_ctx(git_tracked=set())
    assert run_rule(R, "notes", ".claude/commands/README.txt", ctx) == []


def test_no_git_tracking_info_does_not_false_positive(run_rule, make_ctx):
    """
    If Layer 0 could not determine git tracking (e.g. not a git repo), git_tracked is a
    sentinel meaning 'unknown', not 'nothing tracked'. We model 'unknown' as the file being
    present in git_tracked (Layer 0's job to decide); the rule must not fire when the file is
    listed as tracked. This is the same assertion as the tracked case, guarding the default.
    """
    ctx = make_ctx(git_tracked={".claude/commands/deploy.md"})
    assert run_rule(R, "deploy\n", ".claude/commands/deploy.md", ctx) == []
