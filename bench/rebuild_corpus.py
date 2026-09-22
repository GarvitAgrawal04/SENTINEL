"""Rebuild the two benchmark corpora (590 + 340 public repositories) from the committed manifests. Read-only, resumable.

    python bench/rebuild_corpus.py D:\\Repositories\\_sentinel_corpora        # creates <dir>/main and <dir>/heldout

Only the agent-config files named in the manifests are downloaded (raw.githubusercontent.com); nothing is executed. Files are
fetched at each repository's CURRENT head, so numbers can drift a little from the September 2026 snapshot: that is why
`precision_gate.py baseline` records a LOCAL baseline before any rule is changed. Keep the corpora OUTSIDE this repository.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETS = {"main": HERE / "results" / "manifest_main.json", "heldout": HERE / "results" / "manifest_heldout.json"}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    target = Path(argv[0]).resolve()
    if HERE.parent in target.parents or target == HERE.parent:
        print("error: put the corpora outside the repository (they are large and third-party).")
        return 2
    for name, manifest in SETS.items():
        out = target / name
        out.mkdir(parents=True, exist_ok=True)
        repos = json.loads(manifest.read_text(encoding="utf-8"))["repos"]
        state = out / "repos.json"
        if not state.exists():
            state.write_text(json.dumps({"repos": repos, "complete": True}), encoding="utf-8")
        print(f"== {name}: {len(repos)} repositories -> {out}")
        code = subprocess.call([sys.executable, str(HERE / "wildscan.py"), "fetch", str(out)])
        if code:
            print("fetch stopped early (rate limit or network). Run the same command again: it resumes.")
            return code
    print("\nDone. Next:  python bench/precision_gate.py baseline", target / "main", target / "heldout")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
