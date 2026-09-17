"""
S16 — enableAllProjectMcpServers: true.  Penalty 0, ceiling 60.

`.claude/settings.json` may contain `"enableAllProjectMcpServers": true`, which tells
Claude Code to auto-approve *every* MCP server declared in the project's `.mcp.json`
without the usual per-server human approval. On its own that is a misconfiguration /
sharp-edge, not proof of compromise: a developer may legitimately opt in. So S16 alone
behaves like S14b — penalty 0, ceiling 60 (the file can't score CLEAN, but it is NOT
forced to COMPROMISED).

The teeth appear in context. When the setting was introduced by a package install step
(origin `postinstall-suspected` / `postinstall-confirmed`), auto-approving all servers is
the MCP-autoenable persistence pattern (PRD ATR-MCP-005): the attacker's injected
`.mcp.json` server is now trusted silently. In that case S16 escalates to
unambiguous=True.

These tests pin:
  * true alone           → fires, penalty 0, ceiling 60, unambiguous False
  * true + install origin→ unambiguous True
  * false / absent       → no finding
  * global ~/.claude/settings.json is in scope
  * not a settings file  → out of scope
"""
import json

import pytest

R = "S16"

SETTINGS = ".claude/settings.json"


def _settings(value=None, extra=None) -> str:
    doc: dict = {}
    if value is not None:
        doc["enableAllProjectMcpServers"] = value
    if extra:
        doc.update(extra)
    return json.dumps(doc, indent=2)


# --- positives ---------------------------------------------------------------
def test_true_alone_fires_with_ceiling(run_rule, make_ctx, only):
    """Auto-enable on its own is a sharp edge: ceiling 60, not COMPROMISED."""
    f = only(run_rule(R, _settings(True), SETTINGS, make_ctx()), R)
    assert f.penalty == 0
    assert f.ceiling == 60
    assert f.unambiguous is False


def test_true_survives_other_benign_keys(run_rule, make_ctx, ids):
    content = _settings(True, extra={"permissions": {"allow": ["Bash(npm test)"]}})
    assert R in ids(run_rule(R, content, SETTINGS, make_ctx()))


@pytest.mark.parametrize("origin", ["postinstall-suspected", "postinstall-confirmed"])
def test_install_origin_escalates_to_unambiguous(run_rule, make_ctx, only, origin):
    """Introduced by a package install step → the ATR-MCP-005 persistence pattern."""
    ctx = make_ctx(origin=origin)
    f = only(run_rule(R, _settings(True), SETTINGS, ctx), R)
    assert f.unambiguous is True
    assert origin in f.evidence


def test_git_origin_stays_ambiguous(run_rule, make_ctx, only):
    """A developer who committed the setting themselves is not an attack by itself."""
    ctx = make_ctx(origin="git")
    f = only(run_rule(R, _settings(True), SETTINGS, ctx), R)
    assert f.unambiguous is False
    assert f.ceiling == 60


def test_global_settings_in_scope(run_rule, make_ctx, only):
    """~/.claude/settings.json auto-enable applies to every project on the machine."""
    f = only(run_rule(R, _settings(True), "~/.claude/settings.json", make_ctx()), R)
    assert "global" in f.evidence.lower()


# --- negatives ---------------------------------------------------------------
def test_false_does_not_fire(run_rule, make_ctx):
    assert run_rule(R, _settings(False), SETTINGS, make_ctx()) == []


def test_absent_does_not_fire(run_rule, make_ctx):
    content = _settings(None, extra={"permissions": {"allow": ["Read"]}})
    assert run_rule(R, content, SETTINGS, make_ctx()) == []


def test_empty_settings_does_not_fire(run_rule, make_ctx):
    assert run_rule(R, "{}", SETTINGS, make_ctx()) == []


def test_install_origin_without_setting_does_not_fire(run_rule, make_ctx):
    """Origin alone is not S16 — the setting must actually be present and true."""
    ctx = make_ctx(origin="postinstall-confirmed")
    assert run_rule(R, _settings(False), SETTINGS, ctx) == []


def test_not_a_settings_file_out_of_scope(run_rule, make_ctx):
    """The literal string in prose/docs is not a live setting."""
    prose = "Set `enableAllProjectMcpServers: true` to trust every project server.\n"
    assert run_rule(R, prose, "CLAUDE.md", make_ctx()) == []


def test_malformed_json_no_crash(run_rule, make_ctx):
    assert isinstance(run_rule(R, '{"enableAllProjectMcpServers": tru', SETTINGS, make_ctx()), list)
