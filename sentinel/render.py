"""Human output. The CLI text lives in core.render; this is the pull-request comment."""
from __future__ import annotations

TITLE = {
    "S1a": "HIDDEN TEXT", "S1b": "STRAY INVISIBLE CHARACTERS", "S5": "EXFILTRATION-SHAPED INSTRUCTION",
    "S6": "UNDECLARED CHANGE", "S10": "ORPHANED AUTO-RUN", "S13": "CONCEALMENT FROM THE USER",
    "S14b": "WRITE-INTERCEPT HOOK, NOT APPROVED", "S17a": "NEW AUTO-RUN, NOT APPROVED", "S17b": "AUTO-RUN ACROSS SEVERAL TOOLS",
    "S18a": "THE AUTO-RUN SCRIPT IS UNREADABLE", "S18b": "THE AUTO-RUN SCRIPT CAN SPAWN AND CONNECT",
    "S18c": "DOWNLOAD-AND-EXECUTE", "S19": "NEW MCP SERVER, NOT APPROVED", "S20": "GUARDRAIL WEAKENED",
    "D1": "IN THE SANDBOX, A PLANTED SECRET LEFT THE MACHINE", "D2": "IN THE SANDBOX, NEW SENSITIVE BEHAVIOUR",
}
BADGE = {"CLEAN": "🟢 CLEAN", "SUSPICIOUS": "🟡 SUSPICIOUS", "COMPROMISED": "🔴 COMPROMISED"}
MARKER = "<!-- sentinel-agent-behaviour-diff -->"


def pr_comment(report: dict, ctx: dict) -> str:
    """ctx: base, changed (agent-config files touched), trust (state of the base lock), requested (approvals asked for)."""
    lines = [MARKER, f"## 🛡 Sentinel — agent behaviour diff &nbsp; {BADGE[report['verdict']]}", ""]
    changed = ctx.get("changed") or []
    if changed:
        lines.append("This pull request changes what AI coding agents will do in this repository: "
                     + ", ".join(f"`{c}`" for c in changed) + ".")
    else:
        lines.append("This pull request does not touch any file an AI coding agent obeys.")
    lines.append("")
    n = 0
    order = sorted(report["files"].items(), key=lambda kv: kv[1]["score"])
    for name, v in order:
        for f in v["findings"]:
            n += 1
            tag = "forced" if f["force"] else "needs approval" if f["ceiling"] else f"−{f['penalty']}"
            lines += [f"**{n}. {TITLE.get(f['rule'], f['rule'])}** &nbsp; `{f['rule']}` · {tag} · `{name}`",
                      f"> {f['impact']}", f"> <sub>evidence: {f['evidence']}</sub>", ""]
    if not n:
        lines += ["No findings. That means *checked*, not *safe*.", ""]
    req = ctx.get("requested") or {}
    if req.get("autoexec") or req.get("mcp"):
        lines.append("**Approvals requested in this PR** — merging accepts these; a security owner should be the one to click:")
        lines += [f"- auto-run `{a['command']}` on `{a['event']}` ({a['file']})" for a in req.get("autoexec", [])]
        lines += [f"- MCP server `{m}`" for m in req.get("mcp", [])]
        lines.append("")
    if order:
        lines.append("<details><summary>Score arithmetic</summary>\n")
        lines += [f"- `{name}` — {v['breakdown']} → **{v['verdict']}**" for name, v in order]
        lines.append("\n</details>\n")
    fixes = []
    for _, v in order:
        for f in v["findings"]:
            if f["fix"] not in fixes:
                fixes.append(f["fix"])
    if fixes:
        lines.append("**Next**")
        lines += [f"- {x}" for x in fixes[:5]]
        lines.append("")
    trust = ctx.get("trust", "no-lock")
    note = {"valid": "Approvals were read from the base branch's `AGENTS.lock` (signature valid).",
            "unsigned": "The base branch has an `AGENTS.lock` but it is not signed; approvals in it were honoured. Sign it in CI.",
            "no-lock": "The base branch has no `AGENTS.lock`, so every hook and MCP server counts as unapproved. Run `sentinel init`.",
            "INVALID-signature": "⚠ The base branch's `AGENTS.lock` has an INVALID signature. No approval in it was honoured.",
            "unreadable-lock": "⚠ The base branch's `AGENTS.lock` could not be parsed. No approval in it was honoured."}[trust]
    lines.append(f"<sub>{note} Formula v{report['formula_version']}. A model's behaviour can turn a file yellow; "
                 f"only deterministic evidence turns it red.</sub>")
    return "\n".join(lines) + "\n"
