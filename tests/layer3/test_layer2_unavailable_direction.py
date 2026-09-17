import pytest
from sentinel.layer2 import SemanticDisplacement
from sentinel.scoring.formula import compute_score, DisplacementResult
from sentinel.rules.base import ScanResult
from sentinel.layer3.reconstruction import reconstruct_impact
from sentinel.layer2 import Layer2Result

def test_layer2_unavailable_direction_handling():
    # 1. Ensure displacement uses 'unavailable' and distance is kept.
    disp = SemanticDisplacement("f", 0.9, "SEMANTIC_DIRECTION_UNAVAILABLE", 0.0)
    assert disp.direction == "SEMANTIC_DIRECTION_UNAVAILABLE"
    assert disp.cosine_distance == 0.9
    
    # 2. Formula integration MUST KEEP multiplier 1.0 if not explicit 'attack'
    dr = DisplacementResult(magnitude=disp.cosine_distance, direction=disp.direction)
    scan_res = ScanResult(filename="f", findings=[])
    scan_res.displacement = dr
    
    # Score should be 100 - (0.9 * 30 * 1.0) = 73
    score = compute_score(scan_res)
    assert score == 73
    
    # 3. No component converts unavailable into attack
    l2_res = Layer2Result(diffs=[], displacements=[disp])
    impact = reconstruct_impact("f", [], l2_res)
    
    # Should not assert an attack solely based on 0.9 displacement
    for ev in impact.evidence_chain:
        assert "attack" not in ev.lower()
    
    assert "L2_DIRECTION: Unavailable" in "".join(impact.evidence_chain)
