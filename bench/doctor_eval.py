"""Benchmark script: Evaluate doctor checks D001–D008 across public repositories.

Measures the hit-rate of each deterministic check on real-world repositories to ensure
healthy repositories are not bombarded with warnings.
Any check firing on >5% of healthy repos is classified as an OBSERVATION rather than a WARNING.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sentinel.doctor import lints, graph

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = Path(__file__).resolve().parent / "results"

KNOWN_AGENT_FILES = (
    "claude.md",
    ".cursorrules",
    "agents.md",
    ".claude/settings.json",
    ".github/copilot-instructions.md",
)


def find_agent_files(repo_path: Path) -> list[Path]:
    """Find instruction files an agent obeys within a repository."""
    found: list[Path] = []
    # Check top-level known files
    for name in ("CLAUDE.md", ".cursorrules", "AGENTS.md", "GEMINI.md"):
        cand = repo_path / name
        if cand.is_file():
            found.append(cand)

    copilot = repo_path / ".github" / "copilot-instructions.md"
    if copilot.is_file():
        found.append(copilot)

    # Subdirectory rules
    cursor_rules = repo_path / ".cursor" / "rules"
    if cursor_rules.is_dir():
        for f in cursor_rules.iterdir():
            if f.is_file() and f.suffix in (".md", ".mdc"):
                found.append(f)

    return found


def evaluate_repositories(repo_dirs: list[Path]) -> dict[str, Any]:
    """Run D001–D008 across provided repositories and return hit rates."""
    check_hits: dict[str, int] = {f"D00{i}": 0 for i in range(1, 9)}
    repos_with_agent_files = 0
    total_repos_inspected = 0
    repo_results: dict[str, dict[str, int]] = {}

    start_time = time.time()

    for r_dir in sorted(repo_dirs):
        if not r_dir.is_dir() or r_dir.name.startswith("."):
            continue

        total_repos_inspected += 1
        agent_files = find_agent_files(r_dir)
        if not agent_files:
            continue

        repos_with_agent_files += 1
        repo_fired: set[str] = set()

        for af in agent_files:
            findings = lints.check_file(af, root=r_dir)
            for f in findings:
                repo_fired.add(f["id"])

        for cid in repo_fired:
            check_hits[cid] = check_hits.get(cid, 0) + 1

        repo_results[r_dir.name] = {cid: (1 if cid in repo_fired else 0) for cid in check_hits}

    elapsed = round(time.time() - start_time, 2)

    denominator = max(1, repos_with_agent_files)
    hit_rates: dict[str, float] = {}
    classifications: dict[str, str] = {}

    for cid, count in sorted(check_hits.items()):
        rate = count / denominator
        hit_rates[cid] = round(rate, 4)
        classifications[cid] = "OBSERVATION" if rate > 0.05 else "WARNING"

    return {
        "total_repos_inspected": total_repos_inspected,
        "repos_with_agent_files": repos_with_agent_files,
        "elapsed_seconds": elapsed,
        "check_hits": check_hits,
        "hit_rates": hit_rates,
        "classifications": classifications,
    }


def main() -> int:
    # Scan D:\Repositories parent directory for real public repos
    parent_dir = Path("D:/Repositories")
    if not parent_dir.is_dir():
        print(f"Directory {parent_dir} not found. Running on sample set.")
        target_dirs = [ROOT]
    else:
        target_dirs = [p for p in parent_dir.iterdir() if p.is_dir() and p != ROOT]

    print(f"Evaluating D001–D008 across {len(target_dirs)} repositories in {parent_dir}...")
    results = evaluate_repositories(target_dirs)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / "doctor_hit_rates.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Generate markdown report
    md_lines = [
        "# Instruction Doctor Hit-Rate Evaluation",
        "",
        f"- **Repositories Inspected:** {results['total_repos_inspected']}",
        f"- **Repositories with Agent Instruction Files:** {results['repos_with_agent_files']}",
        f"- **Evaluation Runtime:** {results['elapsed_seconds']} s",
        "",
        "## Check Prevalence and Classification (>5% = OBSERVATION)",
        "",
        "| Check ID | Description | Hits | Hit Rate (%) | Status |",
        "|---|---|---|---|---|",
    ]

    descriptions = {
        "D001": "Broken @include / @import target",
        "D002": "Backticked path does not exist",
        "D003": "Named script not in manifests",
        "D004": "Normalized duplicate rule",
        "D005": "Rule contradicts guardrail",
        "D006": "File over token budget (>1500)",
        "D007": "Secret-shaped value in instructions",
        "D008": "ANSI terminal escape sequence",
    }

    for cid, rate in results["hit_rates"].items():
        hits = results["check_hits"][cid]
        pct = round(rate * 100, 2)
        status = results["classifications"][cid]
        md_lines.append(f"| **{cid}** | {descriptions.get(cid, '')} | {hits} | {pct}% | **{status}** |")

    report_path = RESULTS_DIR / "doctor_eval.md"
    report_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Results written to {out_file} and {report_path}")
    print("\nPrevalence:")
    for cid, rate in results["hit_rates"].items():
        print(f"  {cid}: {results['check_hits'][cid]}/{results['repos_with_agent_files']} ({rate*100:.1f}%) -> {results['classifications'][cid]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
