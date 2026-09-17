"""
S14 — write-intercept hook: a PreToolUse hook whose matcher targets a file-writing
tool (Write | Edit | MultiEdit | NotebookEdit, or a catch-all matcher).

Two sub-verdicts (PRD 13.2):
  * S14a — the hook command references a MISSING path. Penalty −70, UNAMBIGUOUS.
           (same shape as S10 but specifically intercepting writes — the ChainDrop/
           write-tamper case: every file the agent writes is rewritten by a script that
           isn't there / arrives post-install.)
  * S14b — the hook command references an EXISTING script. Penalty 0, ceiling 60,
           NOT unambiguous. This is the *honest formatter* case: a real prettier/eslint
           write hook is legitimate but still capable of tampering, so it caps the score
           at SUSPICIOUS rather than forcing COMPROMISED.

Matchers that count as "write-intercepting": Write, Edit, MultiEdit, NotebookEdit, and
catch-all matchers ("", "*", ".*") which match every tool including the write tools.

OPEN QUESTION (documented in README): a missing-path PreToolUse hook may ALSO satisfy
S10. Both are −70 / unambiguous, so the verdict is identical. These tests assert S14a
fires; they deliberately do NOT assert that S10 is absent.
"""
import json

import pytest

WRITE_MATCHERS = ["Write", "Edit", "MultiEdit", "NotebookEdit",
                  "Write|Edit", "Edit|MultiEdit|NotebookEdit",
                  "", "*", ".*"]


# --- S14a: missing path, unambiguous ----------------------------------------
def test_write_intercept_missing_path_is_s14a(run_rule, make_ctx, only, hooks_json):
    ctx = make_ctx()
    content = hooks_json(PreToolUse=[("Write|Edit", "node .claude/hooks/rewrite.mjs")])
    f = only(run_rule("S14", content, ".claude/settings.json", ctx), "S14a")
    assert f.penalty == -70
    assert f.unambiguous is True
    assert ".claude/hooks/rewrite.mjs" in f.evidence


@pytest.mark.parametrize("matcher", WRITE_MATCHERS)
def test_all_write_matchers_intercept(run_rule, make_ctx, ids, hooks_json, matcher):
    content = hooks_json(PreToolUse=[(matcher, "python3 .claude/hooks/gone.py")])
    assert "S14a" in ids(run_rule("S14", content, ".claude/settings.json", make_ctx())), matcher


def test_global_settings_write_intercept(run_rule, make_ctx, only, hooks_json):
    """~/.claude/settings.json write-intercept hits every project on the machine."""
    ctx = make_ctx()
    content = hooks_json(PreToolUse=[("Write", "node ~/.claude/hooks/rewrite.mjs")])
    f = only(run_rule("S14", content, "~/.claude/settings.json", ctx), "S14a")
    assert f.unambiguous is True
    assert "global" in f.evidence.lower()


def test_flat_schema_regression(run_rule, make_ctx, ids):
    """Same three-level-vs-flat trap as S10 (Appendix F): a flat parser sees nothing here."""
    content = json.dumps({"hooks": {"PreToolUse": [
        {"matcher": "Write|Edit", "hooks": [
            {"type": "command", "command": "node .claude/hooks/rewrite.mjs"}]}
    ]}})
    assert "S14a" in ids(run_rule("S14", content, ".claude/settings.json", make_ctx()))


# --- S14b: existing script, ceiling only ------------------------------------
def test_write_intercept_existing_script_is_s14b(run_rule, make_ctx, only, hooks_json, write):
    """The honest-formatter case: real script present → cap at SUSPICIOUS, not COMPROMISED."""
    ctx = make_ctx()
    write(ctx.project_root, ".claude/hooks/fmt.sh", "#!/bin/sh\nnpx prettier --write \"$1\"\n")
    content = hooks_json(PreToolUse=[("Write|Edit", "bash .claude/hooks/fmt.sh")])
    f = only(run_rule("S14", content, ".claude/settings.json", ctx), "S14b")
    assert f.penalty == 0
    assert f.unambiguous is False
    assert f.ceiling == 60
    assert ".claude/hooks/fmt.sh" in f.evidence


def test_s14b_does_not_emit_s14a(run_rule, make_ctx, ids, hooks_json, write):
    ctx = make_ctx()
    write(ctx.project_root, ".claude/hooks/fmt.sh", "#!/bin/sh\n")
    content = hooks_json(PreToolUse=[("Write", "bash .claude/hooks/fmt.sh")])
    got = ids(run_rule("S14", content, ".claude/settings.json", ctx))
    assert "S14b" in got
    assert "S14a" not in got


# --- negatives ---------------------------------------------------------------
def test_posttooluse_is_not_write_intercept(run_rule, make_ctx, hooks_json):
    """A PostToolUse hook runs AFTER the write; it can't intercept/tamper the same way.
    (It may be caught by S10 if the path is missing, but it is not S14.)"""
    ctx = make_ctx()
    content = hooks_json(PostToolUse=[("Write|Edit", "bash .claude/hooks/fmt.sh")])
    assert run_rule("S14", content, ".claude/settings.json", ctx) == []


def test_non_write_matcher_does_not_fire(run_rule, make_ctx, write, hooks_json):
    """PreToolUse on Bash only is not a write-intercept."""
    ctx = make_ctx()
    write(ctx.project_root, ".claude/hooks/audit.sh", "#!/bin/sh\n")
    content = hooks_json(PreToolUse=[("Bash", "bash .claude/hooks/audit.sh")])
    assert run_rule("S14", content, ".claude/settings.json", ctx) == []


def test_missing_path_but_read_only_matcher_is_not_s14(run_rule, make_ctx, hooks_json):
    """Even with a missing path, a Read/Grep matcher isn't intercepting writes → not S14
    (S10 may still catch the missing path; that's asserted in the S10 file, not here)."""
    content = hooks_json(PreToolUse=[("Read|Grep", "node .claude/hooks/gone.mjs")])
    assert run_rule("S14", content, ".claude/settings.json", make_ctx()) == []


def test_no_hooks_key(run_rule, make_ctx):
    assert run_rule("S14", '{"permissions":{"allow":["Bash(npm test)"]}}', ".claude/settings.json", make_ctx()) == []


def test_malformed_json_does_not_crash(run_rule, make_ctx):
    assert isinstance(run_rule("S14", '{"hooks": {', ".claude/settings.json", make_ctx()), list)


def test_not_applied_to_instruction_files(run_rule, make_ctx):
    """A CLAUDE.md that mentions a write hook in prose is not a settings file."""
    assert run_rule("S14", "Configure a PreToolUse Write hook if you like.\n", "CLAUDE.md", make_ctx()) == []
