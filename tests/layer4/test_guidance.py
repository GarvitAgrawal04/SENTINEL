import pytest
from sentinel.rules.base import ScanResult, Finding
from sentinel.layer4.guide import generate_guide, GuideResult
from sentinel.scoring.formula import DisplacementResult

def test_s10_guidance():
    sr = ScanResult(
        filename="test.json",
        findings=[Finding(rule_id="S10", rule_name="hook", filename="test.json", line=1, message="Missing path", severity="high", snippet="hook.js")]
    )
    guide = generate_guide(sr)
    assert guide.verdict == "COMPROMISED"
    assert "Verify the hook configuration and referenced script" in guide.guidance_items[0].remediation

def test_s11_redaction():
    sr = ScanResult(
        filename="test.json",
        findings=[Finding(rule_id="S11", rule_name="url", filename="test.json", line=1, message="C2 URL", severity="high", snippet="https://evil.com/token=123")]
    )
    guide = generate_guide(sr)
    assert guide.verdict == "COMPROMISED"
    assert "[REDACTED" in guide.guidance_items[0].evidence_snippet
    assert "evil.com" not in guide.guidance_items[0].evidence_snippet
    assert "Rotate the exposed credential immediately" in guide.guidance_items[0].remediation

def test_s14b_vs_s14a():
    # S14a - missing path
    sr_a = ScanResult(filename="f", findings=[Finding(rule_id="S14a", rule_name="write", filename="f", line=1, message="", severity="high", snippet="")])
    g_a = generate_guide(sr_a)
    assert g_a.verdict == "COMPROMISED"
    
    # S14b - existing path
    sr_b = ScanResult(filename="f", findings=[Finding(rule_id="S14b", rule_name="write", filename="f", line=1, message="", severity="high", snippet="")])
    g_b = generate_guide(sr_b)
    assert g_b.verdict == "SUSPICIOUS"  # Ceiling 60

def test_s16_guidance():
    sr = ScanResult(filename="f", findings=[Finding(rule_id="S16", rule_name="mcp", filename="f", line=1, message="", severity="high", snippet="")])
    g = generate_guide(sr)
    assert g.verdict == "SUSPICIOUS"
    assert "Explicitly allow-list servers" in g.guidance_items[0].remediation

def test_layer2_uncertainty():
    sr = ScanResult(filename="f", findings=[])
    sr.displacement = DisplacementResult(0.5, "SEMANTIC_DIRECTION_UNAVAILABLE")
    g = generate_guide(sr)
    assert "directional attack classification is unavailable" in g.layer2_uncertainty

def test_clean_result():
    sr = ScanResult(filename="f", findings=[])
    g = generate_guide(sr)
    assert g.verdict == "CLEAN"
    assert g.summary == "No anomalous patterns detected."
    assert len(g.guidance_items) == 0

def test_multiple_findings():
    sr = ScanResult(
        filename="test.json",
        findings=[
            Finding(rule_id="S10", rule_name="hook", filename="test.json", line=1, message="", severity="high", snippet=""),
            Finding(rule_id="S10", rule_name="hook", filename="test.json", line=2, message="", severity="high", snippet="")
        ]
    )
    g = generate_guide(sr)
    # Deduplicates
    assert len(g.guidance_items) == 1
