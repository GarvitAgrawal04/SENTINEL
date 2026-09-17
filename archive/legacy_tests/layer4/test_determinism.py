import pytest
from sentinel.rules.base import ScanResult, Finding
from sentinel.layer4.guide import generate_guide

def test_guide_determinism():
    sr = ScanResult(
        filename="test.json",
        findings=[
            Finding(rule_id="S11", rule_name="url", filename="test.json", line=1, message="C2", severity="high", snippet="secret123")
        ]
    )
    
    g1 = generate_guide(sr)
    g2 = generate_guide(sr)
    
    assert g1.verdict == g2.verdict
    assert g1.summary == g2.summary
    assert len(g1.guidance_items) == len(g2.guidance_items)
    assert g1.guidance_items[0].remediation == g2.guidance_items[0].remediation
    assert g1.guidance_items[0].evidence_snippet == g2.guidance_items[0].evidence_snippet
    assert "secret123" not in g1.guidance_items[0].evidence_snippet
