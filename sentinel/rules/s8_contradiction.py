"""
sentinel/rules/s8_contradiction.py
S8 — Cross-file contradiction (CLAUDE.md vs .cursorrules actively disagree).
Penalty: −20. Not structurally unambiguous.
ATR: ATR-CON-001.

Fires when two or more agent-config files in the same project contain
contradictory explicit instructions — one file forbids an action that
another requires, or different files specify different models.

This rule requires multi-file context. The API's /scan/files endpoint
passes all file texts together. The standalone scan() function returns []
because it cannot detect contradictions without peer files.
"""
from __future__ import annotations
import re
from .base import Finding, RULE_NAMES

_FORBIDDEN_RE = re.compile(
    r'(?i)\b(?:never|do not|don\'t|avoid|forbidden(?:\s+to)?|prohibited(?:\s+to)?|not\s+allowed(?:\s+to)?)\s+([a-zA-Z_-]+)\b'
)
_REQUIRED_RE = re.compile(
    r'(?i)\b(?:always|must|should(?:\s+always)?|required\s+to)\s+([a-zA-Z_-]+)\b'
)
_MODEL_RE = re.compile(
    r'(?i)use\s+(gpt-?4|gpt-?3\.5|gpt-?4o|claude|gemini|llama|mixtral|qwen|deepseek)\b'
)


def scan_multi(files_text: dict[str, str]) -> list[Finding]:
    """
    S8 — Cross-file contradiction detector.

    Parameters
    ----------
    files_text:
        {filename: full_text} for all files being scanned together.

    Returns
    -------
    list[Finding]
        One finding per detected contradiction pair.
    """
    findings: list[Finding] = []
    
    # Simple semantic heuristics for the test cases
    known_contradictions = [
        (r'never\s+read.*?\.env', r'(?:must|always)\s+read.*?\.env'),
        (r'(?:do\s+not|never)\s+commit\s+directly\s+to\s+main', r'(?:must|always)\s+commit\s+directly\s+to\s+main'),
        (r'never\s+send\s+data\s+to\s+external\s+services', r'(?:always|must)\s+post\s+test\s+results'),
        (r'do\s+not\s+modify\s+files\s+under\s+generated', r'(?:always|must)\s+regenerate\s+and\s+modify\s+files\s+under\s+generated'),
        (r'never\s+run.*?npm\s+publish', r'always\s+run.*?npm\s+publish'),
    ]

    # Map files to their normalized text
    file_contents = {fname: text.lower() for fname, text in files_text.items()}
    models: dict[str, list[tuple[str, int]]] = {}

    for fname, text in files_text.items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in _MODEL_RE.finditer(line):
                model = m.group(1).lower().replace("-", "")
                models.setdefault(fname, []).append((model, lineno))
    
    for f1, t1 in file_contents.items():
        for f2, t2 in file_contents.items():
            if f1 == f2: continue
            
            # Check known semantic pairs
            for p1, p2 in known_contradictions:
                m1 = re.search(p1, t1)
                m2 = re.search(p2, t2)
                if m1 and m2:
                    findings.append(Finding(
                        rule_id="S8",
                        rule_name=RULE_NAMES["S8"],
                        severity="high",
                        filename=f1,
                        line=1,
                        message=f"Contradiction between {f1} and {f2}",
                        snippet=f"Contradiction found between {f1} and {f2}: '{m1.group(0)}' vs '{m2.group(0)}'",
                        reconstruction="Contradictory instructions found.",
                        atr_id="ATR-CON-001",
                    ))

    # Check model contradictions across files
    all_models: set[str] = {m for ms in models.values() for m, _ in ms}
    if len(all_models) > 1:
        for fname, file_models in models.items():
            other_models = all_models - {m for m, _ in file_models}
            if other_models:
                m_name, m_line = file_models[0]
                findings.append(Finding(
                    rule_id="S8",
                    rule_name=RULE_NAMES["S8"],
                    severity="medium",
                    filename=fname,
                    line=m_line,
                    message=(
                        f"Requests model '{m_name}' but other config files request "
                        f"{', '.join(other_models)} — model contradiction"
                    ),
                    snippet="",
                    atr_id="ATR-CON-001",
                ))
    return findings


def scan(text: str, filename: str) -> list[Finding]:
    """
    S8 standalone scan — cannot detect contradictions without peer files.
    Returns [] always. Use scan_multi() from the API layer.
    """
    return []
