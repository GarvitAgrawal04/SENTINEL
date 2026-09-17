import pytest
import numpy as np
from sentinel.layer3.classifier import NearestNeighborBaseline, DomainAdaptedClassifier
from sentinel.layer3.exemplar import Exemplar
from sentinel.layer3 import ClassifierStatus

class MockIndex:
    def __init__(self):
        self.exemplars = [
            Exemplar("1", "malicious", "fam1", "desc1", [1.0, 0.0, 0.0]),
            Exemplar("2", "clean", "fam2", "desc2", [0.0, 1.0, 0.0])
        ]

def test_nearest_neighbor_baseline():
    index = MockIndex()
    baseline = NearestNeighborBaseline(index)
    
    # Query matching the malicious exemplar
    res1 = baseline.classify([0.9, 0.1, 0.0], k=1)
    assert res1.inferred_label == "malicious"
    assert res1.confidence > 0.8
    
    # Query matching the clean exemplar
    res2 = baseline.classify([0.0, 0.9, 0.1], k=1)
    assert res2.inferred_label == "clean"
    assert res2.confidence > 0.8

def test_empty_baseline():
    class EmptyIndex:
        exemplars = []
    baseline = NearestNeighborBaseline(EmptyIndex())
    res = baseline.classify([1.0, 0.0, 0.0])
    assert res.inferred_label == "unknown"
    assert res.confidence == 0.0

def test_domain_adapted_classifier_not_promoted():
    # As per PRD constraint and V1 reality: no classifier is trained/promoted yet.
    clf = DomainAdaptedClassifier()
    assert clf.status == ClassifierStatus.NOT_PROMOTED
    
    pred = clf.predict("some text")
    assert pred.status == ClassifierStatus.NOT_PROMOTED
    assert pred.label == "unknown"
    assert pred.confidence == 0.0
