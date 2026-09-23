"""AGENTS.lock - build, sign, verify, approve.

Only CI signs, and only a state that is not COMPROMISED. Anyone verifies with the public key.
A valid lock means "checked", never "safe".
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from . import __version__, core

LOCK, SIG, PUBKEY = "AGENTS.lock", "AGENTS.lock.sig", ".sentinel/pubkey.pem"
CONFIG_SURFACES = (".claude/settings.json", ".claude/settings.local.json", ".gemini/settings.json",
                   ".vscode/tasks.json", ".mcp.json", ".cursor/mcp.json", ".vscode/mcp.json")
NO_FINDINGS = "100 (no findings) = 100 -> 100"


class LockRefused(Exception):
    pass


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def tracked_files(root: Path) -> list[str]:
    files = {rel(root, p) for p in core.text_surfaces(root)}
    files |= {r for r in CONFIG_SURFACES if (root / r).is_file()}
    return sorted(files)


def read_lock(root: Path) -> dict | None:
    p = root / LOCK
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (OSError, ValueError):
        return None


def approvals_of(lock: dict | None) -> dict:
    a = (lock or {}).get("approvals") or {}
    return {"autoexec": list(a.get("autoexec", [])), "mcp": list(a.get("mcp", []))}


def pending(root: Path, approvals: dict) -> dict:
    """Everything that runs or connects automatically and that nobody has approved yet."""
    ok_exec = {(a["file"], a["event"], a["command"], a.get("script_sha256")) for a in approvals.get("autoexec", [])}
    ok_mcp = set(approvals.get("mcp", []))
    autoexec = [{"file": a.file, "event": a.event, "command": a.command, "script_sha256": a.script_sha256}
                for a in core.discover_autoexec(root)
                if (a.file, a.event, a.command, a.script_sha256) not in ok_exec]
    mcp = [f"{k}={s['endpoint']}" for k, s in core.mcp_servers(root).items() if f"{k}={s['endpoint']}" not in ok_mcp]
    return {"autoexec": autoexec, "mcp": mcp}


def discover_test_cassettes(root: Path) -> list[Path]:
    """Find all recorded test cassettes used by deterministic replay tests."""
    fixture_dir = root / "tests" / "fixtures"
    if not fixture_dir.is_dir():
        return []
    cassettes: list[Path] = []
    for p in sorted(fixture_dir.glob("**/*.json")):
        if p.name == "cassette.json" or p.name.endswith(".cassette.json"):
            cassettes.append(p)
    return cassettes


def build_lock(root: Path, report: dict, approvals: dict, pin_cassettes: bool = True) -> dict:
    if report["verdict"] == "COMPROMISED":
        raise LockRefused("refusing to write a lock while anything is COMPROMISED - fix or remove it first")
    files = {}
    for r in tracked_files(root):
        p = root / r
        entry = {"sha256": core.sha256_file(p), "verdict": "CLEAN", "score": 100, "breakdown": NO_FINDINGS}
        if r in report["files"]:
            v = report["files"][r]
            entry.update(verdict=v["verdict"], score=v["score"], breakdown=v["breakdown"])
        if p in core.text_surfaces(root):
            g = core.guardrails(p.read_text(encoding="utf-8", errors="replace"))
            if g:
                entry["guardrails"] = g
        files[r] = entry

    lock_dict = {
        "version": 1,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generator": f"sentinel/{__version__}",
        "formula_version": core.FORMULA_VERSION,
        "files": files,
        "approvals": approvals_of({"approvals": approvals}),
    }
    if pin_cassettes:
        cassettes_map = {}
        for cp in discover_test_cassettes(root):
            cassettes_map[rel(root, cp)] = {
                "sha256": core.sha256_file(cp),
                "size_bytes": cp.stat().st_size,
            }
        if cassettes_map:
            lock_dict["cassettes"] = cassettes_map

    return lock_dict


def write_lock(root: Path, lock: dict, private_pem: bytes | None = None) -> None:
    (root / LOCK).write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sig = root / SIG
    if private_pem:
        sig.write_text(core.sign_lock(lock, private_pem) + "\n", encoding="utf-8")
    elif sig.exists():
        sig.unlink()                       # an edited lock must not keep a signature that no longer covers it


def approve(root: Path, only: str | None = None, note: str | None = None) -> tuple[dict, dict]:
    """Add every pending hook / MCP server (optionally filtered by substring) to the lock. Returns (lock, added).
    Refuses while the repository is COMPROMISED: an unreadable or download-and-execute hook is not approvable."""
    approvals = approvals_of(read_lock(root))
    if core.scan_repo(root, approvals)["verdict"] == "COMPROMISED":
        raise LockRefused("there is a forced finding in this repository; approval would hide it. Fix it first.")
    todo = pending(root, approvals)
    match = (lambda s: only.lower() in s.lower()) if only else (lambda s: True)
    added = {"autoexec": [dict(a, **({"approved_in": note} if note else {})) for a in todo["autoexec"]
                          if match(a["file"] + " " + a["command"])],
             "mcp": [m for m in todo["mcp"] if match(m)]}
    approvals["autoexec"] += added["autoexec"]
    approvals["mcp"] += added["mcp"]
    lock = build_lock(root, core.scan_repo(root, approvals), approvals)
    write_lock(root, lock)                 # unsigned on purpose: a human approved, CI signs after merge
    return lock, added


def _same_content(a: dict | None, b: dict) -> bool:
    strip = lambda d: {k: v for k, v in (d or {}).items() if k not in ("generated", "generator")}
    return a is not None and strip(a) == strip(b)


def sign(root: Path, private_pem: bytes) -> dict:
    """Re-scan, rebuild and sign. If nothing but the timestamp would change and the existing signature is valid for
    this key, leave both files untouched - otherwise every push to the default branch produces a noise commit."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    existing = read_lock(root)
    approvals = approvals_of(existing)
    lock = build_lock(root, core.scan_repo(root, approvals), approvals)
    sig_path = root / SIG
    if _same_content(existing, lock) and sig_path.is_file():
        public_pem = load_pem_private_key(private_pem, password=None).public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        if core.verify_lock(existing, sig_path.read_text(encoding="utf-8").strip(), public_pem):
            return existing
    write_lock(root, lock, private_pem)
    return lock


# --------------------------------------------------------------------------- keys

def keygen(private_path: Path, public_path: Path) -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
    os.chmod(private_path, 0o600)
    pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    public_path.write_bytes(pub)
    return fingerprint(pub)


def fingerprint(public_pem: bytes) -> str:
    return "SHA256:" + hashlib.sha256(b"".join(public_pem.split())).hexdigest()[:32]


def _pins_path() -> Path:
    return Path(os.environ.get("SENTINEL_HOME", Path.home() / ".config" / "sentinel")) / "known_keys.json"


def check_pin(root: Path, public_pem: bytes, remember: bool = True) -> str:
    """Trust on first use, like SSH known_hosts. Returns 'pinned' | 'first-use' | 'KEY_CHANGED'."""
    path, fp, key = _pins_path(), fingerprint(public_pem), str(root.resolve())
    try:
        pins = json.loads(path.read_text()) if path.is_file() else {}
    except ValueError:
        pins = {}
    if key in pins:
        return "pinned" if pins[key] == fp else "KEY_CHANGED"
    if remember:
        path.parent.mkdir(parents=True, exist_ok=True)
        pins[key] = fp
        path.write_text(json.dumps(pins, indent=1))
    return "first-use"


# --------------------------------------------------------------------------- verify

def verify(root: Path, public_pem: bytes | None = None, lock: dict | None = None, signature_hex: str | None = None) -> dict:
    """signature: valid | INVALID | unsigned | no-lock.   Files: changed / new / missing relative to the lock."""
    lock = lock if lock is not None else read_lock(root)
    if lock is None:
        return {"ok": False, "signature": "no-lock", "changed": [], "new": tracked_files(root), "missing": []}
    if public_pem is None and (root / PUBKEY).is_file():
        public_pem = (root / PUBKEY).read_bytes()
    if signature_hex is None and (root / SIG).is_file():
        signature_hex = (root / SIG).read_text(encoding="utf-8").strip()
    if not signature_hex or not public_pem:
        signature = "unsigned"
    else:
        signature = "valid" if core.verify_lock(lock, signature_hex, public_pem) else "INVALID"
    locked = lock.get("files", {})
    present = set(tracked_files(root))
    changed = sorted(r for r in present & set(locked) if core.sha256_file(root / r) != locked[r].get("sha256"))
    new = sorted(present - set(locked))
    missing = sorted(set(locked) - present)
    # approved hooks are pinned to a script hash: a changed script is a changed surface too
    live = {(a.file, a.event, a.command): a.script_sha256 for a in core.discover_autoexec(root)}
    stale = sorted(f"{a['file']} [{a['event']}] {a['command']}" for a in approvals_of(lock)["autoexec"]
                   if (a["file"], a["event"], a["command"]) in live
                   and a.get("script_sha256") != live[(a["file"], a["event"], a["command"])])

    # pinned test cassettes: a tampered or missing cassette fails verification
    locked_cassettes = lock.get("cassettes", {})
    tampered_cassettes = []
    missing_cassettes = []
    for r, info in locked_cassettes.items():
        cp = root / r
        if not cp.is_file():
            missing_cassettes.append(r)
        elif core.sha256_file(cp) != info.get("sha256"):
            tampered_cassettes.append(r)

    ok = signature == "valid" and not (changed or new or missing or stale or tampered_cassettes or missing_cassettes)
    return {
        "ok": ok,
        "signature": signature,
        "changed": changed,
        "new": new,
        "missing": missing,
        "stale_approvals": stale,
        "tampered_cassettes": sorted(tampered_cassettes),
        "missing_cassettes": sorted(missing_cassettes),
    }
