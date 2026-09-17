"""
sentinel/rules.py
Backward compatibility shim for older scripts (like benchmark/run_benchmark.py)
that expect the old monolithic rules.py exports.
"""
from __future__ import annotations

# Export the core data structures and main scanner
from sentinel.rules.base import Finding, ScanResult
from sentinel.scanner import scan_file, is_agent_config

# Constants that were previously exported here
from sentinel.rules.s1_unicode import ZERO_WIDTH_CHARS
from sentinel.rules.s4_override import OVERRIDE_PATTERNS
from sentinel.rules.s5_exfiltration import EXFIL_PATTERNS
from sentinel.rules.s7_encoding import _ENCODED_RE as ENCODED_PAYLOAD

AGENT_CONFIG_EXTENSIONS = {'.md', '.cursorrules', '.json', '.toml', '.yaml', '.yml', '.txt'}
AGENT_CONFIG_NAMES = {
    'claude.md', 'agents.md', 'gemini.md', 'copilot-instructions.md',
    '.cursorrules', '.windsurfrules', 'mcp.json', 'settings.json',
}
