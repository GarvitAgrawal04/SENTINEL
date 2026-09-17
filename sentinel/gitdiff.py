"""Base-vs-head plumbing. Shells out to git; no git library."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import core, lock as lockmod

AGENT_WORDS = re.compile(r"claude|cursor|agent|gemini|copilot|mcp|hook|rules?\b|skill|sentinel|prompt|instruction", re.I)


def git(root: Path, *args: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def show(root: Path, ref: str, path: str) -> str | None:
    return git(root, "show", f"{ref}:{path}")


def changed_files(root: Path, base: str) -> list[str]:
    """Committed changes since the merge-base, plus anything uncommitted or untracked (so it works before a commit too)."""
    out = set()
    for args in (("diff", "--name-only", f"{base}...HEAD"), ("diff", "--name-only", "HEAD"),
                 ("ls-files", "--others", "--exclude-standard")):
        out |= set((git(root, *args) or "").split())
    return sorted(out)


def is_agent_surface(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (path in lockmod.CONFIG_SURFACES or path in core.TEXT_SURFACES or name == "SKILL.md"
            or (path.startswith(".cursor/rules/") and path.endswith(".mdc")) or path in (lockmod.LOCK, lockmod.SIG))


def baseline_texts(root: Path, base: str) -> dict[str, str]:
    """The trusted version of every instruction file that exists in base. Feeds S20 and detonation."""
    out = {}
    for p in core.text_surfaces(root):
        r = lockmod.rel(root, p)
        old = show(root, base, r)
        if old is not None:
            out[r] = old
    return out


def base_trust(root: Path, base: str) -> tuple[dict, str]:
    """Approvals come from the BASE branch's lock, checked with the BASE branch's key:
    a pull request cannot approve itself or swap the key it is judged by."""
    raw = show(root, base, lockmod.LOCK)
    if raw is None:
        return {"autoexec": [], "mcp": []}, "no-lock"
    try:
        lock = json.loads(raw)
    except ValueError:
        return {"autoexec": [], "mcp": []}, "unreadable-lock"
    sig, pub = show(root, base, lockmod.SIG), show(root, base, lockmod.PUBKEY)
    if not sig or not pub:
        return lockmod.approvals_of(lock), "unsigned"
    if core.verify_lock(lock, sig.strip(), pub.encode()):
        return lockmod.approvals_of(lock), "valid"
    return {"autoexec": [], "mcp": []}, "INVALID-signature"


def undeclared_change(root: Path, base: str, touched: list[str]) -> core.Finding | None:
    """S6: the PR changes what the agent obeys, and no commit message says so (Miasma: 'Switched DataConverter...')."""
    surfaces = [t for t in touched if is_agent_surface(t) and t not in (lockmod.LOCK, lockmod.SIG)]
    subjects = [s for s in (git(root, "log", "--format=%s", f"{base}..HEAD") or "").splitlines() if s.strip()]
    if not surfaces or not subjects or any(AGENT_WORDS.search(s) for s in subjects):
        return None
    return core.Finding("S6", surfaces[0], 15,
        evidence=f"{len(surfaces)} agent-config file(s) changed; commit messages mention none of them: "
                 + "; ".join(f'"{s[:60]}"' for s in subjects[:3]),
        impact="What your agent obeys changed inside a change that claims to be about something else.",
        fix="Ask the author why. Legitimate edits to agent instructions are worth a line in the commit message.")


def requested_approvals(root: Path, base_approvals: dict) -> dict:
    """Approvals that exist in this branch's lock but not in base: a human is being asked to accept them."""
    head = lockmod.approvals_of(lockmod.read_lock(root))
    key = lambda a: (a["file"], a["event"], a["command"], a.get("script_sha256"))
    have = {key(a) for a in base_approvals.get("autoexec", [])}
    return {"autoexec": [a for a in head["autoexec"] if key(a) not in have],
            "mcp": [m for m in head["mcp"] if m not in set(base_approvals.get("mcp", []))]}
