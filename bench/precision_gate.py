"""The hard gate for every rule change: what does the engine say about ~930 REAL, healthy repositories?

    python bench/precision_gate.py baseline CORPUS_DIR [CORPUS_DIR ...] [--out FILE]     # before you touch a rule
    python bench/precision_gate.py check    CORPUS_DIR [CORPUS_DIR ...] [--baseline FILE] # after; exit 1 on a regression

A regression is: any repository COMPROMISED, or any SCORED finding from a text rule that the baseline did not have, or a
repository whose verdict got worse. Observations (penalty 0) and approval requests never count. If a new finding is CORRECT
(you looked at the file and it really is dangerous), re-run with --accept "repo: reason" and commit the reason in bench/.
Offline. Corpora come from `python bench/rebuild_corpus.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sentinel import core  # noqa: E402

INVENTORY = {"S14b", "S16", "S17a", "S19"}                      # "please approve this once": a question, not an accusation
RANK = {"CLEAN": 0, "SUSPICIOUS": 1, "COMPROMISED": 2}
DEFAULT_BASELINE = Path(__file__).resolve().parent / "results" / "gate_baseline.local.json"


def run(dirs: list[str]) -> dict:
    started = time.time()
    repos: dict[str, dict] = {}
    for corpus in dirs:
        for d in sorted(Path(corpus).iterdir()):
            if not d.is_dir():
                continue
            rep = core.scan_repo(d)
            scored = sorted({f"{f['rule']}|{f['file']}|{f['evidence'][:160]}" for v in rep["files"].values() for f in v["findings"]
                             if f["penalty"] > 0 and f["rule"] not in INVENTORY})
            repos[d.name] = {"verdict": rep["verdict"], "scored": scored}
    counts: dict[str, int] = {}
    for r in repos.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"engine": core.__dict__.get("FORMULA_VERSION", ""), "repos": repos, "counts": counts,
            "with_scored_findings": sum(1 for r in repos.values() if r["scored"]), "seconds": round(time.time() - started, 1)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["baseline", "check"])
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", default=str(DEFAULT_BASELINE))
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    ap.add_argument("--accept", action="append", default=[], help='"repo-folder-name: why this new finding is correct"')
    a = ap.parse_args()
    now = run(a.dirs)
    print(f"{len(now['repos'])} repositories in {now['seconds']} s · verdicts {now['counts']} · with a scored claim: {now['with_scored_findings']}")
    if a.mode == "baseline":
        Path(a.out).write_text(json.dumps(now, indent=1), encoding="utf-8")
        print(f"baseline written to {a.out} (local file, not committed). Copy the line above into docs/build/PROGRESS.md.")
        return 1 if now["counts"].get("COMPROMISED") else 0
    base = json.loads(Path(a.baseline).read_text(encoding="utf-8"))["repos"]
    accepted = {x.split(":", 1)[0].strip() for x in a.accept}
    problems = []
    for name, r in now["repos"].items():
        old = base.get(name, {"verdict": "CLEAN", "scored": []})
        if r["verdict"] == "COMPROMISED":
            problems.append(f"COMPROMISED  {name}")
        elif RANK[r["verdict"]] > RANK[old["verdict"]] and name not in accepted:
            problems.append(f"WORSE        {name}: {old['verdict']} -> {r['verdict']}")
        for s in r["scored"]:
            if s not in old["scored"] and name not in accepted:
                problems.append(f"NEW FINDING  {name}: {s}")
    fixed = sum(1 for name, old in base.items() if name in now["repos"] and RANK[now["repos"][name]["verdict"]] < RANK[old["verdict"]])
    print(f"better than baseline: {fixed} repositories · regressions: {len(problems)}")
    for p in problems[:40]:
        print("  " + p)
    print("GATE: " + ("PASS" if not problems else "FAIL  (read each line above; a correct new finding needs --accept and a written reason)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
