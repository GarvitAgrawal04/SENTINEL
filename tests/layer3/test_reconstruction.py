import pytest
from sentinel.layer3.reconstruction import reconstruct_impact
from sentinel.rules.base import Finding
from sentinel.layer2 import Layer2Result, DiffResult, FileChangeType, SemanticDisplacement

def test_reconstruct_structural_only():
    findings = [Finding(rule_id="S10", rule_name="missing_hook", filename=".claude/settings.json", line=5, message="Missing path in hook", severity=0, snippet="")]
    impact = reconstruct_impact(".claude/settings.json", findings)
    
    assert impact is not None
    assert impact.affected_surface == ".claude/settings.json"
    assert "Hook execution reference to missing path" in impact.affected_behavior
    assert "Hook Survivability" in impact.security_mechanism
    assert "L1_S10" in impact.evidence_chain[0]
    assert "severe structural bypass attempt" in impact.structured_summary

def test_reconstruct_with_layer2_placeholder():
    findings = []
    l2_res = Layer2Result(
        diffs=[DiffResult("CLAUDE.md", FileChangeType.MODIFIED, "hash1", "hash2")],
        displacements=[SemanticDisplacement("CLAUDE.md", 0.8, "SEMANTIC_DIRECTION_UNAVAILABLE", 0.0)]
    )
    
    impact = reconstruct_impact("CLAUDE.md", findings, l2_res)
    assert impact is not None
    # Verify we did NOT hallucinate an attack
    assert any("L2_DIRECTION: Unavailable" in ev for ev in impact.evidence_chain)
    assert "Significant semantic deviation" in impact.affected_behavior
    assert "severe structural bypass" not in impact.structured_summary

def test_reconstruct_empty():
    assert reconstruct_impact("CLAUDE.md", [], None) is None
