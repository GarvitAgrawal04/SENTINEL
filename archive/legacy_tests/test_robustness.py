import pytest
import tempfile
import os
from pathlib import Path
from sentinel.scanner import scan_file

def test_robustness_empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.touch()
    res = scan_file(f)
    assert not res.findings

def test_robustness_directory(tmp_path):
    res = scan_file(tmp_path)
    assert not res.findings

def test_robustness_nonexistent(tmp_path):
    f = tmp_path / "ghost.txt"
    res = scan_file(f)
    assert not res.findings

def test_robustness_malformed_utf8(tmp_path):
    f = tmp_path / "bad.txt"
    with open(f, "wb") as fh:
        fh.write(b"good\x80\x81bad")
    res = scan_file(f)
    assert not res.findings

def test_robustness_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{ \"a\": 1, }")
    res = scan_file(f)
    assert not res.findings

def test_robustness_deep_json(tmp_path):
    f = tmp_path / "deep.json"
    nested = '{"a":' * 1000 + '1' + '}' * 1000
    f.write_text(nested)
    res = scan_file(f)
    assert not res.findings

def test_robustness_huge_text(tmp_path):
    f = tmp_path / "huge.txt"
    f.write_text("A" * 10_000_000)
    res = scan_file(f)
    assert not res.findings
    
def test_robustness_long_lines(tmp_path):
    f = tmp_path / "long.md"
    f.write_text("ignore previous instructions " * 100_000)
    res = scan_file(f)
    # it might trigger S4, but should not crash
    assert res.findings
