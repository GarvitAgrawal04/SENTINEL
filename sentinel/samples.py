"""The demo files in samples/, with names a newcomer understands. Used by the API and by the web UI's saved results."""
from __future__ import annotations

from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

INFO = {                                   # file -> (title, one-line description), in the order the UI shows them
    "trapdoor_style_demo.md": ("Invisible text", "An instruction written in characters you cannot see"),
    "adversarial_injection_demo.md": ("Hidden comment", "Orders tucked inside a comment that a preview never shows"),
    "kill_shot_2_demo.md": ("Talks to the reviewer", "Tells security tools to mark the file as safe"),
    "s7_base64_payload_demo.md": ("Encoded instruction", "A block of base64 that decodes to an order"),
    "s4_s5_fastapi_env_demo.md": ("Secrets upload", "A team-sync step that sends the .env file away"),
    "s5_gemini_zero_trust_demo.md": ("Fake compliance check", "A zero-trust check that posts your configuration"),
    "s3_mcp_manifest_demo.json": ("Unknown tool server", "A tool-server config that nobody approved"),
    "clean_reference.md": ("A healthy file", "Ordinary coding guidelines, nothing to find"),
}


_verdicts: dict[str, str] = {}


def listing() -> list[dict]:
    """Title, description and the engine's verdict for each bundled sample (the UI shows it as a coloured dot)."""
    from . import contract
    out = []
    for name, (title, description) in INFO.items():
        if not (SAMPLES / name).is_file():
            continue
        if name not in _verdicts:
            _verdicts[name] = contract.scan_text(name, read(name))["verdict"]
        out.append({"file": name, "title": title, "description": description, "verdict": _verdicts[name]})
    return out


def read(name: str) -> str | None:
    """Only a bare file name from the list above: no paths, nothing outside samples/."""
    if name not in INFO or not (SAMPLES / name).is_file():
        return None
    return (SAMPLES / name).read_text(encoding="utf-8", errors="replace")
