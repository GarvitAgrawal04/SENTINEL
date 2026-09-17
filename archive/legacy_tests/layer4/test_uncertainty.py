import pytest
from sentinel.rules.base import ScanResult, Finding
from sentinel.layer4.guide import generate_guide

def test_missing_snippet():
    sr = ScanResult(
        filename="test.json",
        findings=[Finding(rule_id="S10", rule_name="hook", filename="test.json", line=1, message="Msg", severity="high", snippet="")]
    )
    g = generate_guide(sr)
    assert g.guidance_items[0].evidence_snippet == "Evidence unavailable."

def test_layer2_absent():
    sr = ScanResult(filename="test.json", findings=[])
    g = generate_guide(sr)
    assert g.layer2_uncertainty == "Layer 2 displacement analysis not performed."

def test_layer3_absent():
    sr = ScanResult(filename="test.json", findings=[])
    g = generate_guide(sr)
    assert g.layer3_status == "Layer 3 analysis unavailable."
    
def test_unknown_rule_id():
    sr = ScanResult(
        filename="test.json",
        findings=[Finding(rule_id="S99", rule_name="unknown", filename="test.json", line=1, message="Msg", severity="high", snippet="abc")]
    )
    g = generate_guide(sr)
    assert g.guidance_items[0].remediation == "Review the flagged finding and modify the file to adhere to security best practices."
