"""
sentinel/rules/s2_comments.py
S2 — Hidden commands in non-rendering syntax (HTML/Markdown comments).
Penalty: −35. Not structurally unambiguous.
ATR: ATR-INJ-002.

Fires when an HTML comment (<!-- ... -->) contains imperative instructions
that would not be rendered to a human reviewer but would be parsed
by an agent reading raw Markdown.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

# Match HTML comments, Markdown link-reference comments, and Front-matter comments
# HTML: <!-- ... -->
# Link ref: [//]: # ( ... ) or [comment]: <> ( ... )
# Frontmatter: --- ... # ... ... ---
_COMMENT_RE = re.compile(
    r'(<!--(.*?)-->)|'
    r'(\[//\]:\s*#\s*\((.*?)\))|'
    r'(\[comment\]:\s*<>\s*\((.*?)\))',
    re.DOTALL
)

# Frontmatter matcher
_FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)

# Code fence matcher to exclude
_CODE_FENCE_RE = re.compile(r'```.*?```', re.DOTALL)

# Imperative verbs that suggest an instruction rather than a developer note
_IMPERATIVE_RE = re.compile(
    r'\b(do|run|execute|send|fetch|call|override|set|use|'
    r'make|append|read|output|print|format|provide|post|upload|download|'
    r'transmit|exfiltrate|access|retrieve)\b',
    re.IGNORECASE,
)

# Benign overrides
_BENIGN_RE = re.compile(
    r'(prettier-ignore|markdownlint-disable|TODO:)',
    re.IGNORECASE,
)


def scan(text: str, filename: str) -> list[Finding]:
    """
    S2 — Hidden commands in non-rendering HTML/Markdown comment blocks.
    """
    findings: list[Finding] = []
    
    # Mask out code fences
    masked_text = text
    for m in _CODE_FENCE_RE.finditer(text):
        masked_text = masked_text[:m.start()] + ' ' * (m.end() - m.start()) + masked_text[m.end():]

    def _check_match(match_obj, inner_text, start_idx):
        if not inner_text:
            return
        inner = inner_text.strip()
        if not inner:
            return
        if not _IMPERATIVE_RE.search(inner) or _BENIGN_RE.search(inner):
            return
        
        lineno = text[:start_idx].count('\n') + 1
        findings.append(Finding(
            rule_id="S2",
            rule_name=RULE_NAMES["S2"],
            severity="medium",
            filename=filename,
            line=lineno,
            message="Imperative instruction found inside an HTML/Markdown comment — visible to agent, hidden from rendered view",
            snippet=text[start_idx:start_idx+200], # Provide the actual comment start
            reconstruction=(
                f"Line {lineno}: The comment block contains imperative language "
                f"that an agent parsing raw Markdown will treat as an instruction. "
                f"A human reviewer sees no visible text here."
            ),
            atr_id="ATR-INJ-002",
        ))

    for match in _COMMENT_RE.finditer(masked_text):
        inner = match.group(2) or match.group(4) or match.group(6)
        _check_match(match, inner, match.start())
        
    # Check frontmatter
    fm_match = _FRONTMATTER_RE.search(masked_text)
    if fm_match:
        fm_content = fm_match.group(1)
        # Find comments in frontmatter
        for line_match in re.finditer(r'^#\s*(.*?)$', fm_content, re.MULTILINE):
            _check_match(line_match, line_match.group(1), fm_match.start(1) + line_match.start(1))

    return findings
