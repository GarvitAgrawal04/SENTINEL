"""Write frontend/saved-results.json: what the engine returns for each bundled sample.

    python demo/save_sample_results.py

The web UI uses this file only when no scanner is reachable (for example a static demo site whose API is asleep),
and says so on screen. A test fails if this file drifts from what the engine returns today.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sentinel import contract, samples  # noqa: E402


def build() -> dict:
    out = []
    for s in samples.listing():
        text = samples.read(s["file"])
        out.append({**s, "text": text, "result": contract.scan_text(s["file"], text)})
    return {"samples": out}


if __name__ == "__main__":
    target = ROOT / "frontend" / "saved-results.json"
    target.write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)} ({len(build()['samples'])} samples)")
