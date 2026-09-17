"""
sentinel/scanner.py
Central scan orchestrator for Layer 0 → Layer 1 pipeline.

This is the ONLY place that wires all rules together.
Neither the CLI nor the API should contain rule logic.

scan_file(path, text=None) — scan one file through all applicable L1 rules
scan_directory(root, hooks_only=False) — full D1+D3+L1 pipeline
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from sentinel.rules.base import ScanResult, Finding

# ── Layer 1 rule modules ──────────────────────────────────────────────────────
from sentinel.rules import s1_unicode
from sentinel.rules import s2_comments
from sentinel.rules import s3_mcp_injection
from sentinel.rules import s4_override
from sentinel.rules import s5_exfiltration
from sentinel.rules import s6_new_file
from sentinel.rules import s7_encoding
from sentinel.rules import s8_contradiction
from sentinel.rules import s9_tool_shadow
from sentinel.rules import s10_hook_survivability
from sentinel.rules import s11_bridge_url
from sentinel.rules import s12_trust_delegation
from sentinel.rules import s13_persona_override
from sentinel.rules import s14_write_intercept
from sentinel.rules import s15_slash_command
from sentinel.rules import s16_mcp_autoenable

# ── Layer 0 ───────────────────────────────────────────────────────────────────
from sentinel.layer0.discovery import discover, discover_global_surfaces
from sentinel.layer0.origin import detect_origin


# Files where hook-specific rules apply
_HOOK_FILE_NAMES = frozenset({
    "settings.json",
    ".claude.json",
    "mcp.json",
    ".mcp.json",
})

# Files that are plain-text instruction surfaces (markdown, cursorrules, etc.)
_INSTRUCTION_EXTENSIONS = frozenset({
    ".md", ".cursorrules", ".windsurfrules", ".txt", ".mdc"
})

# Files that are JSON configs (MCP, settings)
_JSON_EXTENSIONS = frozenset({".json"})


def is_agent_config(path: Path) -> bool:
    """Returns True if this path is an agent-trust surface Sentinel should scan."""
    name_lower = path.name.lower()
    from sentinel.layer0.discovery import _EXACT_NAMES, _RELEVANT_EXTENSIONS
    return (
        name_lower in _EXACT_NAMES or
        path.suffix.lower() in _RELEVANT_EXTENSIONS
    )


def scan_file(
    path: Path,
    text: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> ScanResult:
    """
    Scan a single file (D2 -> S1..S16).

    Parameters
    ----------
    path:
        Path to the file (used for D2 origin check and rule scoping).
    text:
        Pre-read file content. If None, reads from disk.
    project_root:
        Project root for origin detection. If None, uses path.parent.
    """
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit
    if text is None:
        try:
            if path.exists() and path.stat().st_size > MAX_FILE_SIZE:
                return ScanResult(filename=str(path))
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ScanResult(filename=str(path))
    else:
        if len(text) > MAX_FILE_SIZE:
            text = text[:MAX_FILE_SIZE]

    filename = str(path)
    name_lower = path.name.lower()
    ext_lower = path.suffix.lower()

    result = ScanResult(filename=filename)

    # ── D2: Origin detection ──────────────────────────────────────────────────
    root = project_root or path.parent
    result.origin = detect_origin(path, root)

    findings: list[Finding] = []

    # ── S1: Invisible Unicode (all text files) ────────────────────────────────
    if ext_lower not in {".json"}:
        findings.extend(s1_unicode.scan(text, filename))

    # ── S2: Hidden comments (markdown / plain text files) ────────────────────
    if ext_lower in _INSTRUCTION_EXTENSIONS:
        findings.extend(s2_comments.scan(text, filename))

    # ── S3: MCP injection (JSON files) ───────────────────────────────────────
    if ext_lower in _JSON_EXTENSIONS:
        findings.extend(s3_mcp_injection.scan(text, filename))

    # ── S4: Override phrasing (text + markdown files) ─────────────────────────
    if ext_lower in _INSTRUCTION_EXTENSIONS:
        findings.extend(s4_override.scan(text, filename))

    # ── S5: Exfiltration patterns (text + markdown) ───────────────────────────
    if ext_lower in _INSTRUCTION_EXTENSIONS:
        findings.extend(s5_exfiltration.scan(text, filename))

    # 🟢 S6: New / modified file in dependency PR
    findings.extend(s6_new_file.scan(text, filename, result.origin))

    # ── S7: Encoded payload (all text files) ─────────────────────────────────
    findings.extend(s7_encoding.scan(text, filename))

    # S8 requires multi-file context — omit here, called from API layer

    # ── S9: Tool shadowing (JSON files) ──────────────────────────────────────
    if ext_lower in _JSON_EXTENSIONS:
        findings.extend(s9_tool_shadow.scan(text, filename))

    # ── S10: Hook survivability (settings.json files) ─────────────────────────
    if name_lower == "settings.json" or ".claude" in filename.lower():
        findings.extend(s10_hook_survivability.scan(text, filename))

    # ── S11: Bridge/C2 URL (JSON files) ──────────────────────────────────────
    if ext_lower in _JSON_EXTENSIONS:
        findings.extend(s11_bridge_url.scan(text, filename))

    # ── S12: External trust delegation (text + markdown) ─────────────────────
    if ext_lower in _INSTRUCTION_EXTENSIONS:
        findings.extend(s12_trust_delegation.scan(text, filename))

    # ── S13: Persona override (text + markdown) ───────────────────────────────
    if ext_lower in _INSTRUCTION_EXTENSIONS:
        findings.extend(s13_persona_override.scan(text, filename))

    # ── S14: Write-intercept hook (settings.json files) ──────────────────────
    if name_lower == "settings.json" or ".claude" in filename.lower():
        findings.extend(s14_write_intercept.scan(text, filename))

    # ✨ S15: Slash command (files in .claude/commands/ and settings.json) ──────────────────────
    if (".claude" in filename.lower() and "commands" in filename.lower()) or name_lower == "settings.json" or name_lower == "claude.json":
        findings.extend(s15_slash_command.scan(text, filename))

    # ── S16: enableAllProjectMcpServers (JSON files) ──────────────────────────
    if ext_lower in _JSON_EXTENSIONS:
        findings.extend(s16_mcp_autoenable.scan(text, filename))

    result.findings = findings
    return result


def scan_directory(
    root: Path,
    hooks_only: bool = False,
    project_root: Optional[Path] = None,
) -> list[ScanResult]:
    """
    Full D1 + D3 + L1 pipeline for a directory.

    Parameters
    ----------
    root:
        Directory to scan.
    hooks_only:
        If True, only scan .claude/settings.json and ~/.claude/settings.json
        (the --hooks-only CLI mode for ChainDrop/Miasma detection).
    project_root:
        Passed to scan_file for origin detection. Defaults to root.
    """
    if project_root is None:
        project_root = root

    if hooks_only:
        # Only scan hook surfaces
        surfaces = []
        project_settings = root / ".claude" / "settings.json"
        if project_settings.exists():
            surfaces.append(project_settings)
        # Also include global settings
        from pathlib import Path as P
        import sys
        if not sys.platform.startswith("win"):
            global_settings = P.home() / ".claude" / "settings.json"
            if global_settings.exists():
                surfaces.append(global_settings)
        # Also include ~/.claude.json (Mitiga Labs vector)
        claude_json = P.home() / ".claude.json"
        if claude_json.exists():
            surfaces.append(claude_json)
    else:
        # Full D1 discovery
        surfaces = discover(root)
        # Add global surfaces for comprehensive scan
        surfaces.extend(discover_global_surfaces())

    results: list[ScanResult] = []
    for path in surfaces:
        result = scan_file(path, project_root=project_root)
        results.append(result)

    return results


def scan_multi_files(files_text: dict[str, str]) -> list[ScanResult]:
    """
    Scan multiple files simultaneously, enabling S8 cross-file contradiction detection.

    Parameters
    ----------
    files_text:
        {filename: full_text} for all files in the batch.
    """
    results: list[ScanResult] = []
    # First pass: scan each file individually
    file_results: dict[str, ScanResult] = {}
    for fname, text in files_text.items():
        path = Path(fname)
        result = scan_file(path, text=text)
        file_results[fname] = result

    # S8: cross-file contradiction detection
    from sentinel.rules.s8_contradiction import scan_multi as s8_multi
    s8_findings = s8_multi(files_text)
    for finding in s8_findings:
        if finding.filename in file_results:
            file_results[finding.filename].findings.append(finding)

    return list(file_results.values())
