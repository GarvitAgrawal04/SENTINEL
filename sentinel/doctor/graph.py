"""Sentinel Doctor - Agent instruction file load graph analysis.

Builds a dependency/load graph by following `@import` / `@include` directives
and hierarchical nested `CLAUDE.md` files.

Every node in the graph is an attack surface an agent obeys and Sentinel must inspect.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable


IMPORT_RE = re.compile(
    r'(?:^|[\s*`<!-])@(?:import|include)\s+["\']?([^"\'\s>]+)["\']?',
    re.IGNORECASE | re.MULTILINE,
)

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".tox",
    ".mypy_cache",
    "dist",
    "build",
}

DEFAULT_MAX_DEPTH = 16


class CycleError(ValueError):
    """Raised when a circular import is detected and raise_on_cycle=True."""


class Edge(tuple):
    """A directed edge in the load graph (source -> target)."""

    def __new__(cls, source: str, target: str):
        return super().__new__(cls, (source, target))

    @property
    def source(self) -> str:
        return self[0]

    @property
    def target(self) -> str:
        return self[1]

    @property
    def from_node(self) -> str:
        return self[0]

    @property
    def to_node(self) -> str:
        return self[1]

    def to_dict(self) -> dict[str, str]:
        return {"source": self[0], "target": self[1]}


class LoadGraph(dict):
    """Dictionary representation of the load graph with attribute access."""

    @property
    def nodes(self) -> list[str]:
        return self["nodes"]

    @property
    def edges(self) -> list[Edge]:
        return self["edges"]

    @property
    def order(self) -> list[str]:
        return self["order"]

    @property
    def tokens(self) -> int:
        return self["tokens"]

    @property
    def cycles(self) -> list[list[str]]:
        return self.get("cycles", [])

    @property
    def missing(self) -> list[str]:
        return self.get("missing", [])

    @property
    def node_tokens(self) -> dict[str, int]:
        return self.get("node_tokens", {})


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text file (~4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def extract_imports(text: str) -> list[str]:
    """Extract imported file paths referenced in agent instructions."""
    raw = IMPORT_RE.findall(text)
    # Strip any trailing punct or brackets
    cleaned = []
    for p in raw:
        p = p.strip().strip("'\"`")
        if p and p not in cleaned:
            cleaned.append(p)
    return cleaned


def resolve_import_path(raw_import: str, current_file: Path, root: Path) -> Path:
    """Resolve an import path relative to current file's directory or repo root."""
    target = Path(raw_import)
    if target.is_absolute():
        try:
            rel = target.relative_to(root)
            return root / rel
        except ValueError:
            return root / target.name

    # 1. Check relative to current file's directory
    cand1 = (current_file.parent / target).resolve()
    if cand1.exists():
        return cand1

    # 2. Check relative to repository root
    cand2 = (root / target).resolve()
    if cand2.exists():
        return cand2

    # Default fallback: relative to current file's directory
    return cand1


def find_nested_claude_files(root: Path, entry_path: Path) -> list[Path]:
    """Find all nested CLAUDE.md files in subdirectories under root."""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.lower() == "claude.md":
                full_p = (Path(dirpath) / f).resolve()
                if full_p != entry_path.resolve():
                    found.append(full_p)
    return sorted(found)


def build(
    root: Path | str,
    entry_file: Path | str = "CLAUDE.md",
    max_depth: int = DEFAULT_MAX_DEPTH,
    raise_on_cycle: bool = False,
) -> LoadGraph:
    """Build the load graph for agent instruction files starting at entry_file.

    Follows `@import` / `@include` directives and discovers hierarchical nested
    `CLAUDE.md` files.

    Returns:
        LoadGraph with {nodes, edges, order, tokens, cycles, missing, node_tokens}.
    """
    root_path = Path(root).resolve()
    entry_p = Path(entry_file)
    if not entry_p.is_absolute():
        entry_full = (root_path / entry_p).resolve()
    else:
        entry_full = entry_p.resolve()

    try:
        entry_rel = entry_full.relative_to(root_path).as_posix()
    except ValueError:
        entry_rel = entry_p.name

    nodes: list[str] = []
    edges: list[Edge] = []
    order: list[str] = []
    node_tokens: dict[str, int] = {}
    missing: list[str] = []
    cycles: list[list[str]] = []

    visited: set[str] = set()
    stack: list[str] = []

    def get_rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(root_path).as_posix()
        except ValueError:
            return p.as_posix()

    def process_file(file_path: Path, current_depth: int) -> None:
        rel_name = get_rel(file_path)

        if rel_name not in nodes:
            nodes.append(rel_name)

        if not file_path.exists():
            if rel_name not in missing:
                missing.append(rel_name)
            node_tokens[rel_name] = 0
            if rel_name not in order:
                order.append(rel_name)
            return

        # Read content and compute tokens
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""

        tokens = estimate_tokens(content)
        node_tokens[rel_name] = tokens

        if rel_name not in order:
            order.append(rel_name)

        visited.add(rel_name)
        stack.append(rel_name)

        if current_depth < max_depth:
            # 1. Follow explicit @import / @include directives
            raw_imports = extract_imports(content)
            for imp in raw_imports:
                target_p = resolve_import_path(imp, file_path, root_path)
                target_rel = get_rel(target_p)
                edge = Edge(rel_name, target_rel)
                if edge not in edges:
                    edges.append(edge)

                if target_rel in stack:
                    # Circular reference detected!
                    idx = stack.index(target_rel)
                    cycle_path = stack[idx:] + [target_rel]
                    if cycle_path not in cycles:
                        cycles.append(cycle_path)
                    if target_rel not in nodes:
                        nodes.append(target_rel)
                else:
                    if target_rel not in visited:
                        process_file(target_p, current_depth + 1)

            # 2. If this is a root CLAUDE.md, follow hierarchical nested CLAUDE.md files
            if current_depth == 0 and file_path.name.lower() == "claude.md":
                nested_files = find_nested_claude_files(root_path, file_path)
                for nested_p in nested_files:
                    nested_rel = get_rel(nested_p)
                    edge = Edge(rel_name, nested_rel)
                    if edge not in edges:
                        edges.append(edge)
                    if nested_rel not in visited and nested_rel not in stack:
                        process_file(nested_p, current_depth + 1)

        stack.pop()

    process_file(entry_full, 0)

    if raise_on_cycle and cycles:
        raise CycleError(f"Cycle detected in instruction load graph: {' -> '.join(cycles[0])}")

    total_tokens = sum(node_tokens.get(n, 0) for n in nodes)

    return LoadGraph({
        "nodes": nodes,
        "edges": edges,
        "order": order,
        "tokens": total_tokens,
        "cycles": cycles,
        "missing": missing,
        "node_tokens": node_tokens,
    })
