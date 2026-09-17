import pytest
from sentinel.layer3 import (
    Exemplar,
    RetrievalResult,
    BaselineClassification,
    AgentImpact,
    ClassifierPrediction,
    Layer3Result,
    ClassifierStatus
)

def test_layer3_contracts():
    ex = Exemplar("ex-1", "malicious", "S10", "Missing hook", [0.1, 0.2])
    rr = RetrievalResult(ex, 0.95)
    bc = BaselineClassification([rr], "malicious", 0.95)
    
    ai = AgentImpact(
        affected_surface="settings.json",
        affected_behavior="Hook exfiltration",
        security_mechanism="Hook integrity",
        evidence_chain=["L1_S10"],
        structured_summary="Detected missing hook"
    )
    
    cp = ClassifierPrediction("unknown", 0.0, ClassifierStatus.NOT_PROMOTED, None)
    
    res = Layer3Result(
        baseline_classification=bc,
        agent_impact=ai,
        classifier_prediction=cp,
        escalation_required=False
    )
    
    assert res.baseline_classification.inferred_label == "malicious"
    assert res.agent_impact.affected_surface == "settings.json"
    assert res.classifier_prediction.status == ClassifierStatus.NOT_PROMOTED
