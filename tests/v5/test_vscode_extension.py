"""The VS Code extension, run for real against the API with a stand-in for the `vscode` module (needs Node.js; skipped without it)."""
import shutil
import socket
import subprocess
import threading
import time

import pytest

pytest.importorskip("fastapi"); uvicorn = pytest.importorskip("uvicorn")
from conftest import ROOT
from sentinel import contract
from sentinel.api import app


def test_clean_files_are_green_as_the_v1_contract_promised():
    """v1 clients (this extension among them) test for 'green'. v5 briefly said 'clean', and clean files got no message at all."""
    assert contract.scan_text("CLAUDE.md", "# Rules\n\nUse type hints.\n")["color_band"] == "green"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_extension_underlines_the_right_line_and_reports_in_plain_english():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    try:
        r = subprocess.run(["node", str(ROOT / "vscode-extension" / "test" / "smoke.js"), f"http://127.0.0.1:{port}"],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        server.should_exit = True
