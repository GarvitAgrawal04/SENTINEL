"""Integration tests for sentinel timewarp run --record, budget, trace, and provider failure (Day 5)."""

import http.server
import json
import os
import socket
import threading
from pathlib import Path

import pytest

from sentinel.cli import main

ROOT = Path(__file__).resolve().parents[2]


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class StandInOpenAIHandler(http.server.BaseHTTPRequestHandler):
    """Stand-in mock server simulating an OpenAI-compatible /v1/chat/completions endpoint."""

    def log_message(self, format, *args):
        pass  # suppress server log noise

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8"))

        messages = payload.get("messages", [])
        last_msg = messages[-1] if messages else {}

        # Scripted mock response
        if last_msg.get("role") == "user":
            # Initial probe turn: call read_file tool
            resp = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_standin_1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": json.dumps({"path": "src/utils.py"}),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        else:
            # Tool result return turn: finish probe
            resp = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Completed requested task in sandbox.",
                        }
                    }
                ]
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))


@pytest.fixture
def stand_in_provider():
    port = find_free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), StandInOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/v1"
    server.shutdown()


def test_timewarp_run_record_and_replay_standin(stand_in_provider, tmp_path, monkeypatch, capsys):
    """Record a cassette with a stand-in provider, then replay 100% offline."""
    monkeypatch.setenv("SENTINEL_LLM_URL", stand_in_provider)
    monkeypatch.setenv("SENTINEL_LLM_KEY", "sk-mock-test-key")
    monkeypatch.setenv("SENTINEL_LLM_MODEL", "mock-model")

    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    record_dir = tmp_path / "recorded_cassette"

    # 1. Record live model interactions
    ret_rec = main(["timewarp", "run", str(target_file), "--record", str(record_dir), "--trace"])
    assert ret_rec == 0
    captured_rec = capsys.readouterr()

    assert "estimate:" in captured_rec.out
    assert "[trace] Scenario plan" in captured_rec.out
    assert "recorded:" in captured_rec.out
    assert (record_dir / "cassette.json").is_file()

    # Verify cassette structure
    cassette_data = json.loads((record_dir / "cassette.json").read_text(encoding="utf-8"))
    assert "entries" in cassette_data
    assert len(cassette_data["entries"]) > 0

    # 2. Replay cassette with NO network / invalid provider URL
    monkeypatch.setenv("SENTINEL_LLM_URL", "http://127.0.0.1:59999/down")
    ret_rep = main(["timewarp", "run", str(target_file), "--replay", str(record_dir), "--trace"])
    assert ret_rep == 0
    captured_rep = capsys.readouterr()
    assert "[trace] Per-scenario spend:" in captured_rep.out
    assert "sentinel timewarp  verdict: CLEAN" in captured_rep.out


def test_provider_down_never_clean(tmp_path, monkeypatch, capsys):
    """When the provider is down, recording must fail and NEVER report CLEAN."""
    # Point to an unused, dead local port
    dead_port = find_free_port()
    monkeypatch.setenv("SENTINEL_LLM_URL", f"http://127.0.0.1:{dead_port}/v1")
    monkeypatch.setenv("SENTINEL_LLM_KEY", "sk-test")
    monkeypatch.setenv("SENTINEL_LLM_MODEL", "test-model")
    monkeypatch.setenv("SENTINEL_LLM_RPM", "0")

    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    record_dir = tmp_path / "dead_rec"

    ret = main(["timewarp", "run", str(target_file), "--record", str(record_dir)])
    assert ret != 0

    captured = capsys.readouterr()
    assert "error:" in captured.err or "error:" in captured.out
    assert "verdict: CLEAN" not in captured.out


def test_budget_drops_scenarios(tmp_path, capsys):
    """Assert that --budget N drops scenarios with a printed notification line."""
    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    replay_dir = ROOT / "tests" / "fixtures" / "sleeper"

    ret = main(["timewarp", "run", str(target_file), "--replay", str(replay_dir), "--budget", "1"])
    assert ret == 0

    captured = capsys.readouterr()
    assert "dropped: session_3 (exceeds budget)" in captured.out
    assert "across 1 scenarios" in captured.out


def test_timewarp_run_parallel_execution(tmp_path, capsys):
    """Assert --parallel runs concurrent worker pool (capped at 4)."""
    target_file = ROOT / "tests" / "fixtures" / "sleeper" / "AGENTS.md"
    replay_dir = ROOT / "tests" / "fixtures" / "sleeper"

    ret = main(["timewarp", "run", str(target_file), "--replay", str(replay_dir), "--parallel", "4", "--trace"])
    assert ret == 1  # detects finding in sleeper cassette
    captured = capsys.readouterr()
    assert "[trace] Scenario plan" in captured.out
    assert "conditional finding" in captured.out
