import json
import pytest
from pathlib import Path

from sentinel.doctor.graph import build, CycleError, Edge, estimate_tokens


def test_chain_imports(tmp_path: Path):
    """Test A imports B imports C resolves nodes, edges, order, and tokens."""
    c_file = tmp_path / "C.md"
    c_file.write_text("# Leaf instructions\nAlways use typing.", encoding="utf-8")

    b_file = tmp_path / "B.md"
    b_file.write_text("# Middleware instructions\n@include C.md\nFollow guidelines.", encoding="utf-8")

    a_file = tmp_path / "A.md"
    a_file.write_text("# Root instructions\n@import B.md\nDo not break CI.", encoding="utf-8")

    g = build(tmp_path, "A.md")

    assert "A.md" in g.nodes
    assert "B.md" in g.nodes
    assert "C.md" in g.nodes
    assert len(g.nodes) == 3

    assert ("A.md", "B.md") in g.edges
    assert ("B.md", "C.md") in g.edges

    assert g.order == ["A.md", "B.md", "C.md"]
    assert g.tokens > 0
    assert g.missing == []
    assert g.cycles == []


def test_cycle_detection(tmp_path: Path):
    """Test cyclical imports are safely detected without infinite recursion."""
    a_file = tmp_path / "A.md"
    b_file = tmp_path / "B.md"

    a_file.write_text("# File A\n@import B.md", encoding="utf-8")
    b_file.write_text("# File B\n@import A.md", encoding="utf-8")

    # Safe return without raise_on_cycle
    g = build(tmp_path, "A.md")
    assert len(g.cycles) >= 1
    assert ["A.md", "B.md", "A.md"] in g.cycles
    assert ("A.md", "B.md") in g.edges
    assert ("B.md", "A.md") in g.edges

    # Raising on cycle when requested
    with pytest.raises(CycleError, match="Cycle detected"):
        build(tmp_path, "A.md", raise_on_cycle=True)


def test_missing_import(tmp_path: Path):
    """Test broken/missing imports are recorded without crashing."""
    a_file = tmp_path / "A.md"
    a_file.write_text("# Instructions\n@import missing_submodule.md\n@include nonexistent/rules.md", encoding="utf-8")

    g = build(tmp_path, "A.md")

    assert "A.md" in g.nodes
    assert "missing_submodule.md" in g.missing
    assert any("nonexistent/rules.md" in m for m in g.missing)
    assert len(g.missing) == 2
    assert ("A.md", "missing_submodule.md") in g.edges


def test_nested_claude_discovery(tmp_path: Path):
    """Test hierarchical nested CLAUDE.md files are linked to root CLAUDE.md."""
    root_claude = tmp_path / "CLAUDE.md"
    root_claude.write_text("# Root Project Rules", encoding="utf-8")

    sub_dir = tmp_path / "services" / "auth"
    sub_dir.mkdir(parents=True)
    sub_claude = sub_dir / "CLAUDE.md"
    sub_claude.write_text("# Auth Microservice Rules", encoding="utf-8")

    g = build(tmp_path, "CLAUDE.md")

    assert "CLAUDE.md" in g.nodes
    assert "services/auth/CLAUDE.md" in g.nodes
    assert ("CLAUDE.md", "services/auth/CLAUDE.md") in g.edges
    assert g.tokens > 0


def test_max_depth_capping(tmp_path: Path):
    """Test recursion depth is bounded by max_depth."""
    prev = "file_0.md"
    (tmp_path / prev).write_text("root", encoding="utf-8")

    for i in range(1, 10):
        curr = f"file_{i}.md"
        (tmp_path / curr).write_text(f"content {i}", encoding="utf-8")
        # rewrite prev to import curr
        (tmp_path / prev).write_text(f"@import {curr}", encoding="utf-8")
        prev = curr

    # With max_depth=3, depth is capped
    g = build(tmp_path, "file_0.md", max_depth=3)
    assert len(g.nodes) <= 5


def test_edge_properties_and_json(tmp_path: Path):
    """Test Edge helper methods and JSON serializability."""
    e = Edge("foo.md", "bar.md")
    assert e.source == "foo.md"
    assert e.target == "bar.md"
    assert e.from_node == "foo.md"
    assert e.to_node == "bar.md"
    assert e.to_dict() == {"source": "foo.md", "target": "bar.md"}

    f = tmp_path / "entry.md"
    f.write_text("sample content", encoding="utf-8")
    g = build(tmp_path, "entry.md")
    # Verify dict is JSON-serializable
    dumped = json.dumps(g)
    loaded = json.loads(dumped)
    assert loaded["nodes"] == ["entry.md"]
    assert loaded["tokens"] > 0
