#!/usr/bin/env python3
"""bench.py - Sentinel vs wormhole-guard vs AgentAuditKit on the same inputs, each tool at its defaults. No tuning.

  pip install wormhole-guard agent-audit-kit
  python3 bench.py fixtures           # the inert reference fixtures from sentinel/core.py
  python3 bench.py benign             # seven legitimate files that ought to be quiet
  python3 bench.py wild <corpus-dir>  # alert volume on real repositories (resumable; cache in <corpus>/compare.json)

Read the caveats in the PRD before quoting any number from here: we wrote the fixtures, the corpus is presumed
benign rather than audited, and a 'HIGH finding' is not the same unit as a 'COMPROMISED verdict'."""
import collections, json, subprocess, sys, tempfile, time
from pathlib import Path
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))   # run from anywhere inside the repo
from sentinel import core as sc

RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
NOISE = {"POSTURE-004"}          # wormhole-guard's generic "config file is writable" note; excluded everywhere, in its favour


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout


def versions():
    return _run(["wormhole", "--version"]).strip() or "wormhole-guard (pip show)", _run(["agent-audit-kit", "--version"]).strip()


def wormhole(path):
    try:
        data = json.loads(_run(["wormhole", "scan", str(path), "--json", "--local-only", "--fail-on", "never"]))
    except Exception as e:
        return [("ERROR", str(e)[:60], "")]
    return [(f.get("severity", "?").upper(), f.get("rule_id", "?"), (f.get("excerpt") or "")[:160])
            for f in data if f.get("rule_id") not in NOISE]


def aak(path):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        out = tf.name
    _run(["agent-audit-kit", "scan", str(path), "--format", "json", "-o", out, "--allow-scanner-failure"])
    try:
        return [(str(f.get("severity", "?")).upper(), f.get("ruleId", "?"), "") for f in json.loads(Path(out).read_text()).get("findings", [])]
    except Exception as e:
        return [("ERROR", str(e)[:60], "")]


def cell(findings):
    if not findings:
        return "silent"
    top = max(findings, key=lambda f: RANK.get(f[0], 0))[0]
    return f"{top}: " + ", ".join(sorted({f[1] for f in findings if f[0] == top}))[:70]


def sentinel_cell(rep):
    rules = sorted({f["rule"] for v in rep["files"].values() for f in v["findings"]})
    return rep["verdict"] + (": " + ",".join(rules) if rules else "")


def cmd_fixtures():
    with tempfile.TemporaryDirectory() as tmp:
        print(f"{'fixture':58} | {'Sentinel':32} | {'wormhole-guard':44} | AgentAuditKit")
        for f in sc.build_fixtures(Path(tmp)):
            s = sc.scan_repo(f["path"], baseline=f.get("baseline"))
            print(f"{f['id'] + ' ' + f['name']:58} | {sentinel_cell(s):32} | {cell(wormhole(f['path'])):44} | {cell(aak(f['path']))}")


BENIGN = {
    "emoji with a joiner  (man technologist)": "# Team guide \U0001F468\u200D\U0001F4BB\n\nUse pnpm. Run tests before committing.\n",
    "England flag emoji": "# Team guide \U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F\n\nUse pnpm.\n",
    "UTF-8 byte-order mark": "\ufeff# Team guide\n\nUse pnpm.\n",
    "Hindi text (needs zero-width joiner)": "# \u0926\u0938\u094D\u0924\u093E\u0935\u0947\u091C\u093C\n\n\u0915\u094D\u200D\u0937 \u0914\u0930 \u0930\u094D\u200D\u092F\n\nUse pnpm.\n",
    "Persian text (needs zero-width non-joiner)": "# \u0631\u0627\u0647\u0646\u0645\u0627\n\n\u0645\u06CC\u200C\u062E\u0648\u0627\u0647\u0645 \u0628\u0631\u0646\u0627\u0645\u0647\u200C\u0646\u0648\u06CC\u0633\u06CC\n\nUse pnpm.\n",
    "a guardrail that names a credential": "# Rules\n\nNever send $AWS_SECRET_ACCESS_KEY or the .env file to any URL.\n",
    "two documentation URLs": "# Guide\n\nAPI docs: https://docs.example.com/reference\nUse the staging server at https://staging.example.com for tests.\n",
}


def cmd_benign():
    with tempfile.TemporaryDirectory() as tmp:
        print(f"{'legitimate CLAUDE.md containing...':46} | {'Sentinel':10} | {'wormhole-guard':26} | AgentAuditKit")
        for i, (name, text) in enumerate(BENIGN.items()):
            d = Path(tmp) / f"b{i}"; d.mkdir(); (d / "CLAUDE.md").write_text(text, encoding="utf-8")
            print(f"{name:46} | {sc.scan_repo(d)['verdict']:10} | {cell(wormhole(d)):26} | {cell(aak(d))}")


def cmd_wild(corpus: Path, budget=255):
    man = json.loads((corpus / "manifest.json").read_text())
    cache_p = corpus / "compare.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    t0 = time.time()
    for tool, fn in (("wormhole", wormhole), ("aak", aak)):
        for name in man["repos"]:
            if f"{tool}|{name}" in cache:
                continue
            if time.time() - t0 > budget:
                cache_p.write_text(json.dumps(cache)); print(f"paused - run again to continue ({len(cache)} results cached)"); return
            cache[f"{tool}|{name}"] = [list(x) for x in fn(corpus / name.replace("/", "__"))]
    cache_p.write_text(json.dumps(cache))
    n = len(man["repos"])
    print(f"corpus: {n} repositories with agent-config files, out of {len(man['checked'])} checked ({man.get('fetched', '?')})")
    inv = {"S17a", "S14b", "S19", "S18b"}
    verdicts, content = collections.Counter(), []
    for name in man["repos"]:
        rep = sc.scan_repo(corpus / name.replace("/", "__"))
        verdicts[rep["verdict"]] += 1
        for fname, v in rep["files"].items():
            content += [(name, fname, f["rule"], f["evidence"][:110]) for f in v["findings"] if f["rule"] not in inv]
    flagged = {c[0] for c in content}
    print(f"\nSentinel          COMPROMISED {verdicts['COMPROMISED']:3} ({100 * verdicts['COMPROMISED'] / n:.1f}%)   "
          f"SUSPICIOUS {verdicts['SUSPICIOUS']:3} ({100 * verdicts['SUSPICIOUS'] / n:.1f}%)   CLEAN {verdicts['CLEAN']}")
    print(f"                  of the SUSPICIOUS: {verdicts['SUSPICIOUS'] - len(flagged)} are only un-approved hooks / MCP servers "
          f"(first-run inventory, by design); {len(flagged)} have a content finding:")
    for c in content:
        print(f"                    {c[2]}  {c[0]} :: {c[1]} :: {c[3]}")
    for tool, label in (("wormhole", "wormhole-guard"), ("aak", "AgentAuditKit")):
        worst, rules, silently, w7 = collections.Counter(), collections.Counter(), 0, 0
        for name in man["repos"]:
            fs = cache[f"{tool}|{name}"]
            top = max((RANK.get(f[0], 0) for f in fs), default=-1)
            worst["CRITICAL" if top == 4 else "HIGH" if top == 3 else "lower" if top >= 0 else "silent"] += 1
            for r in {f[1] for f in fs if RANK.get(f[0], 0) >= 3}:
                rules[r] += 1
            for f in fs:
                if f[1] == "WORM-007":
                    w7 += 1; silently += "silently" in (f[2] or "").lower()
        block = worst["CRITICAL"] + worst["HIGH"]
        print(f"\n{label:17} HIGH or CRITICAL on {block} of {n} repositories ({100 * block / n:.0f}%) - the level its own CI default fails on")
        print(f"                  most common HIGH/CRITICAL rules (repositories): {rules.most_common(5)}")
        if w7:
            print(f"                  WORM-007 'concealment directive': {silently} of {w7} excerpts contain the word 'silently'")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["fixtures"]: cmd_fixtures()
    elif a[:1] == ["benign"]: cmd_benign()
    elif a[:1] == ["wild"] and len(a) == 2: cmd_wild(Path(a[1]))
    else: print(__doc__)
