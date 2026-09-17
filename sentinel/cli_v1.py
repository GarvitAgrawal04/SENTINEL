"""
SENTINEL CLI — sentinel scan <target>

Usage:
    sentinel scan .                    # Scan current directory (full D1 discovery)
    sentinel scan CLAUDE.md            # Scan a single file
    sentinel scan --hooks-only .       # Scan only hook surfaces (ChainDrop detection)
    sentinel scan --json .             # Machine-readable JSON output
    sentinel scan --all .              # Show all files including clean ones
    sentinel scan --eye CLAUDE.md      # Show Agent's-Eye View (invisible chars)

The CLI is thin: it calls scanner.py → formula.py → formatter.py.
No rule logic lives in the CLI.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf-16'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── ANSI colors (auto-disable on Windows / non-TTY) ───────────────────────────
def _color(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _color("91", t)
AMBER  = lambda t: _color("33", t)
GREEN  = lambda t: _color("92", t)
CYAN   = lambda t: _color("96", t)
BOLD   = lambda t: _color("1",  t)
DIM    = lambda t: _color("2",  t)


def _agents_eye_view(text: str) -> str:
    """
    Show a side-by-side diff of what a human sees vs what the agent parser sees.
    Highlights invisible Unicode characters by rendering them as [U+XXXX].
    """
    from sentinel.rules.s1_unicode import _is_invisible

    lines_human = []
    lines_agent = []
    for line in text.splitlines()[:30]:  # cap at 30 lines for terminal output
        lines_human.append(line)
        visible = ""
        for ch in line:
            if _is_invisible(ch):
                visible += CYAN(f"[U+{ord(ch):04X}]")
            else:
                visible += ch
        lines_agent.append(visible)

    out = [f"{'HUMAN VIEW':<50}  AGENT PARSER SEES"]
    out.append("─" * 100)
    for h, a in zip(lines_human, lines_agent):
        marker = "  " + RED("◄ HIDDEN CHARS") if h != a else ""
        out.append(f"{h[:50]:<50}  {a[:50]}{marker}")
    return "\n".join(out)


def _collect_paths(target: str) -> list[Path]:
    """Collect file paths for a target (file, directory, or archive)."""
    p = Path(target)
    if p.is_file():
        return [p]
    if p.is_dir():
        from sentinel.layer0.discovery import discover
        return discover(p)
    # Try as glob pattern
    results = list(Path(".").glob(target))
    return [r for r in results if r.is_file()]


def _print_result(result, show_eye: bool = False) -> None:
    """Print a formatted result using the output formatter."""
    from sentinel.output.formatter import format_result
    from sentinel.scoring.formula import compute_score, compute_verdict

    output = format_result(result, show_reconstruction=True)
    print(output)

    if show_eye and result.findings:
        path = Path(result.filename)
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            print(CYAN("\n── Agent's-Eye View (first 30 lines) ──"))
            print(_agents_eye_view(text))
            print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="SENTINEL — The firewall for your AI coding agent's instructions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sentinel scan .                      Full scan of current directory
  sentinel scan --hooks-only .         Scan only hook surfaces (ChainDrop detection)
  sentinel scan CLAUDE.md              Scan one file
  sentinel scan --json .               Machine-readable JSON output
  sentinel scan --eye CLAUDE.md        Agent's-Eye View (shows invisible chars)
  sentinel scan --all .                Show all files including clean ones
        """,
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Scan a file, directory, or archive")
    scan_p.add_argument("target", nargs="?", default=".", help="File or directory to scan (default: current directory)")
    scan_p.add_argument("--hooks-only", action="store_true", help="Scan only hook surfaces (.claude/settings.json, ~/.claude/settings.json)")
    scan_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    scan_p.add_argument("--eye", action="store_true", help="Show Agent's-Eye View (invisible Unicode highlighted)")
    scan_p.add_argument("--all", action="store_true", help="Show results for clean files too (not just findings)")

    args = parser.parse_args()

    if args.command == "scan":
        from sentinel.scanner import scan_directory, scan_file
        from sentinel.scoring.formula import compute_score, compute_verdict, score_breakdown
        from sentinel.output.formatter import format_result, format_summary

        target = Path(args.target)

        if target.is_file():
            # Single file scan
            results = [scan_file(target)]
        elif target.is_dir():
            results = scan_directory(target, hooks_only=args.hooks_only)
        else:
            print(f"Target not found: '{args.target}'", file=sys.stderr)
            sys.exit(1)

        if not results:
            if args.hooks_only:
                print(GREEN("No hook surfaces found (.claude/settings.json or ~/.claude/settings.json)"))
                print(DIM("This is consistent with no ChainDrop/Miasma-style hook installation."))
            else:
                print(f"No agent-config files found in '{args.target}'")
            sys.exit(0)

        # Layer 2, 3, 4 Integration (only if not hooks-only)
        if not args.hooks_only:
            from sentinel.pipeline import get_orchestrator
            orch = get_orchestrator()
            results = orch.run_full_pipeline(results)

        from sentinel.redaction import redact_scan_result
        for r in results:
            redact_scan_result(r)

        # JSON output
        if args.json:
            import dataclasses
            out = []
            for r in results:
                d = r.to_dict()
                if getattr(r, 'guide', None):
                    d['guide'] = dataclasses.asdict(r.guide)
                out.append(d)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            any_issues = any(r.findings for r in results)
            sys.exit(1 if any_issues else 0)

        # ── Human-readable output ─────────────────────────────────────────────
        any_issues = False

        for result in results:
            trust_score = compute_score(result)
            verdict = compute_verdict(result, trust_score)
            if result.findings or args.all:
                _print_result(result, show_eye=args.eye)
                if result.findings:
                    any_issues = True
            elif verdict == "CLEAN" and not args.all:
                # Brief clean line for non-flagged files
                print(f"  {GREEN('✓')} {result.filename} — score {GREEN(str(trust_score))}/100 CLEAN  origin:{DIM(result.origin)}")

        # ── Summary ───────────────────────────────────────────────────────────
        if len(results) > 1:
            print(format_summary(results))

        sys.exit(1 if any_issues else 0)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
