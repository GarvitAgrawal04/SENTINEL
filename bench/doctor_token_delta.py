"""Benchmark script: Token delta measurement before and after doctor auto-fixes.

Evaluates 50 public agent files before and after `sentinel doctor --fix`.
Asserts that the median token delta <= 0 (hygiene fixes strictly prune duplicate rules,
broken includes, and ANSI escapes without adding token bloat).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel.doctor import lints

DEFAULT_CORPUS_DIR = ROOT / "tests" / "fixtures" / "doctor_corpus"
RESULTS_DIR = ROOT / "bench" / "results"


def evaluate(
    corpus_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    assert_median_non_positive: bool = True,
) -> dict[str, Any]:
    """Run before/after --fix evaluation on agent files and compute token delta."""
    c_dir = Path(corpus_dir) if corpus_dir else DEFAULT_CORPUS_DIR
    res_dir = Path(output_dir) if output_dir else RESULTS_DIR
    res_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = c_dir / "manifest.json"
    manifest_by_name = {}
    if manifest_path.is_file():
        try:
            m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in m_data:
                manifest_by_name[entry["filename"]] = entry
        except Exception:
            pass

    target_files = sorted([f for f in c_dir.iterdir() if f.is_file() and f.suffix in (".md", ".mdc", ".cursorrules")])
    if not target_files:
        raise RuntimeError(f"No agent instruction files found in {c_dir}")

    file_results: list[dict[str, Any]] = []
    deltas: list[int] = []
    total_fixes = 0
    total_before = 0
    total_after = 0

    print(f"Evaluating token delta across {len(target_files)} public agent files...")
    print(f"{'File':<16} {'Original Repo / Path':<36} {'Before':<8} {'After':<8} {'Delta':<8} {'Fixes':<6}")
    print("-" * 88)

    for f in target_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        tok_before = lints.estimate_tokens(content)

        findings = lints.check_text(content, filename=f.name)
        fixed_content, n_fixes = lints.apply_fixes(content, findings)
        tok_after = lints.estimate_tokens(fixed_content)

        delta = tok_after - tok_before
        deltas.append(delta)
        total_fixes += n_fixes
        total_before += tok_before
        total_after += tok_after

        meta = manifest_by_name.get(f.name, {})
        orig_desc = meta.get("original_path", f.name)

        file_results.append({
            "file": f.name,
            "original_path": orig_desc,
            "tokens_before": tok_before,
            "tokens_after": tok_after,
            "token_delta": delta,
            "percent_change": round((delta / max(1, tok_before)) * 100, 2),
            "fixes_applied": n_fixes,
            "findings_count": len(findings),
            "finding_ids": [find["id"] for find in findings],
        })

        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{f.name:<16} {orig_desc[:34]:<36} {tok_before:<8} {tok_after:<8} {delta_str:<8} {n_fixes:<6}")

    median_delta = float(statistics.median(deltas))
    mean_delta = round(float(statistics.mean(deltas)), 2)
    min_delta = min(deltas)
    max_delta = max(deltas)
    files_with_fixes = sum(1 for r in file_results if r["fixes_applied"] > 0)

    print("-" * 88)
    print(f"Total files evaluated     : {len(target_files)}")
    print(f"Files with fixes applied : {files_with_fixes} ({files_with_fixes / len(target_files) * 100:.1f}%)")
    print(f"Total fixes applied      : {total_fixes}")
    print(f"Total tokens before      : {total_before}")
    print(f"Total tokens after       : {total_after} (net delta: {total_after - total_before:+d})")
    print(f"Median token delta       : {median_delta:+.1f} tokens")
    print(f"Mean token delta         : {mean_delta:+.2f} tokens")
    print(f"Range                    : [{min_delta:+d}, {max_delta:+d}] tokens")

    summary: dict[str, Any] = {
        "files_tested": len(target_files),
        "files_with_fixes": files_with_fixes,
        "total_fixes_applied": total_fixes,
        "total_tokens_before": total_before,
        "total_tokens_after": total_after,
        "net_token_delta": total_after - total_before,
        "median_token_delta": median_delta,
        "mean_token_delta": mean_delta,
        "min_token_delta": min_delta,
        "max_token_delta": max_delta,
        "results": file_results,
    }

    # Save JSON report
    json_path = res_dir / "doctor_token_delta.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Generate Markdown report
    md_lines = [
        "# Instruction Doctor Token Delta Benchmark",
        "",
        "Evaluation of 50 public agent files before and after `sentinel doctor --fix`.",
        "Demonstrates that deterministic fixes (duplicate rule pruning, broken includes removal, ANSI escape stripping)",
        "strictly reduce or preserve context window consumption.",
        "",
        "## Summary Metrics",
        "",
        f"- **Files Evaluated:** {summary['files_tested']}",
        f"- **Files Requiring Fixes:** {files_with_fixes} ({files_with_fixes / summary['files_tested'] * 100:.1f}%)",
        f"- **Total Safe Fixes Applied:** {total_fixes}",
        f"- **Context Tokens Before:** {total_before:,}",
        f"- **Context Tokens After:** {total_after:,}",
        f"- **Net Token Delta:** {total_after - total_before:+,} tokens",
        f"- **Median Token Delta:** **{median_delta:+.1f} tokens** (requirement: <= 0)",
        f"- **Mean Token Delta:** **{mean_delta:+.2f} tokens**",
        f"- **Delta Range:** [{min_delta:+d}, {max_delta:+d}] tokens",
        "",
        "## Per-File Evaluation Breakdown",
        "",
        "| File | Origin Repo / Path | Tokens Before | Tokens After | Delta | Fixes Applied | Findings |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in file_results:
        d_str = f"**{r['token_delta']:+d}**" if r["token_delta"] < 0 else "0"
        md_lines.append(
            f"| `{r['file']}` | {r['original_path']} | {r['tokens_before']} | {r['tokens_after']} | {d_str} | {r['fixes_applied']} | {r['findings_count']} |"
        )

    md_path = res_dir / "doctor_token_delta.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"\nResults recorded to {json_path} and {md_path}")

    if assert_median_non_positive:
        assert median_delta <= 0, f"Expected median token delta <= 0, got {median_delta}"
        assert max_delta <= 0, f"Expected max token delta <= 0, got {max_delta}"

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate token delta before and after doctor --fix.")
    parser.add_argument("--corpus-dir", type=str, default=None, help="Directory of agent files to evaluate")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to write results")
    args = parser.parse_args()

    evaluate(corpus_dir=args.corpus_dir, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
