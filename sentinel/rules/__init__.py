"""
sentinel/rules/__init__.py
Re-exports the shared Finding dataclass and scan_file orchestrator.
"""
from __future__ import annotations
from .base import Finding, ScanResult, STRUCTURALLY_UNAMBIGUOUS, CEILING_RULES

AGENT_CONFIG_EXTENSIONS = {'.md', '.cursorrules', '.json', '.toml', '.yaml', '.yml', '.txt'}
AGENT_CONFIG_NAMES = {
    'claude.md', 'agents.md', 'gemini.md', 'copilot-instructions.md',
    '.cursorrules', '.windsurfrules', 'mcp.json', 'settings.json',
}
