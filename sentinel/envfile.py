"""Load Sentinel's own .env - and only that one.

Sentinel is run inside repositories it does not trust (`sentinel run`, `sentinel scan`, `sentinel pr --detonate`).
If it loaded a `.env` from the current directory, a hostile repository could point SENTINEL_LLM_URL at its own server
and receive your API key on the next detonation. So the only file ever read is the `.env` that sits beside Sentinel's
own source tree (the folder you cloned), never the working directory, and real environment variables always win.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

OWN_ENV = Path(__file__).resolve().parent.parent / ".env"
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value)           # trailing comment on an unquoted value
        if _KEY.match(key) and value:
            out[key] = value
    return out


def load_own_env(path: Path | None = None) -> list[str]:
    """Set variables from Sentinel's own .env that are not already set. Returns the names it set."""
    path = path or OWN_ENV
    try:
        pairs = parse(path.read_text(encoding="utf-8-sig"))
    except OSError:
        return []
    fresh = [k for k in pairs if not os.environ.get(k)]
    for k in fresh:
        os.environ[k] = pairs[k]
    return fresh


def set_values(values: dict[str, str], path: Path | None = None) -> Path:
    """Write KEY=value lines into Sentinel's own .env, keeping every comment and every other line as it is.
    An empty value blanks the line (that is how a key is removed). Starts from .env.example when .env is missing."""
    path = path or OWN_ENV
    if path.is_file():
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    else:
        example = path.with_name(".env.example")
        lines = example.read_text(encoding="utf-8").splitlines() if example.is_file() else []
    left = dict(values)
    for i, line in enumerate(lines):
        m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if m and m.group(1) in left:
            lines[i] = f"{m.group(1)}={left.pop(m.group(1))}"
    lines += [f"{k}={v}" for k, v in left.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)                                   # best effort: readable by you only
    except OSError:
        pass
    return path


def read_values(path: Path | None = None) -> dict[str, str]:
    try:
        return parse((path or OWN_ENV).read_text(encoding="utf-8-sig"))
    except OSError:
        return {}
