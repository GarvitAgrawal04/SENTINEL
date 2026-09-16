"""
layer3 — Anthropic-powered AI-agent instruction file security analyzer.

Public API
----------
from layer3 import analyze

result = analyze(
    filename="CLAUDE.md",
    declared_purpose="project coding instructions",
    layer1_findings_summary="S4 fired, line 4: override/concealment phrasing detected",
    content="<file text here>",
)
"""

from layer3.analyzer import analyze

__all__ = ["analyze"]
