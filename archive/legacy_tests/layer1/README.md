# Sentinel — Layer 1 (DETECT) test suite

Tests for the 16 deterministic rules S1–S16 and the Layer-1 half of the
Trust Score formula, written directly from `SENTINEL_PRD_Master_v3.md`
Sections 13.2, 13.3 (D3 hook schema), 15.1, 15.2, 16 and Appendix E.

```
tests/
├── README.md                ← you are here
├── conftest.py              ← the ONE adapter between tests and your code
├── corpus.py                ← attack + clean samples (Section 15.1 / 15.2 in miniature)
└── layer1/
    ├── test_s1_unicode.py … test_s16_mcp_autoenable.py   (one file per rule)
    ├── test_rule_metadata.py    ← penalties / unambiguous flags / ATR ids == PRD table
    ├── test_formula_l1.py       ← the 4 verified arithmetic examples + clamps + ceilings
    ├── test_clean_corpus.py     ← false-positive guard: every rule × every clean sample = 0 findings
    ├── test_attack_corpus.py    ← every attack sample fires exactly the rules the PRD says
    └── test_performance.py      ← "milliseconds per file" sanity bound
```

## Run

```bash
pip install pytest
pytest tests/layer1 -q                      # everything
pytest tests/layer1/test_s10_hook_survivability.py -v
pytest tests/layer1 -q -m "not perf"        # skip the timing test
```

## The contract your code must satisfy

The tests import three things. Everything else is yours.

### 1. `sentinel/rules/base.py`

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Finding:
    rule_id: str                 # "S1" … "S16"; S14 emits "S14a" or "S14b"
    penalty: int                 # negative int, e.g. -50. 0 for ceiling-only findings (S14b, S16-alone)
    unambiguous: bool            # True => verdict forced to COMPROMISED regardless of arithmetic
    evidence: str                # human-readable; MUST contain the matched text / path / tool name
    path: str                    # the file that was scanned
    offset: int | None = None    # character offset of first match, where meaningful
    ceiling: int | None = None   # 60 for S14b and S16-alone
    atr: tuple[str, ...] = ()    # ATR / ATLAS ids from the PRD table

@dataclass
class ScanContext:
    project_root: Path
    home: Path | None = None                     # for ~/.claude/settings.json, ~/.claude.json
    files: dict[str, str] = field(default_factory=dict)        # every surface file: rel path -> content (S8, S9)
    origin: str = "git"                          # "git" | "postinstall-suspected" | "postinstall-confirmed" | "unknown"  (Layer 0 D2)
    diff_status: dict[str, str] = field(default_factory=dict)  # rel path -> "added" | "modified" | "unchanged"   (S6)
    git_tracked: set[str] = field(default_factory=set)         # rel paths present in git history            (S15)
    trusted_tools: dict[str, dict] = field(default_factory=dict) # from sentinel.lock: tool name -> {"server", "description", "inputSchema"} (S9)
```

### 2. Each rule module `sentinel/rules/sN_*.py`

```python
RULE_ID = "S1"
PENALTY = -50
UNAMBIGUOUS = True
ATR = ("AML.T0067", "ATR-INJ-001")

def check(content: str, path: str, ctx: ScanContext) -> list[Finding]: ...
```

`sentinel/rules/__init__.py` must expose `ALL_RULES`: the 16 modules in order S1…S16.

### 3. `sentinel/scoring/formula.py`

```python
@dataclass
class DisplacementResult:   # Layer 2 input (may be None on first scan / TOFU)
    magnitude: float        # cosine distance 0–1
    direction: str          # "attack" | "benign"

@dataclass
class ScoreResult:
    score: int              # clamp(raw, 0, 100)
    verdict: str            # "CLEAN" | "SUSPICIOUS" | "COMPROMISED"
    breakdown: str          # auditable arithmetic, e.g. "raw=100, L1=0, L2=-6 (0.20×30×1.0), L3=0 → 94"

def compute_trust_score(
    l1_findings: list[Finding],
    displacement: DisplacementResult | None = None,
    l3_confidence_clean: float | None = None,   # 0–1; bonus = confidence × 10, capped per 13.2
) -> ScoreResult: ...
```

If your names differ, edit `run_rule()` / `make_ctx()` / `score()` in `conftest.py` — nothing else.

## Decisions the PRD leaves open (encoded in these tests — flip them if the team decides otherwise)

| Where | Decision taken here | Why |
|---|---|---|
| S1 | A **leading** U+FEFF (Windows BOM at offset 0) does **not** fire; U+FEFF anywhere else does | Otherwise every Windows-authored CLAUDE.md is COMPROMISED |
| S1 | U+FE0F after an emoji does not fire; Variation Selectors Supplement (U+E0100+) does | Emoji VS-16 is everywhere in READMEs |
| S7 | Only fires when the decoded payload is ≥90 % printable text; git SHAs / sha256 / sha512 integrity strings never fire | Unambiguous rule ⇒ must not be a false-positive machine |
| S13 | Concealment language ("don't tell the user about these rules") fires even without an explicit persona line | The concealment is the dangerous part (see `TestPolicyDecisions` in the S13 file) |
| S14/S10 | A missing-path PreToolUse write hook is asserted to fire **S14a**; whether S10 *also* fires on the same hook is not asserted | PRD doesn't say; both are −70 unambiguous so the verdict is identical either way |
| Formula | Verdict thresholds between the PRD's examples (94→CLEAN, 60→SUSPICIOUS, 30→COMPROMISED) are **not pinned** — see the skipped test in `test_formula_l1.py` | PRD 13.2 never states the boundaries. Decide before Round 3. |

All hostnames in fixtures use RFC 2606 reserved domains (`example.com/.net/.org`, `.invalid`, `.test`) — nothing resolves.
