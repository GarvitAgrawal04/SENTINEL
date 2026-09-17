import pytest
import numpy as np

from sentinel.layer2.displacement import compute_embedding, cosine_distance, compute_displacement, ModelUnavailableError
from sentinel.layer2 import SemanticDisplacement

@pytest.fixture(autouse=True)
def mock_sentence_transformers(monkeypatch):
    """Mock the model to prevent massive downloads during tests, unless we actually want to test the real model."""
    class MockModel:
        def encode(self, text, normalize_embeddings=False):
            # Deterministic dummy embedding based on string length and basic hash
            np.random.seed(len(text) + sum(ord(c) for c in text))
            vec = np.random.randn(1024).astype(np.float32)
            if normalize_embeddings:
                vec /= np.linalg.norm(vec)
            return vec
            
    monkeypatch.setattr("sentinel.layer2.displacement._get_model", lambda: MockModel())

def test_cosine_distance():
    v1 = np.array([1, 0, 0], dtype=np.float32)
    v2 = np.array([0, 1, 0], dtype=np.float32)
    dist = cosine_distance(v1, v2)
    assert np.isclose(dist, 1.0) # Cosine similarity is 0, dist is 1
    
    v3 = np.array([1, 0, 0], dtype=np.float32)
    dist2 = cosine_distance(v1, v3)
    assert np.isclose(dist2, 0.0) # Identical

def test_displacement_direction_and_magnitude():
    # We use a mocked model that produces deterministic vectors.
    current_text = "This is a new instruction"
    baseline_emb = compute_embedding("This is the old instruction").tolist()
    
    disp = compute_displacement(current_text, baseline_emb, "test.md")
    
    assert isinstance(disp, SemanticDisplacement)
    assert 0.0 <= disp.cosine_distance <= 2.0
    assert disp.direction == "SEMANTIC_DIRECTION_UNAVAILABLE"

def test_missing_baseline_displacement():
    disp = compute_displacement("Some new file", None, "new.md")
    assert disp.cosine_distance == 1.0
    assert disp.direction == "unknown"

def test_identical_text():
    text = "Identical text"
    emb = compute_embedding(text).tolist()
    disp = compute_displacement(text, emb, "same.md")
    assert np.isclose(disp.cosine_distance, 0.0)
    assert disp.direction == "benign"

def test_empty_text():
    disp = compute_displacement("", compute_embedding("test").tolist(), "empty.md")
    assert disp.cosine_distance == 1.0
