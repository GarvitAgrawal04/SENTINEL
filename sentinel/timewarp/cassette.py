"""Cassette format for recording and replaying model interactions during sandbox detonation.

Offline, deterministic, key-free:
  - Key = sha256 of JSON-serialized messages list (redacted).
  - Value = model's response dictionary (redacted).
  - Replay raises CassetteMissError on unseen inputs (fails loudly in CI).
  - All stored strings are redacted via sentinel.core.redact.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from sentinel import core


class CassetteMissError(KeyError):
    """Raised when a prompt/message sequence is not found in the cassette during replay."""


def _redact_data(val: Any) -> Any:
    if isinstance(val, str):
        return core.redact(val)
    elif isinstance(val, dict):
        return {k: _redact_data(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_redact_data(v) for v in val]
    return val


def hash_messages(messages: list[dict]) -> str:
    """Compute deterministic SHA256 of canonical JSON-serialized messages."""
    redacted = _redact_data(messages)
    payload = json.dumps(redacted, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CassetteRecorder:
    """Wraps a model and records every step into a cassette."""

    def __init__(self, model: Any, cassette: Cassette, path: Path | str | None = None) -> None:
        self.model = model
        self.cassette = cassette
        self.path = Path(path) if path else None

    def step(self, messages: list[dict]) -> dict:
        key = hash_messages(messages)
        res = self.model.step(messages)
        redacted_res = _redact_data(copy.deepcopy(res))
        self.cassette.entries[key] = redacted_res
        if self.path:
            self.cassette.save(self.path)
        return res

    def save(self, path: Path | str | None = None) -> None:
        self.cassette.save(path or self.path)


class Cassette:
    """A collection of recorded model responses keyed by message-history hash."""

    def __init__(self, entries: dict[str, dict] | None = None, path: Path | str | None = None) -> None:
        self.entries: dict[str, dict] = copy.deepcopy(entries) if entries else {}
        self.path = Path(path) if path else None

    @classmethod
    def record(cls, model: Any, path: Path | str | None = None) -> CassetteRecorder:
        """Wrap a model with a CassetteRecorder that records model calls as they happen."""
        cassette = cls(path=path)
        if path and Path(path).is_file():
            cassette.load(path)
        return CassetteRecorder(model=model, cassette=cassette, path=path)

    @classmethod
    def replay(cls, path: Path | str) -> Cassette:
        """Load a cassette from file and return a replayer model instance."""
        cassette = cls(path=path)
        cassette.load(path)
        return cassette

    def load(self, path: Path | str) -> None:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Cassette file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], dict):
            self.entries = data["entries"]
        elif isinstance(data, dict):
            self.entries = data
        else:
            raise ValueError(f"Invalid cassette format in {p}")
        self.path = p

    def save(self, path: Path | str | None = None) -> None:
        target = Path(path) if path else self.path
        if not target:
            raise ValueError("No path specified to save cassette.")
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "entries": self.entries}
        target.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    def step(self, messages: list[dict]) -> dict:
        """Replay model call: looks up messages hash in cassette."""
        key = hash_messages(messages)
        if key not in self.entries:
            raise CassetteMissError(
                f"Cassette replay miss: message sequence (hash {key}) not found in cassette {self.path or '<memory>'}. "
                "Ensure cassette was recorded with matching messages or prompts."
            )
        return copy.deepcopy(self.entries[key])
