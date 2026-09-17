"""
S10 — hook referencing a missing path, ANY event type. Penalty −70. STRUCTURALLY UNAMBIGUOUS.

ChainDrop / SafeDep shape (PRD 4.2): a `SessionStart` hook in .claude/settings.json pointing at
a script that the uninstalled package took with it. The hook keeps firing on every session.

PRD 13.3 / 20 item 9 — THE regression test for this project:
  Claude Code's hook schema is THREE levels deep:
      hooks -> <Event> -> [ { matcher?, hooks: [ { type, command } ] } ]
  "a flat-schema parser silently returns CLEAN on real attacks". If your parser reads
  hooks.SessionStart[0].command it will pass NOTHING in this file.
"""
import json

import pytest

R = "S10"

EVENTS = ["SessionStart", "SessionEnd", "PreToolUse", "PostToolUse", "UserPromptSubmit",
          "Notification", "Stop", "SubagentStop", "PreCompact"]


# --- positives ---------------------------------------------------------------
def test_chaindrop_session_start_missing_script(run_rule, make_ctx, only, hooks_json):
    ctx = make_ctx()
    content = hooks_json(SessionStart=[("", "node .claude/setup.mjs")])
    f = only(run_rule(R, content, ".claude/settings.json", ctx), R)
    assert f.penalty == -70
    assert f.unambiguous is True
    assert ".claude/setup.mjs" in f.evidence
    assert "SessionStart" in f.evidence


@pytest.mark.parametrize("event", EVENTS)
def test_any_event_type(run_rule, make_ctx, ids, hooks_json, event):
    matcher = "Bash" if event in ("PreToolUse", "PostToolUse") else ""
    content = hooks_json(**{event: [(matcher, "bash .claude/hooks/gone.sh")]})
    assert R in ids(run_rule(R, content, ".claude/settings.json", make_ctx())), event


@pytest.mark.parametrize("command,missing", [
    ("node .claude/setup.mjs", ".claude/setup.mjs"),
    ("python3 .claude/hooks/telemetry.py --quiet", ".claude/hooks/telemetry.py"),
    ("bash ./scripts/hooks/session.sh", "scripts/hooks/session.sh"),
    (".claude/hooks/run.sh", ".claude/hooks/run.sh"),                                  # bare relative script
    ('bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/gone.sh', ".claude/hooks/gone.sh"),     # documented env var
    ("bash $CLAUDE_PROJECT_DIR/.claude/hooks/gone.sh", ".claude/hooks/gone.sh"),
    ("sh -c 'node .claude/setup.mjs && echo ok'", ".claude/setup.mjs"),               # nested in sh -c
    ("node ./.claude/setup.mjs", ".claude/setup.mjs"),
])
def test_path_extraction_variants(run_rule, make_ctx, only, hooks_json, command, missing):
    content = hooks_json(SessionStart=[("", command)])
    f = only(run_rule(R, content, ".claude/settings.json", make_ctx()), R)
    assert missing in f.evidence.replace("\\", "/"), (command, f.evidence)


def test_absolute_missing_path(run_rule, make_ctx, ids, hooks_json, tmp_path):
    gone = tmp_path / "nowhere" / "hook.sh"
    content = hooks_json(SessionStart=[("", f'bash "{gone}"')])
    assert R in ids(run_rule(R, content, ".claude/settings.json", make_ctx()))


def test_global_settings_missing_path(run_rule, make_ctx, only, hooks_json):
    """~/.claude/settings.json applies to EVERY project on the machine (PRD 16: elevated severity)."""
    ctx = make_ctx()
    content = hooks_json(SessionStart=[("", "node ~/.claude/setup.mjs")])
    f = only(run_rule(R, content, "~/.claude/settings.json", ctx), R)
    assert "setup.mjs" in f.evidence
    assert "global" in f.evidence.lower()


def test_tilde_resolved_against_ctx_home_not_real_home(run_rule, make_ctx, ids, hooks_json, write):
    """The file exists under ctx.home → no S10. Proves the rule doesn't expanduser() the real $HOME."""
    ctx = make_ctx()
    write(ctx.home, ".claude/setup.mjs", "// present")
    content = hooks_json(SessionStart=[("", "node ~/.claude/setup.mjs")])
    assert R not in ids(run_rule(R, content, "~/.claude/settings.json", ctx))


def test_one_finding_per_missing_hook(run_rule, make_ctx, hooks_json):
    content = hooks_json(
        SessionStart=[("", "node .claude/a.mjs"), ("", "node .claude/b.mjs")],
        Stop=[("", "node .claude/c.mjs")],
    )
    findings = [f for f in run_rule(R, content, ".claude/settings.json", make_ctx()) if f.rule_id == R]
    assert len(findings) == 3
    assert {n for f in findings for n in ("a.mjs", "b.mjs", "c.mjs") if n in f.evidence} == {"a.mjs", "b.mjs", "c.mjs"}


def test_matcher_group_with_multiple_hooks(run_rule, make_ctx, ids):
    """Inner hooks array with two commands, one missing."""
    content = json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "npx eslint --quiet"},
        {"type": "command", "command": "bash .claude/hooks/gone.sh"},
    ]}]}})
    assert R in ids(run_rule(R, content, ".claude/settings.json", make_ctx()))


def test_flat_schema_regression(run_rule, make_ctx, ids):
    """
    Appendix F: the bug already caught once in this project's history.
    A parser that only reads a FLAT shape ({"hooks": {"SessionStart": [{"command": ...}]}})
    will see nothing here. This must fire.
    """
    content = json.dumps({
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "node .claude/setup.mjs"}]}
            ]
        }
    })
    assert R in ids(run_rule(R, content, ".claude/settings.json", make_ctx()))


# --- negatives ---------------------------------------------------------------
def test_existing_script_does_not_fire(run_rule, make_ctx, write, hooks_json):
    ctx = make_ctx()
    write(ctx.project_root, ".claude/hooks/lint.sh", "#!/bin/sh\nnpx eslint .\n")
    content = hooks_json(PostToolUse=[("Write|Edit", "bash .claude/hooks/lint.sh")])
    assert run_rule(R, content, ".claude/settings.json", ctx) == []


@pytest.mark.parametrize("command", [
    "npx prettier --write .",
    "echo 'session started'",
    "git status --short",
    "make lint",
    "pnpm test",
])
def test_path_free_commands_do_not_fire(run_rule, make_ctx, hooks_json, command):
    """Binaries resolved via PATH are not 'paths' — no filesystem claim to verify."""
    content = hooks_json(SessionStart=[("", command)])
    assert run_rule(R, content, ".claude/settings.json", make_ctx()) == []


def test_prompt_type_hook_has_no_path(run_rule, make_ctx):
    content = json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "prompt", "prompt": "Summarise the session."}]}]}})
    assert run_rule(R, content, ".claude/settings.json", make_ctx()) == []


def test_no_hooks_key(run_rule, make_ctx):
    assert run_rule(R, '{"permissions":{"allow":["Bash(npm test)"]}}', ".claude/settings.json", make_ctx()) == []


def test_empty_hooks(run_rule, make_ctx):
    assert run_rule(R, '{"hooks":{}}', ".claude/settings.json", make_ctx()) == []


def test_malformed_json_does_not_crash(run_rule, make_ctx):
    assert isinstance(run_rule(R, '{"hooks": {', ".claude/settings.json", make_ctx()), list)


def test_not_applied_to_instruction_files(run_rule, make_ctx):
    """A markdown file that *mentions* a missing path is not a hook (PRD 16 scoping)."""
    assert run_rule(R, "Run `node .claude/setup.mjs` if it exists.\n", "CLAUDE.md", make_ctx()) == []
