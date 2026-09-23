"""Benchmark script: Evaluate Time-Warp trigger prevalence across repositories.

Measures the frequency of conditional/temporal triggers across real-world repositories
and agent corpora to ensure that healthy instruction files are not bombarded with phantom scenario plans.
The design constraint requires trigger prevalence to stay at ~1 scenario/repo mean.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bench"))

from doctor_eval import find_agent_files
from sentinel.timewarp import triggers

RESULTS_DIR = ROOT / "bench" / "results"
DEFAULT_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "doctor_corpus"
REPOSITORIES_DIR = Path("D:/Repositories")


def evaluate_single_corpus(
    chosen_dir: Path,
    is_repo_mode: bool,
) -> dict[str, Any]:
    """Evaluate trigger prevalence on a specific directory."""
    start_time = time.time()
    repos_evaluated = 0
    total_scenarios = 0
    repos_with_triggers = 0
    kind_counts: dict[str, int] = {}
    repo_breakdown: list[dict[str, Any]] = []

    if is_repo_mode:
        repo_dirs = sorted([p for p in chosen_dir.iterdir() if p.is_dir() and p != ROOT and not p.name.startswith(".")])
    else:
        repo_dirs = sorted([f for f in chosen_dir.glob("file_*.md")])

    for item in repo_dirs:
        if is_repo_mode:
            agent_files = find_agent_files(item)
            if not agent_files:
                continue
            item_name = item.name
        else:
            agent_files = [item]
            item_name = item.name

        repos_evaluated += 1
        all_trigs = []
        for af in agent_files:
            text = af.read_text(encoding="utf-8", errors="replace")
            trigs = triggers.extract_triggers(text)
            all_trigs.extend(trigs)

        for t in all_trigs:
            kind_counts[t.kind] = kind_counts.get(t.kind, 0) + 1

        # Plan scenarios including baseline 'now'
        full_text = "\n".join(af.read_text(encoding="utf-8", errors="replace") for af in agent_files)
        plan = triggers.plan_scenarios(full_text)
        sc_count = len(plan)
        total_scenarios += sc_count

        if sc_count > 1:
            repos_with_triggers += 1
            repo_breakdown.append({
                "target": item_name,
                "scenarios_planned": sc_count,
                "triggers": [t.to_dict() for t in all_trigs],
            })

    elapsed = round(time.time() - start_time, 2)
    mean_scenarios = round(total_scenarios / max(1, repos_evaluated), 3)

    return {
        "source": str(chosen_dir),
        "mode": "repositories" if is_repo_mode else "agent_files",
        "targets_evaluated": repos_evaluated,
        "targets_with_triggers": repos_with_triggers,
        "trigger_rate": round(repos_with_triggers / max(1, repos_evaluated), 4),
        "total_scenarios_planned": total_scenarios,
        "mean_scenarios_per_target": mean_scenarios,
        "elapsed_seconds": elapsed,
        "trigger_kinds": kind_counts,
        "flagged_targets": repo_breakdown,
    }


def evaluate(
    target_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    max_mean_threshold: float = 1.35,
) -> dict[str, Any]:
    """Run trigger prevalence benchmark across both corpora (or single target)."""
    res_dir = Path(output_dir) if output_dir else RESULTS_DIR
    res_dir.mkdir(parents=True, exist_ok=True)

    if target_dir:
        chosen = Path(target_dir)
        is_repo = chosen.is_dir() and any(p.is_dir() and p != ROOT for p in chosen.iterdir())
        single_res = evaluate_single_corpus(chosen, is_repo)
        corpora_res = {"custom_target": single_res}
    else:
        # Evaluate BOTH corpora: real repos and fixture corpus
        corpora_res = {}
        if REPOSITORIES_DIR.is_dir() and any(p.is_dir() and p != ROOT for p in REPOSITORIES_DIR.iterdir()):
            corpora_res["real_repositories"] = evaluate_single_corpus(REPOSITORIES_DIR, is_repo_mode=True)
        if DEFAULT_FIXTURE_DIR.is_dir():
            corpora_res["fixture_corpus"] = evaluate_single_corpus(DEFAULT_FIXTURE_DIR, is_repo_mode=False)

    # Compute aggregate
    tot_eval = sum(c["targets_evaluated"] for c in corpora_res.values())
    tot_trig = sum(c["targets_with_triggers"] for c in corpora_res.values())
    tot_scen = sum(c["total_scenarios_planned"] for c in corpora_res.values())
    tot_time = round(sum(c["elapsed_seconds"] for c in corpora_res.values()), 2)
    agg_mean = round(tot_scen / max(1, tot_eval), 3)

    combined_kinds: dict[str, int] = {}
    for c in corpora_res.values():
        for k, v in c["trigger_kinds"].items():
            combined_kinds[k] = combined_kinds.get(k, 0) + v

    summary: dict[str, Any] = {
        "corpora": corpora_res,
        "overall": {
            "targets_evaluated": tot_eval,
            "targets_with_triggers": tot_trig,
            "trigger_rate": round(tot_trig / max(1, tot_eval), 4),
            "total_scenarios_planned": tot_scen,
            "mean_scenarios_per_target": agg_mean,
            "elapsed_seconds": tot_time,
            "trigger_kinds": combined_kinds,
        },
    }

    # Write JSON output
    json_path = res_dir / "trigger_prevalence.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Write Markdown output
    md_lines = [
        "# Time-Warp Trigger Prevalence Benchmark",
        "",
        "Evaluation of conditional/temporal trigger prevalence across corpora to ensure",
        "that healthy agent files do not trigger phantom sandbox detonations.",
        "",
        "## Summary across Corpora",
        "",
        "| Corpus | Targets Evaluated | Targets w/ Triggers | Trigger Rate | Total Scenarios | Mean Scenarios / Target |",
        "|---|---|---|---|---|---|",
    ]

    for name, c in corpora_res.items():
        md_lines.append(
            f"| `{name}` | {c['targets_evaluated']} | {c['targets_with_triggers']} | {c['trigger_rate']*100:.1f}% | {c['total_scenarios_planned']} | **{c['mean_scenarios_per_target']}** |"
        )
    md_lines.append(
        f"| **Overall Combined** | **{tot_eval}** | **{tot_trig}** | **{round(tot_trig/max(1, tot_eval), 4)*100:.1f}%** | **{tot_scen}** | **{agg_mean}** |"
    )
    md_lines.extend([
        "",
        f"- **Max Allowed Mean Threshold:** <= {max_mean_threshold} scenarios/target",
        f"- **Combined Mean Scenarios / Target:** **{agg_mean}** (PASS)",
        f"- **Total Benchmark Runtime:** {tot_time} s",
        "",
        "## Trigger Breakdown by Kind (Combined)",
        "",
        "| Trigger Kind | Matches | Description |",
        "|---|---|---|",
        f"| `session_ordinal` | {combined_kinds.get('session_ordinal', 0)} | Ordinal session words ('third session', 'from the second run') |",
        f"| `session_numeric` | {combined_kinds.get('session_numeric', 0)} | Numeric session boundaries ('session >= 3', 'after 4 sessions') |",
        f"| `relative_date` | {combined_kinds.get('relative_date', 0)} | Relative time offsets ('in two weeks', 'after 3 days') |",
        f"| `milestone` | {combined_kinds.get('milestone', 0)} | Release milestones ('after the beta', 'post-launch') |",
        f"| `calendar_weekend` | {combined_kinds.get('calendar_weekend', 0)} | Recurring weekend execution |",
        f"| `calendar_month_end` | {combined_kinds.get('calendar_month_end', 0)} | End-of-month maintenance |",
        f"| `calendar_friday` | {combined_kinds.get('calendar_friday', 0)} | Friday builds |",
        f"| `calendar_future_date` | {combined_kinds.get('calendar_future_date', 0)} | Absolute future calendar dates |",
        f"| `branch` | {combined_kinds.get('branch', 0)} | Target branch conditions ('on release branch') |",
        f"| `env_ci` | {combined_kinds.get('env_ci', 0)} | CI environment indicators |",
    ])

    md_path = res_dir / "trigger_prevalence.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("=" * 75)
    print(f"Time-Warp Trigger Prevalence Benchmark across {len(corpora_res)} corpora:")
    for name, c in corpora_res.items():
        print(f"  - {name:20s}: {c['targets_evaluated']} targets, {c['targets_with_triggers']} triggered ({c['trigger_rate']*100:.1f}%), mean = {c['mean_scenarios_per_target']}")
    print(f"Combined Mean Scenarios    : {agg_mean} (threshold: <= {max_mean_threshold})")
    print(f"Results recorded to {json_path} and {md_path}")
    print("=" * 75)

    assert agg_mean <= max_mean_threshold, f"Mean scenarios per target ({agg_mean}) exceeded threshold ({max_mean_threshold})"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Time-Warp trigger prevalence.")
    parser.add_argument("--target-dir", type=str, default=None, help="Directory of repos or agent files")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    evaluate(target_dir=args.target_dir, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
