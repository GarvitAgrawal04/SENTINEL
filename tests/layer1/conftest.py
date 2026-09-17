"""
Shared fixtures for the Layer 1 (DETECT) test suite.

This file is the ONLY place that knows how the tests talk to the sentinel package.
If your function names / signatures differ from tests/README.md, adapt
`run_rule`, `make_ctx` and `score` here and leave the test files alone.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Callable, Iterable

import pytest

# ---------------------------------------------------------------------------
# Contract imports — adjust these three lines if your module layout differs.
# ---------------------------------------------------------------------------
from sentinel.rules.base import Finding
from sentinel.rules.base import ScanResult
from sentinel.scoring.formula import compute_score, compute_verdict, score_breakdown
import dataclasses

@dataclasses.dataclass
class ScanContext:
    project_root: Path
    home: Path
    files: dict[str, str] = dataclasses.field(default_factory=dict)
    diff_status: dict[str, str] = dataclasses.field(default_factory=dict)
    git_tracked: set[str] = dataclasses.field(default_factory=set)
    origin: str = "unknown"
    trusted_tools: dict = dataclasses.field(default_factory=dict)

@dataclasses.dataclass
class DisplacementResult:
    direction: str = None
    rule_id: str = None
    layer2_score: int = 0

@dataclasses.dataclass
class ScoreResult:
    score: int
    verdict: str

def compute_trust_score(findings, displacement, l3_confidence_clean):
    res = ScanResult(filename="test.md", findings=findings)
    # Monkey patch for tests
    res.displacement = displacement
    res.l3_confidence_clean = l3_confidence_clean
    score = compute_score(res)
    verdict = compute_verdict(res, score)
    breakdown = score_breakdown(res, score)
    result = ScoreResult(score=score, verdict=verdict)
    # Monkey patch breakdown onto result
    result.breakdown = breakdown
    return result

# Rule module names exactly as in PRD Section 20 "Canonical codebase structure".
RULE_MODULES: dict[str, str] = {
    "S1": "s1_unicode",
    "S2": "s2_comments",
    "S3": "s3_mcp_injection",
    "S4": "s4_override",
    "S5": "s5_exfiltration",
    "S6": "s6_new_file",
    "S7": "s7_encoding",
    "S8": "s8_contradiction",
    "S9": "s9_tool_shadow",
    "S10": "s10_hook_survivability",
    "S11": "s11_bridge_url",
    "S12": "s12_trust_delegation",
    "S13": "s13_persona_override",
    "S14": "s14_write_intercept",
    "S15": "s15_slash_command",
    "S16": "s16_mcp_autoenable",
}


def pytest_configure(config):
    config.addinivalue_line("markers", "perf: timing sanity tests (deselect with -m 'not perf')")


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class TestFinding:
    rule_id: str
    penalty: int
    unambiguous: bool
    evidence: str
    path: str
    ceiling: int = None
    offset: int = 1

def _run_rule(rule: str, content: str, path: str, ctx: ScanContext) -> list[TestFinding]:
    """Run one rule. `rule` is 'S1'..'S16' or a module name like 's1_unicode'."""
    module_name = RULE_MODULES.get(rule, rule)
    mod = importlib.import_module(f"sentinel.rules.{module_name}")
    
    original_path = path
    # Expand ~ to ctx.home so rules receive absolute paths without using expanduser
    if path.startswith("~/") or path.startswith("~\\"):
        path = str(ctx.home) + path[1:]
    elif not Path(path).is_absolute():
        path = str(ctx.project_root / path)
    
    if rule == "S8" and hasattr(mod, "scan_multi"):
        raw_findings = list(mod.scan_multi(ctx.files))
    else:
        origin = ctx.origin
        if rule == "S6" and origin == "unknown":
            status = ctx.diff_status.get(original_path, "unchanged")
            if status in {"added", "modified"}:
                origin = "postinstall-suspected"
                
        if hasattr(mod, "scan"):
            import inspect
            sig = inspect.signature(mod.scan)
            kwargs = {}
            if "origin" in sig.parameters:
                kwargs["origin"] = origin
            if "git_tracked" in sig.parameters:
                kwargs["git_tracked"] = ctx.git_tracked
            if "diff_status" in sig.parameters:
                kwargs["diff_status"] = ctx.diff_status
            if "trusted_tools" in sig.parameters:
                kwargs["trusted_tools"] = ctx.trusted_tools
            raw_findings = list(mod.scan(content, path, **kwargs))
        else:
            raw_findings = []
            
    test_findings = []
    for f in raw_findings:
        offset = f.offset if hasattr(f, 'offset') and f.offset is not None else content.find(f.snippet)
        if offset == -1:
            # Fallback for offset
            offset = 1
        test_findings.append(TestFinding(
            rule_id=f.rule_id,
            penalty=-f.penalty if f.penalty is not None else None,
            unambiguous=f.forces_compromised,
            evidence=f.snippet,
            path=original_path,
            ceiling=f.ceiling,
            offset=offset
        ))
    return test_findings


def _run_all_rules(content: str, path: str, ctx: ScanContext) -> list[TestFinding]:
    out: list[TestFinding] = []
    for rule in RULE_MODULES:
        out.extend(_run_rule(rule, content, path, ctx))
    return out


@pytest.fixture
def run_rule() -> Callable[[str, str, str, ScanContext], list[TestFinding]]:
    return _run_rule


@pytest.fixture
def run_all_rules() -> Callable[[str, str, ScanContext], list[TestFinding]]:
    return _run_all_rules


@pytest.fixture
def make_ctx(tmp_path: Path) -> Callable[..., ScanContext]:
    """
    Build a ScanContext rooted at a fresh tmp project.
    Any keyword overrides the dataclass field of the same name.
    A `home` directory is always created so global-scope tests can write into it.
    """

    def _make(**overrides) -> ScanContext:
        project = overrides.pop("project_root", tmp_path / "project")
        home = overrides.pop("home", tmp_path / "home")
        Path(project).mkdir(parents=True, exist_ok=True)
        Path(home).mkdir(parents=True, exist_ok=True)
        return ScanContext(project_root=Path(project), home=Path(home), **overrides)

    return _make


@pytest.fixture
def score() -> Callable[..., ScoreResult]:
    """Thin wrapper around the formula so tests read naturally."""

    def _score(
        findings: Iterable[Finding] = (),
        displacement: DisplacementResult | None = None,
        l3_confidence_clean: float | None = None,
    ) -> ScoreResult:
        return compute_trust_score(list(findings), displacement, l3_confidence_clean)

    return _score


# ---------------------------------------------------------------------------
# Small helpers exposed as fixtures (so test files stay import-free)
# ---------------------------------------------------------------------------
@pytest.fixture
def ids() -> Callable[[Iterable[Finding]], set[str]]:
    return lambda findings: {f.rule_id for f in findings}


@pytest.fixture
def only() -> Callable[[Iterable[Finding], str], Finding]:
    """Return the single finding with rule_id; fail loudly if 0 or >1."""

    def _only(findings: Iterable[Finding], rule_id: str) -> Finding:
        hits = [f for f in findings if f.rule_id == rule_id]
        assert len(hits) == 1, f"expected exactly one {rule_id} finding, got {hits!r}"
        return hits[0]

    return _only


@pytest.fixture
def write(tmp_path: Path) -> Callable[[Path, str, str], Path]:
    """write(root, 'rel/path', content) -> absolute Path (creates parents)."""

    def _write(root: Path, rel: str, content: str) -> Path:
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    return _write


@pytest.fixture
def mk_finding() -> Callable[..., Finding]:
    """Construct a Finding for formula tests without running a rule."""

    def _mk(rule_id: str, penalty: int, unambiguous: bool = False, ceiling: int | None = None,
            path: str = "CLAUDE.md", evidence: str = "synthetic") -> Finding:
        return Finding(rule_id=rule_id, rule_name="Test", severity="high",
                       filename=path, line=1, message="test", snippet=evidence,
                       penalty=penalty, forces_compromised=unambiguous, ceiling=ceiling)

    return _mk


@pytest.fixture
def hooks_json() -> Callable[..., str]:
    """
    Build a .claude/settings.json string using Claude Code's REAL three-level
    nested hook schema (PRD 13.3 / Appendix F):

        hooks -> <EventName> -> [ { matcher?, hooks: [ { type, command } ] } ]

    hooks_json(SessionStart=[("", "node .claude/setup.mjs")],
               PreToolUse=[("Write|Edit", "bash .claude/hooks/fmt.sh")],
               extra={"enableAllProjectMcpServers": True})
    """

    def _build(extra: dict | None = None, **events: list[tuple[str, str]]) -> str:
        doc: dict = {"hooks": {}}
        for event, entries in events.items():
            groups = []
            for matcher, command in entries:
                group: dict = {"hooks": [{"type": "command", "command": command}]}
                if matcher:
                    group["matcher"] = matcher
                groups.append(group)
            doc["hooks"][event] = groups
        if extra:
            doc.update(extra)
        return json.dumps(doc, indent=2)

    return _build


@pytest.fixture
def tools_json() -> Callable[..., str]:
    """tools_json([("get_weather", "Get weather for a city", {"city": "string"})]) -> tools/list JSON."""

    def _build(tools: list[tuple[str, str, dict]]) -> str:
        return json.dumps({
            "tools": [
                {
                    "name": name,
                    "description": desc,
                    "inputSchema": {
                        "type": "object",
                        "properties": {k: {"type": v} for k, v in props.items()},
                    },
                }
                for name, desc, props in tools
            ]
        }, indent=2)

    return _build
