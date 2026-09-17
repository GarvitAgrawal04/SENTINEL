#!/usr/bin/env python3
"""wildscan.py - build a real-world corpus of agent-config files from popular public repos (read-only, public data).

  python3 wildscan.py search corpus/ [--max 1500] [--set heldout --exclude corpus/]
                                                     # GitHub repo search, no token needed. Resumable: re-run until "complete"
  python3 wildscan.py fetch  corpus/                 # raw file fetch. Resumable: re-run until all repos are checked
  python3 bench.py wild corpus/                      # then compare the three tools on it

Set GITHUB_TOKEN to raise rate limits. Only a fixed list of agent-config paths (and the scripts their hooks
point at) is downloaded. Nothing is executed."""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sentinel_core as sc

PRIMARY = ["CLAUDE.md", "AGENTS.md", ".cursorrules", ".claude/settings.json", ".mcp.json"]
SECONDARY = ["GEMINI.md", ".github/copilot-instructions.md", ".gemini/settings.json", ".vscode/tasks.json",
             ".cursor/mcp.json", ".vscode/mcp.json", ".claude/settings.local.json"]
SETS = {   # `main` is the set the rules were tightened against. `heldout` was never looked at while writing rules.
    "main": ["stars:>8000 pushed:>2026-06-01", "stars:3000..8000 pushed:>2026-07-01", "topic:claude-code stars:>50",
             "topic:mcp stars:>200", "topic:ai-agents stars:>500", "topic:cursor stars:>100"],
    "heldout": ["stars:1200..2999 pushed:>2026-08-01", "topic:llm stars:300..2999", "topic:developer-tools stars:300..2999",
                "topic:agents stars:100..2999", "topic:typescript stars:1500..2999 pushed:>2026-08-15"],
}
QUERIES = SETS["heldout" if "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "heldout" else "main"]
EXCLUDE = set()
if "--exclude" in sys.argv:                                  # skip repositories already present in another corpus
    EXCLUDE = set(json.loads((Path(sys.argv[sys.argv.index("--exclude") + 1]) / "repos.json").read_text())["repos"])
HDR = {"User-Agent": "sentinel-wildscan/0.1 (research; read-only)"}
if os.environ.get("GITHUB_TOKEN"): HDR["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

def get(url, timeout=20):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, b""
    except Exception: return 0, b""

def cmd_search(out, max_repos, budget=240):
    """Resumable and time-budgeted: run it again to continue where it stopped."""
    out.mkdir(parents=True, exist_ok=True)
    state_p = out / "repos.json"
    state = json.loads(state_p.read_text()) if state_p.exists() else {"done": [], "repos": {}}
    t0 = time.time()
    for q in QUERIES:
        for page in range(1, 11):
            key = f"{q}|{page}"
            if key in state["done"] or len(state["repos"]) >= max_repos: continue
            if time.time() - t0 > budget:
                state_p.write_text(json.dumps(state)); print(f"paused: {len(state['repos'])} repos so far"); return
            code, body = get("https://api.github.com/search/repositories?" + urllib.parse.urlencode(
                {"q": q, "sort": "stars", "order": "desc", "per_page": 100, "page": page}))
            if code in (403, 429): time.sleep(20); continue
            items = json.loads(body).get("items", []) if code == 200 else []
            for it in items:
                if not it.get("fork") and not it.get("archived") and it["full_name"] not in EXCLUDE:
                    state["repos"].setdefault(it["full_name"], {"branch": it["default_branch"], "stars": it["stargazers_count"]})
            state["done"].append(key)
            if len(items) < 100:
                state["done"] += [f"{q}|{p}" for p in range(page + 1, 11)]
            time.sleep(6.2)                                   # unauthenticated search: 10 requests/minute
    state_p.write_text(json.dumps(state)); print(f"search complete: {len(state['repos'])} repos")

def fetch_repo(args):
    name, meta, out = args
    base = f"https://raw.githubusercontent.com/{name}/{meta['branch']}/"
    d = out / name.replace("/", "__"); got = []
    def grab(path):
        if len(path) > 200 or ".." in path or path.startswith(("/", "~")): return False
        code, body = get(base + urllib.parse.quote(path))
        if code == 200 and body and len(body) < 2_000_000:
            p = d / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(body); got.append(path); return True
        return False
    if not any([grab(p) for p in PRIMARY]): return name, []
    for p in SECONDARY: grab(p)
    for ae in sc.discover_autoexec(d):                        # fetch hook targets so S10/S18 judge the real script
        if ae.script and not ae.script_exists: grab(ae.script)
    return name, got

def cmd_fetch(out, budget=250):
    """Resumable and time-budgeted."""
    repos = json.loads((out / "repos.json").read_text())["repos"]
    man_p = out / "manifest.json"
    man = json.loads(man_p.read_text()) if man_p.exists() else {"checked": [], "repos": {}}
    todo = [(n, m, out) for n, m in repos.items() if n not in set(man["checked"])]
    t0 = time.time()
    with ThreadPoolExecutor(24) as ex:
        for start in range(0, len(todo), 96):
            if time.time() - t0 > budget: break
            for name, got in ex.map(fetch_repo, todo[start:start + 96]):
                man["checked"].append(name)
                if got: man["repos"][name] = {**repos[name], "files": got}
            man["fetched"] = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
            man_p.write_text(json.dumps(man, indent=1))
    print(f"checked {len(man['checked'])}/{len(repos)} repos; {len(man['repos'])} have agent-config files")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        cmd_search(Path(sys.argv[2]), int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 1500)
    elif len(sys.argv) >= 3 and sys.argv[1] == "fetch":
        cmd_fetch(Path(sys.argv[2]))
    else: print(__doc__)
