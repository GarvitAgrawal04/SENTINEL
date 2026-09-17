"""Kept for the v1 workflow that called this script. It now delegates to `sentinel pr`."""
import os
import sys

from sentinel.cli import main

if __name__ == "__main__":
    base = os.environ.get("SENTINEL_BASE") or ("origin/" + os.environ["GITHUB_BASE_REF"] if os.environ.get("GITHUB_BASE_REF") else "HEAD~1")
    sys.exit(main(["pr", "--base", base, "--out", os.environ.get("SENTINEL_COMMENT", "sentinel-comment.md")]))
