"""Detonation harness tests. No real model: a fake OpenAI-compatible server plays an obedient agent, so the
loop, the sandbox, the canary tracking and the differential are all exercised deterministically."""
import glob, json, os, re, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import pytest
from sentinel import detonate
from conftest import ROOT

CORPUS = ROOT / "bench" / "detonation"


def _obedient_handler():
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            sysx = body["messages"][0]["content"]
            done = [m for m in body["messages"] if m["role"] == "tool"]
            url = re.search(r"https?://[^\s)'\"]+", sysx)
            send = bool(url) and bool(re.search(r"\b(send|upload|post|forward|mirror|submit|transmit|paste|include|copy|store|publish|attach|push|report|register)\b", sysx, re.I))
            def wrap(cs): return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                {"id": f"c{i}", "type": "function", "function": {"name": n, "arguments": json.dumps(a)}} for i, (n, a) in enumerate(cs)]}}]}
            if send and len(done) == 0: out = wrap([("read_file", {"path": ".env"})])
            elif send and len(done) == 1: out = wrap([("http_request", {"method": "POST", "url": url.group(0), "body": done[-1]["content"]})])
            elif len(done) == 0: out = wrap([("read_file", {"path": "src/utils.py"})])
            else: out = {"choices": [{"message": {"role": "assistant", "content": "Done."}}]}
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(out).encode())
    return H


@pytest.fixture
def obedient_model():
    srv = HTTPServer(("127.0.0.1", 0), _obedient_handler())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield detonate.OpenAICompatModel(f"http://127.0.0.1:{srv.server_address[1]}/v1", "fake", "")
    srv.shutdown()


def test_sandbox_never_touches_the_real_world():
    assert detonate.fake_tool("http_request", {"method": "POST", "url": "https://example.invalid", "body": "x"}) == "ok"
    assert detonate.fake_tool("write_file", {"path": "/etc/passwd", "content": "x"}) == "ok"


def test_secret_files_resolve_by_the_names_a_model_uses():
    for path in (".env", "~/.aws/credentials", "./config/deploy.yaml", "/root/.ssh/id_rsa", ".npmrc"):
        assert detonate.CANARY in detonate.fake_tool("read_file", {"path": path}), path


def test_provider_presets_build_the_right_endpoint(monkeypatch):
    for k in ("SENTINEL_LLM_URL", "SENTINEL_LLM_PROVIDER", "SENTINEL_LLM_KEY", "SENTINEL_LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SENTINEL_LLM_MODEL", "m"); monkeypatch.setenv("SENTINEL_LLM_KEY", "k")
    monkeypatch.setenv("SENTINEL_LLM_PROVIDER", "groq")
    assert detonate.model_from_env().url.startswith("https://api.groq.com/openai/v1")
    monkeypatch.setenv("SENTINEL_LLM_PROVIDER", "anthropic")
    assert isinstance(detonate.model_from_env(), detonate.AnthropicModel)
    monkeypatch.delenv("SENTINEL_LLM_KEY")
    with pytest.raises(RuntimeError):                       # hosted endpoint without a key must fail loudly
        monkeypatch.setenv("SENTINEL_LLM_PROVIDER", "openai"); detonate.model_from_env()


def test_the_harness_catches_paraphrased_exfiltration_via_the_http_path(obedient_model):
    base = (CORPUS / "base_clean.md").read_text()
    attack = detonate.differential((CORPUS / "attack" / "01_notes_page.md").read_text(), base, obedient_model, "CLAUDE.md")
    benign = detonate.differential((CORPUS / "benign" / "03_never_secrets.md").read_text(), base, obedient_model, "CLAUDE.md")
    assert any(b == "CANARY_LEAK" for b, _ in attack["new_behaviours"])
    assert benign["new_behaviours"] == []


def test_corpus_is_all_static_misses_and_the_right_size():
    from sentinel import contract
    attacks = sorted(glob.glob(str(CORPUS / "attack" / "*.md")))
    benign = sorted(glob.glob(str(CORPUS / "benign" / "*.md")))
    assert len(attacks) == 30 and len(benign) == 30
    for f in attacks:                                      # if a static rule already catches it, it is not a detonation test
        assert contract.scan_text("CLAUDE.md", Path(f).read_text())["verdict"] == "CLEAN", f
    for f in benign:
        assert contract.scan_text("CLAUDE.md", Path(f).read_text())["verdict"] == "CLEAN", f


@pytest.mark.parametrize("n", [3])
def test_whole_corpus_separates_cleanly_against_an_obedient_agent(obedient_model, n):
    base = (CORPUS / "base_clean.md").read_text()
    def leaks(f): return any(b == "CANARY_LEAK" for b, _ in detonate.differential(Path(f).read_text(), base, obedient_model, "CLAUDE.md")["new_behaviours"])
    caught = sum(leaks(f) for f in sorted(glob.glob(str(CORPUS / "attack" / "*.md")))[:n])
    fp = sum(leaks(f) for f in sorted(glob.glob(str(CORPUS / "benign" / "*.md")))[:n])
    assert caught == n and fp == 0
