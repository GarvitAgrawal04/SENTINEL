"""Prove that every button, badge, avatar and link in the README answers. Needs internet; standard library only.

    python docs/check_readme_links.py

Local files and #anchors are checked offline by tests/v5/test_readme.py; this script covers what only the network can tell.
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def external_links() -> list[str]:
    prose, in_code = [], False
    for line in (ROOT / "README.md").read_text(encoding="utf-8").split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code:
            prose.append(line)
    found = re.findall(r'(?:\]\(|href="|src="|srcset=")(https?://[^)"\s]+)', "\n".join(prose))
    return sorted({u for u in found if "example." not in u and "127.0.0.1" not in u})


def main() -> int:
    bad = 0
    for url in external_links():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sentinel README link check)"})
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                status = resp.status
        except Exception as e:                                   # noqa: BLE001 - report every kind of failure the same way
            status = getattr(e, "code", None) or type(e).__name__
        ok = isinstance(status, int) and 200 <= status < 400
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {status}  {url}")
    print(f"\n{bad} link(s) failed." if bad else "\nEvery external link in the README answers.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
