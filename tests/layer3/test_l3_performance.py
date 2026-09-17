import time
import pytest
from sentinel.layer3.classifier import NearestNeighborBaseline
from sentinel.layer3.exemplar import ExemplarIndex
from sentinel.layer3.reconstruction import reconstruct_impact

@pytest.fixture
def mock_index(monkeypatch):
    import numpy as np
    idx = ExemplarIndex()
    # Fill with 36 mock vectors
    for i in range(36):
        from sentinel.layer3.exemplar import Exemplar
        idx.exemplars.append(Exemplar(str(i), "clean", None, "desc", np.random.randn(1024).tolist()))
    return idx

def test_performance_warm_path(mock_index):
    baseline = NearestNeighborBaseline(mock_index)
    
    # Measure time to classify (knn)
    import numpy as np
    query = np.random.randn(1024).tolist()
    
    t0 = time.perf_counter()
    baseline.classify(query)
    t1 = time.perf_counter()
    
    assert (t1 - t0) < 0.5 # KNN should be sub-100ms
    
def test_determinism_layer3(mock_index):
    baseline = NearestNeighborBaseline(mock_index)
    import numpy as np
    query = np.random.randn(1024).tolist()
    
    res1 = baseline.classify(query)
    res2 = baseline.classify(query)
    
    assert res1.nearest_exemplars[0].exemplar.id == res2.nearest_exemplars[0].exemplar.id
    assert res1.confidence == res2.confidence
