"""
SENTINEL.md CLI — sentinel scan <target>

Usage:
    sentinel scan CLAUDE.md
    sentinel scan ./path/to/repo
    sentinel scan package.tar.gz
    sentinel scan --json CLAUDE.md          # machine-readable output

Phase A Week 1: Layer 1 only. Layer 2 (diff) and Layer 3 (LLM) are stubs
that wire up in Weeks 2–3 without changing the CLI interface.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import tarfile
import zipfile
from pathlib import Path

import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() \
    not in ('utf-8', 'utf-16'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from .rules import is_agent_config, scan_file, ScanResult


# ── ANSI colors (auto-disable on Windows / non-TTY) ─────────────────────────
def _color(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _color("91", t)
AMBER  = lambda t: _color("33", t)
GREEN  = lambda t: _color("92", t)
BOLD   = lambda t: _color("1",  t)
DIM    = lambda t: _color("2",  t)
CYAN   = lambda t: _color("96", t)


# ── Pretty-print a single ScanResult ─────────────────────────────────────────
def print_result(result: ScanResult) -> None:
    score = result.trust_score()
    band  = result.color_band()

    color_fn = {"red": RED, "amber": AMBER, "green": GREEN}.get(band, lambda t: t)
    label    = {"red": "COMPROMISED", "amber": "SUSPICIOUS", "green": "CLEAN"}.get(band, band.upper())

    header = f"\n{'─'*60}"
    print(header)
    print(BOLD(result.filename))
    print(f"  Trust Score  {color_fn(f'{score:3d}/100')}  [{color_fn(label)}]")

    if not result.findings:
        print(f"  {GREEN('✓')} No Layer 1 findings")
        return

    print(f"  {len(result.findings)} finding(s):\n")
    for f in sorted(result.findings, key=lambda x: -{"high": 3, "medium": 2, "low": 1}.get(x.severity, 0)):
        sev_str = {"high": RED("HIGH"), "medium": AMBER("MED"), "low": DIM("LOW")}.get(f.severity, f.severity)
        print(f"  [{sev_str}] {BOLD(f.rule_id)} — line {f.line}")
        print(f"         {f.message}")
        if f.snippet:
            print(f"         {DIM(repr(f.snippet[:80]))}")
        print()


# ── Collect files from a directory or archive ─────────────────────────────────
def collect_paths(target: str) -> list[Path]:
    p = Path(target)

    if p.is_file():
        if tarfile.is_tarfile(target):
            return _from_tar(p)
        if zipfile.is_zipfile(target):
            return _from_zip(p)
        return [p]

    if p.is_dir():
        return [f for f in p.rglob("*") if f.is_file() and is_agent_config(f)]

    print(f"sentinel: cannot find '{target}'", file=sys.stderr)
    sys.exit(1)


def _from_tar(p: Path) -> list[Path]:
    """Extract agent-config files from a tarball into /tmp, return paths."""
    import tempfile, os
    tmp = Path(tempfile.mkdtemp(prefix="sentinel_"))
    with tarfile.open(p) as tf:
        members = [m for m in tf.getmembers()
                   if m.isfile() and is_agent_config(Path(m.name))]
        tf.extractall(tmp, members=members)
    return list(tmp.rglob("*"))


def _from_zip(p: Path) -> list[Path]:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="sentinel_"))
    with zipfile.ZipFile(p) as zf:
        names = [n for n in zf.namelist() if is_agent_config(Path(n))]
        for name in names:
            zf.extract(name, tmp)
    return list(tmp.rglob("*"))


# ── Agent's-Eye View (text-mode, for CLI demo) ───────────────────────────────
def agents_eye_view(text: str) -> str:
    """
    Returns a side-by-side diff where invisible Unicode is made visible.
    Full graphical version lives in the React frontend; this is the terminal version
    used in the Sep 5 live demo when the UI isn't loaded.
    """
    from .rules import ZERO_WIDTH_CHARS
    lines_human = []
    lines_agent = []
    for line in text.splitlines():
        lines_human.append(line)
        visible = ""
        for ch in line:
            if ch in ZERO_WIDTH_CHARS:
                visible += f"[U+{ord(ch):04X}]"   # make invisible chars bright red in terminal
            else:
                visible += ch
        lines_agent.append(visible)

    out = [f"{'HUMAN VIEW':<50}  AGENT PARSER SEES"]
    out.append("─" * 100)
    for h, a in zip(lines_human, lines_agent):
        marker = " ← HIDDEN" if h != a else ""
        out.append(f"{h[:50]:<50}  {a[:50]}{marker}")
    return "\n".join(out)


# ── Main entry point ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="SENTINEL.md — The firewall for your AI coding agent's instructions",
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Scan a file, directory, or archive")
    scan_p.add_argument("target", help="File path, directory, or .tar.gz/.zip package")
    scan_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    scan_p.add_argument("--eye", action="store_true", help="Show Agent's-Eye View for each file")
    scan_p.add_argument("--all", action="store_true", help="Show results for clean files too")

    args = parser.parse_args()

    if args.command == "scan":
        paths = collect_paths(args.target)
        if not paths:
            print(f"No agent-config files found in '{args.target}'")
            sys.exit(0)

        results = []
        for p in paths:
            res = scan_file(p)
            if os.environ.get("GROQ_API_KEY"):
                from sentinel.api import _infer_purpose, _call_analyze
                declared_purpose = _infer_purpose(str(p))
                layer1_summary = ", ".join(f"{f.rule_id} line {f.line}" for f in res.findings) if res.findings else "no findings"
                try:
                    res.layer3_result = _call_analyze(p.name, declared_purpose, layer1_summary, p.read_text(encoding='utf-8', errors='replace'))
                except Exception as e:
                    pass
            results.append(res)

        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
            return

        any_issues = False
        for result in results:
            if result.findings or args.all:
                print_result(result)
                if args.eye and result.findings:
                    p = Path(result.filename)
                    if p.exists():
                        print("\n" + CYAN("── Agent's-Eye View ──"))
                        print(agents_eye_view(p.read_text(encoding='utf-8', errors='replace')))
                if result.findings:
                    any_issues = True

        # Summary line
        n_files   = len(results)
        n_issues  = sum(1 for r in results if r.findings)
        n_clean   = n_files - n_issues
        avg_score = int(sum(r.trust_score() for r in results) / max(1, n_files))

        print(f"\n{'═'*60}")
        print(BOLD(f"Scanned {n_files} file(s) — avg Trust Score: {avg_score}/100"))
        if n_issues:
            print(RED(f"  {n_issues} file(s) with findings"))
        if n_clean:
            print(GREEN(f"  {n_clean} file(s) clean"))

        sys.exit(1 if any_issues else 0)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
