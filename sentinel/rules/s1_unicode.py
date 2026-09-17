"""
sentinel/rules/s1_unicode.py
S1 — Invisible Unicode (zero-width, directional-override, Tags block, PUA var-selectors).
Penalty: −50. Structurally unambiguous → forces COMPROMISED.
ATR: AML.T0067, ATR-INJ-001.

Detection set matches TrapDoor's exact mechanism (U+200B/C/D, U+FEFF, U+202A–E)
plus the complete invisible/non-printing set from the PRD §13.2 table.
"""
from __future__ import annotations
from .base import Finding, RULE_NAMES

# ── Zero-width / invisible Unicode codepoints ─────────────────────────────────
# PRD: "U+200B/C/D, U+FEFF, U+202A–E, Tags block, PUA var-selectors"
ZERO_WIDTH_CHARS: frozenset[str] = frozenset({
    '\u200b',  # ZERO WIDTH SPACE
    '\u200c',  # ZERO WIDTH NON-JOINER
    '\u200d',  # ZERO WIDTH JOINER
    '\u200e',  # LEFT-TO-RIGHT MARK
    '\u200f',  # RIGHT-TO-LEFT MARK
    '\u202a',  # LEFT-TO-RIGHT EMBEDDING
    '\u202b',  # RIGHT-TO-LEFT EMBEDDING
    '\u202c',  # POP DIRECTIONAL FORMATTING
    '\u202d',  # LEFT-TO-RIGHT OVERRIDE
    '\u202e',  # RIGHT-TO-LEFT OVERRIDE
    '\ufeff',  # ZERO WIDTH NO-BREAK SPACE (BOM)
    '\u2060',  # WORD JOINER
    '\u2061',  # FUNCTION APPLICATION
    '\u2062',  # INVISIBLE TIMES
    '\u2063',  # INVISIBLE SEPARATOR
    '\u2064',  # INVISIBLE PLUS
})

# Tags block: U+E0000–U+E007F (invisible tag characters)
TAGS_BLOCK_START = 0xE0000
TAGS_BLOCK_END   = 0xE007F

# Variation selectors that are invisible: U+FE00–U+FE0F and U+E0100–U+E01EF
VS_START_1, VS_END_1 = 0xFE00, 0xFE0F
VS_START_2, VS_END_2 = 0xE0100, 0xE01EF


def _is_invisible(ch: str) -> bool:
    if ch in ZERO_WIDTH_CHARS:
        return True
    cp = ord(ch)
    if TAGS_BLOCK_START <= cp <= TAGS_BLOCK_END:
        return True
    if VS_START_1 <= cp <= VS_END_1:
        # Ignore VS-16 (U+FE0F) commonly used for emojis
        if cp == 0xFE0F:
            return False
        return True
    if VS_START_2 <= cp <= VS_END_2:
        return True
    return False


def scan(text: str, filename: str) -> list[Finding]:
    """
    S1 — Zero-width / invisible Unicode detector.

    Produces one Finding per line that contains at least one invisible character.
    Each finding lists the exact Unicode codepoints detected so the output is
    actionable for remediation.

    Agent-impact reconstruction: invisible characters in a CLAUDE.md are a
    confirmed TrapDoor / GlassWorm delivery mechanism — the agent parser sees
    them while the human reviewer cannot.
    """
    findings: list[Finding] = []
    
    # Process line by line, but also keep track of global offset
    offset = 0
    
    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        # We need to find individual invisible chars or contiguous blocks
        hits = []
        for i, ch in enumerate(line):
            if _is_invisible(ch):
                # Check for BOM at offset 0
                if ch == '\ufeff' and offset + i == 0:
                    continue
                hits.append((i, ch))
                
        if not hits:
            offset += len(line)
            continue
            
        codepoints = ", ".join(f"U+{ord(c):04X}" for _, c in sorted(set(hits), key=lambda x: ord(x[1])))
        
        # Tags block decoding
        decoded_tags = ""
        for _, ch in hits:
            cp = ord(ch)
            if TAGS_BLOCK_START <= cp <= TAGS_BLOCK_END:
                decoded_tags += chr(cp - 0xE0000)
                
        reconstruction = (
            f"Line {lineno} contains {len(hits)} invisible Unicode character(s) "
            f"({codepoints}). These characters are consumed by the agent parser "
            f"but invisible in every rendered view, editor, and diff viewer. "
            f"This is TrapDoor's exact mechanism for hiding instructions."
        )
        
        snippet = repr(line[:120])
        if decoded_tags:
            snippet = f"{snippet} (Decoded: {decoded_tags})"
            
        findings.append(Finding(
            rule_id="S1",
            rule_name=RULE_NAMES["S1"],
            severity="high",
            filename=filename,
            line=lineno,
            message=(
                f"{len(hits)} invisible Unicode character(s) — "
                f"hidden from rendered view, consumed by agent parser. "
                f"Codepoints: {codepoints}"
            ),
            snippet=snippet,
            reconstruction=reconstruction,
            atr_id="AML.T0067 / ATR-INJ-001",
            offset=offset + hits[0][0]
        ))
        offset += len(line)
    return findings
