"""
Metadata contract for the 16 Layer-1 rules (PRD 13.2, "Deterministic rule table").

Every `sentinel/rules/sN_*.py` module must publish four module-level constants —
RULE_ID, PENALTY, UNAMBIGUOUS, ATR — and `sentinel/rules/__init__.py` must expose
ALL_RULES as the 16 rule modules in canonical S1..S16 order. This file is the single
place that pins the numbers, so a typo'd penalty or a mis-set unambiguous flag fails
here loudly instead of silently skewing every Trust Score.

Two rules carry per-FINDING metadata rather than one module-level value and are handled
specially:
  * S14 emits S14a (−70, unambiguous) OR S14b (0, ceiling 60) depending on whether the
    hook's target path exists. The exact per-finding values are pinned in
    test_s14_write_intercept.py; here we only require the module constants to exist and
    the ATR mapping to be correct.
  * S16 emits penalty 0 / ceiling 60, escalating to unambiguous only with an install
    origin (pinned in test_s16_mcp_autoenable.py). Same treatment.
"""
import importlib

import pytest

from tests.layer1.conftest import RULE_MODULES

# rule_id -> (penalty, unambiguous, primary_atr)   for the single-valued rules
EXPECTED = {
    "S1":  (-50, True,  "ATR-INJ-001"),
    "S2":  (-35, False, "ATR-INJ-002"),
    "S3":  (-35, False, "ATR-MCP-003"),
    "S4":  (-25, False, "ATR-INJ-004"),
    "S5":  (-40, False, "ATR-EXF-001"),
    "S6":  (-15, False, "ATR-RUG-001"),
    "S7":  (-45, True,  "ATR-OBF-001"),
    "S8":  (-20, False, "ATR-CON-001"),
    "S9":  (-30, False, "ATR-MCP-004"),
    "S10": (-70, True,  "ATR-HOOK-001"),
    "S11": (-70, True,  "ATR-EXF-002"),
    "S12": (-35, False, "ATR-DEL-001"),
    "S13": (-50, True,  "ATR-PER-001"),
    "S15": (-55, False, "ATR-PERSIST-001"),
}

# rules whose penalty/unambiguous are decided per finding, not per module
PER_FINDING_ATR = {
    "S14": "ATR-HOOK-002",
    "S16": "ATR-MCP-005",
}

ALL_RULE_IDS = [f"S{i}" for i in range(1, 17)]


def _module(rule_id: str):
    return importlib.import_module(f"sentinel.rules.{RULE_MODULES[rule_id]}")


def _atr_tuple(mod) -> tuple:
    atr = getattr(mod, "ATR")
    # A single string is tolerated but a tuple/list is the contract.
    return (atr,) if isinstance(atr, str) else tuple(atr)


# --- determinate rules -------------------------------------------------------
@pytest.mark.parametrize("rule_id", list(EXPECTED))
def test_module_constants_match_prd(rule_id):
    penalty, unambiguous, atr = EXPECTED[rule_id]
    mod = _module(rule_id)
    assert mod.RULE_ID == rule_id, f"{rule_id}: RULE_ID mismatch"
    assert mod.PENALTY == penalty, f"{rule_id}: penalty should be {penalty}"
    assert mod.UNAMBIGUOUS is unambiguous, f"{rule_id}: unambiguous should be {unambiguous}"
    assert atr in _atr_tuple(mod), f"{rule_id}: ATR {atr} missing from {mod.ATR!r}"


def test_s1_maps_to_atlas_technique():
    """S1 additionally carries the MITRE ATLAS technique for invisible-Unicode injection."""
    assert "AML.T0067" in _atr_tuple(_module("S1"))


# --- per-finding rules -------------------------------------------------------
@pytest.mark.parametrize("rule_id, atr", PER_FINDING_ATR.items())
def test_per_finding_rule_metadata_present(rule_id, atr):
    mod = _module(rule_id)
    assert isinstance(mod.RULE_ID, str) and mod.RULE_ID
    assert isinstance(mod.PENALTY, int)
    assert isinstance(mod.UNAMBIGUOUS, bool)
    assert atr in _atr_tuple(mod), f"{rule_id}: ATR {atr} missing from {mod.ATR!r}"


# --- registry ----------------------------------------------------------------
def test_all_rules_registry_is_complete_and_ordered():
    from sentinel.rules import ALL_RULES

    seen = [getattr(mod, "RULE_ID") for mod in ALL_RULES]
    assert len(ALL_RULES) == 16, f"expected 16 rules, got {len(ALL_RULES)}"
    # S14/S16 module RULE_ID may be 'S14'/'S16'; accept the base id in canonical order.
    normalised = [rid[:3] if rid.startswith(("S14", "S16")) else rid for rid in seen]
    assert normalised == ALL_RULE_IDS, f"ALL_RULES out of order: {seen}"


@pytest.mark.parametrize("rule_id", ALL_RULE_IDS)
def test_every_module_has_check_callable(rule_id):
    mod = _module(rule_id)
    assert callable(getattr(mod, "check")), f"{rule_id}: check() missing"
