"""
sentinel/rules/base.py
Shared dataclasses, constants, and registry for Layer 1 rules.

Every Layer 1 rule function must return a list[Finding].
A Finding contains everything needed for scoring, output, and manifest.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ── PRD Table 13.2 ────────────────────────────────────────────────────────────
# Penalty for each rule. None = uses a ceiling instead of a deduction.
RULE_PENALTIES: dict[str, Optional[int]] = {
    "S1":  50,   # invisible Unicode — forces COMPROMISED
    "S2":  35,   # hidden commands in non-rendering syntax
    "S3":  35,   # MCP tool description injection
    "S4":  25,   # override/jailbreak phrasing
    "S5":  40,   # network-shaped instruction (exfiltration URL)
    "S6":  15,   # new/modified file in dependency PR
    "S7":  45,   # encoded payload (base64, hex) — forces COMPROMISED
    "S8":  20,   # cross-file contradiction
    "S9":  30,   # tool shadowing
    "S10": 70,   # hook referencing missing path — forces COMPROMISED
    "S11": 70,   # hardcoded bridge/C2 URL — forces COMPROMISED
    "S12": 35,   # external trust delegation
    "S13": 50,   # persona override + self-concealment — forces COMPROMISED
    "S14a": 70,  # write-intercept hook, missing path — forces COMPROMISED
    "S14b": None,  # write-intercept hook, existing path — ceiling 60
    "S15": 55,   # deposited slash command
    "S16": None,  # enableAllProjectMcpServers:true — ceiling 60 (or COMPROMISED if +postinstall)
}

# S1, S7, S10, S11, S13, S14a → force COMPROMISED regardless of score
STRUCTURALLY_UNAMBIGUOUS: frozenset[str] = frozenset({"S1", "S7", "S10", "S11", "S13", "S14a"})

# S14b and S16 alone → cap score at 60 (cannot be CLEAN; not forced COMPROMISED)
CEILING_RULES: frozenset[str] = frozenset({"S14b", "S16"})

RULE_NAMES: dict[str, str] = {
    "S1":  "Invisible Unicode",
    "S2":  "Hidden Commands in Non-Rendering Syntax",
    "S3":  "MCP Tool Description Injection",
    "S4":  "Override / Jailbreak Phrasing",
    "S5":  "Network-Shaped Instruction (Exfiltration URL)",
    "S6":  "New / Modified File in Dependency PR",
    "S7":  "Encoded Payload (Base64 / Hex)",
    "S8":  "Cross-File Contradiction",
    "S9":  "Tool Shadowing (Deadbugz Pattern)",
    "S10": "Hook References Missing Path",
    "S11": "Hardcoded Bridge / C2 URL or Auth Token",
    "S12": "External Trust Delegation",
    "S13": "Persona Override with Self-Concealment",
    "S14a": "Write-Intercept Hook — Missing Script Path",
    "S14b": "Write-Intercept Hook — Existing Script Path",
    "S15": "Deposited Slash Command",
    "S16": "enableAllProjectMcpServers: true",
}


@dataclass
class Finding:
    """
    One rule firing against one file.

    Every field here feeds scoring, formatter output, and sentinel.lock.
    No field should be None unless it is genuinely inapplicable.
    """
    rule_id: str          # e.g. "S10"
    rule_name: str        # human-readable name from RULE_NAMES
    severity: str         # "high" | "medium" | "low"
    filename: str         # path of the scanned file
    line: int             # line number where the evidence appears (1-indexed; 0 = whole file)
    message: str          # one-line description of what was found
    snippet: str          # raw evidence text (truncated if needed)
    penalty: Optional[int] = None     # None for ceiling-only rules
    ceiling: Optional[int] = None     # 60 for S14b and S16
    forces_compromised: bool = False  # True for structurally unambiguous rules
    reconstruction: Optional[str] = None  # PRD §13.5 agent-impact reconstruction

    # ATR mapping — informational, not enforced
    atr_id: Optional[str] = None

    offset: Optional[int] = None

    def __post_init__(self) -> None:
        # Auto-populate penalty, ceiling, forces_compromised from PRD table
        # only if they were not explicitly set to a non-default value by the rule
        if getattr(self, "penalty", None) is None:
            self.penalty = RULE_PENALTIES.get(self.rule_id)
            
        # forces_compromised defaults to False in dataclass, so we check if it's explicitly set to True
        if getattr(self, "forces_compromised", False) is False:
            self.forces_compromised = self.rule_id in STRUCTURALLY_UNAMBIGUOUS
            
        if self.ceiling is None and self.rule_id in CEILING_RULES:
            self.ceiling = 60

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "filename": self.filename,
            "line": self.line,
            "message": self.message,
            "snippet": self.snippet,
            "penalty": self.penalty,
            "ceiling": self.ceiling,
            "forces_compromised": self.forces_compromised,
            "reconstruction": self.reconstruction,
            "atr_id": self.atr_id,
        }


@dataclass
class ScanResult:
    """
    Full result for one scanned file.

    Scoring is deferred to sentinel.scoring.formula — this class is a data
    carrier only. Do not put scoring logic here.
    """
    filename: str
    findings: list[Finding] = field(default_factory=list)
    layer2_delta_pct: Optional[float] = None  # from Layer 2 (if available)
    layer3_result: Optional[dict] = None       # from Layer 3 (if available)
    origin: str = "unknown"                    # D2 origin label

    def to_dict(self) -> dict:
        """Produce the JSON-serializable dict that the API returns.

        This dict is the external contract consumed by the frontend,
        VS Code extension, and GitHub Action.  Add fields additively;
        never remove or rename existing keys.
        """
        from sentinel.scoring.formula import compute_score, compute_verdict
        trust_score = compute_score(self)
        verdict = compute_verdict(self, trust_score)
        return {
            "filename": self.filename,
            "trust_score": trust_score,
            "color_band": verdict.lower() if verdict == "CLEAN" else (
                "red" if verdict == "COMPROMISED" else "amber"
            ),
            "verdict": verdict,
            "findings": [f.to_dict() for f in self.findings],
            "layer3_result": self.layer3_result,
            "origin": self.origin,
        }

    # ── Backward compatibility methods ────────────────────────────────────────
    # These exist so that benchmark/run_benchmark.py and other existing code
    # that calls scan_result.trust_score() continues to work without modification.

    def trust_score(self) -> int:
        """Backward-compat alias. New code should use sentinel.scoring.formula.compute_score()."""
        from sentinel.scoring.formula import compute_score
        return compute_score(self)

    def color_band(self) -> str:
        """Backward-compat alias. Returns 'red'|'amber'|'green'."""
        from sentinel.scoring.formula import compute_score, compute_verdict
        score = compute_score(self)
        verdict = compute_verdict(self, score)
        return "red" if verdict == "COMPROMISED" else ("amber" if verdict == "SUSPICIOUS" else "green")

