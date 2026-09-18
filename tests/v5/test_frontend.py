"""The web UI is plain files served by the API. These tests keep it honest: it loads, it stays self-contained,
its saved results match the engine, and the routes it depends on behave."""
import json
import re

import pytest

pytest.importorskip("fastapi"); pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from conftest import ROOT
from sentinel import contract, samples
from sentinel.api import app

c = TestClient(app)
FRONTEND = ROOT / "frontend"


def test_the_api_serves_the_ui_and_api_routes_still_win():
    page = c.get("/")
    assert page.status_code == 200 and "See what a file would make your AI agent do." in page.text
    for asset in ("app.js", "styles.css", "config.js", "favicon.svg", "saved-results.json"):
        assert c.get("/" + asset).status_code == 200, asset
    assert c.get("/health").json()["engine"] == "v5" and c.get("/docs").status_code == 200


def test_ui_is_self_contained_no_third_party_requests_and_a_strict_csp():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in html and "script-src 'self'" in html and "style-src 'self'" in html
    assert not re.search(r"<script[^>]+src=[\"']https?:", html) and not re.search(r"<link[^>]+href=[\"']https?:", html)
    assert " style=" not in html and "<style" not in html                       # the CSP forbids inline styles
    css = (FRONTEND / "styles.css").read_text(encoding="utf-8")
    assert "@import" not in css and "url(http" not in css                         # no web fonts, no remote assets
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js.replace("never innerHTML", "")                   # scanned text is untrusted
    assert not (FRONTEND / "package.json").exists() and not (FRONTEND / "node_modules").exists()


def test_samples_routes():
    listing = c.get("/samples").json()
    assert [s["file"] for s in listing][0] == "trapdoor_style_demo.md" and all(s["title"] and s["description"] for s in listing)
    assert c.get("/samples/clean_reference.md").json()["text"].strip()
    for bad in ("nope.md", "..%2Fpyproject.toml", "%2e%2e%2f.env.example"):
        assert c.get("/samples/" + bad).status_code == 404


def test_scan_bundle_gives_repository_context_and_has_limits():
    hook = json.dumps({"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "node .claude/setup.mjs"}]}]}})
    out = c.post("/scan/bundle", json={"files": {".claude/settings.json": hook, "../../escape.md": "x"}}).json()
    assert out["verdict"] == "COMPROMISED" and out["files"][0]["findings"][0]["rule_id"] == "S10"
    assert c.post("/scan/bundle", json={"files": {f"f{i}.md": "x" for i in range(201)}}).status_code == 413


def test_saved_results_match_the_engine_today():
    saved = json.loads((FRONTEND / "saved-results.json").read_text(encoding="utf-8"))["samples"]
    assert [s["file"] for s in saved] == [s["file"] for s in samples.listing()]
    for s in saved:
        live = contract.scan_text(s["file"], samples.read(s["file"]))
        assert s["text"] == samples.read(s["file"]), s["file"]
        assert (s["result"]["verdict"], s["result"]["trust_score"], [f["rule_id"] for f in s["result"]["findings"]]) == \
               (live["verdict"], live["trust_score"], [f["rule_id"] for f in live["findings"]]), \
               f"{s['file']} is stale: run python demo/save_sample_results.py"


def test_vercel_deployment_stays_deployable():
    """Vercel installs from pyproject.toml when it can see one, and ours lists no dependencies on purpose.
    That once took the hosted demo down with 500 FUNCTION_INVOCATION_FAILED. Keep the three things that prevent it."""
    ignore = (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
    assert "pyproject.toml" in ignore                                       # the builder must fall back to requirements.txt
    for needed in ("api/", "sentinel/", "frontend/", "samples/", "requirements.txt"):
        assert needed not in ignore and needed.rstrip("/") not in ignore, needed
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "fastapi==" in reqs and "python-multipart==" in reqs
    import importlib
    assert type(importlib.import_module("api.index").app).__name__ == "FastAPI"   # the entrypoint Vercel discovers
