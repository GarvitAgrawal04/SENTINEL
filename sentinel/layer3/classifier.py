from typing import List, Optional
import numpy as np

from sentinel.layer3 import (
    BaselineClassification,
    RetrievalResult,
    Exemplar,
    ClassifierPrediction,
    ClassifierStatus
)
from sentinel.layer2.displacement import cosine_distance

class NearestNeighborBaseline:
    def __init__(self, index):
        """Expects an instantiated ExemplarIndex."""
        self.index = index

    def classify(self, query_embedding: List[float], k: int = 1) -> BaselineClassification:
        if not self.index.exemplars:
            # Handle empty index gracefully
            return BaselineClassification(
                nearest_exemplars=[],
                inferred_label="unknown",
                confidence=0.0
            )

        query_arr = np.array(query_embedding, dtype=np.float32)
        results = []

        for ex in self.index.exemplars:
            ex_arr = np.array(ex.embedding, dtype=np.float32)
            dist = cosine_distance(query_arr, ex_arr)
            # Similarity is logically 1.0 - distance
            # Bounded between 0 and 1 since dist is [0, 2] usually but clipped to [0, 1] practically in Layer 2
            sim = max(0.0, 1.0 - dist)
            results.append(RetrievalResult(exemplar=ex, similarity=sim))

        # Sort by highest similarity
        results.sort(key=lambda r: r.similarity, reverse=True)
        top_k = results[:k]
        
        # Inferred label from the nearest neighbor
        best_match = top_k[0]
        
        return BaselineClassification(
            nearest_exemplars=top_k,
            inferred_label=best_match.exemplar.label,
            confidence=best_match.similarity
        )

class DomainAdaptedClassifier:
    """
    Optional Domain-Adapted Classifier (3a-ii).
    Currently NOT PROMOTED because we have not validated it against the baseline.
    """
    def __init__(self):
        self.status = ClassifierStatus.NOT_PROMOTED

    def predict(self, text: str) -> ClassifierPrediction:
        # V1 DEFECT / ARCHITECTURAL BOUNDARY:
        # The optional classifier is absent/unpromoted.
        # We explicitly return NOT_PROMOTED and 0.0 confidence.
        return ClassifierPrediction(
            label="unknown",
            confidence=0.0,
            status=self.status,
            model_version=None
        )