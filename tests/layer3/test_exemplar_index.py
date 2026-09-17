import pytest
import json
from pathlib import Path
from sentinel.layer3.exemplar import ExemplarIndex

@pytest.fixture
def mock_corpus(tmp_path):
    corpus = tmp_path / "dataset.json"
    data = {
        "samples": [
            {"id": "TR-01", "split": "train", "label": "malicious", "text": "bad content"},
            {"id": "TR-02", "split": "train", "label": "benign", "text": "good content"},
            {"id": "TE-01", "split": "test", "label": "malicious", "text": "test bad"},
            {"id": "HO-01-HOLDOUT", "split": "train", "label": "malicious", "text": "holdout bad"}
        ]
    }
    corpus.write_text(json.dumps(data))
    return corpus

@pytest.fixture(autouse=True)
def mock_embedding(monkeypatch):
    import numpy as np
    class MockModel:
        def encode(self, text, normalize_embeddings=False):
            return np.array([0.1, 0.2])
    monkeypatch.setattr("sentinel.layer2.displacement._get_model", lambda: MockModel())

def test_exemplar_index_loading(mock_corpus):
    index = ExemplarIndex()
    index.load_from_corpus(mock_corpus, max_attack=10, max_clean=10)
    
    assert len(index.exemplars) == 2
    ids = [ex.id for ex in index.exemplars]
    assert "TR-01" in ids
    assert "TR-02" in ids
    assert "TE-01" not in ids # Must not leak test split
    assert "HO-01-HOLDOUT" not in ids # Must not leak holdout families
