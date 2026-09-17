import pytest
from sentinel.layer3.classifier import DomainAdaptedClassifier
from sentinel.layer3 import ClassifierStatus

def test_classifier_is_not_promoted():
    clf = DomainAdaptedClassifier()
    # Ensure it's not silently replacing the baseline
    assert clf.status == ClassifierStatus.NOT_PROMOTED
    
    pred = clf.predict("test")
    assert pred.status == ClassifierStatus.NOT_PROMOTED
    assert pred.confidence == 0.0
