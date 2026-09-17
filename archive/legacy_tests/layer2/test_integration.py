import pytest
from pathlib import Path

from sentinel.layer2.orchestrator import run_layer2
from sentinel.layer2 import FileChangeType
from sentinel.manifest.sentinel_lock import BaselineFile, BaselineProvider
from sentinel.scoring.formula import DisplacementResult

class MockBaseline(BaselineProvider):
    def __init__(self, files):
        self._files = {f.filepath: f for f in files}
        
    def get_file(self, filepath: str) -> BaselineFile:
        return self._files.get(filepath)

    def get_all_files(self):
        return list(self._files.values())

@pytest.fixture(autouse=True)
def mock_sentence_transformers(monkeypatch):
    class MockModel:
        def encode(self, text, normalize_embeddings=False):
            import numpy as np
            np.random.seed(len(text))
            vec = np.random.randn(1024).astype(np.float32)
            if normalize_embeddings:
                vec /= np.linalg.norm(vec)
            return vec
    monkeypatch.setattr("sentinel.layer2.displacement._get_model", lambda: MockModel())

def test_layer2_orchestrator(tmp_path):
    f_mod = tmp_path / "modified.md"
    f_mod.write_text("modified content")
    
    f_add = tmp_path / "added.md"
    f_add.write_text("added content")
    
    f_unchanged = tmp_path / "unchanged.md"
    f_unchanged.write_text("unchanged content")
    
    import hashlib
    def get_hash(text):
        return hashlib.sha256(text.encode()).hexdigest()
        
    baseline = MockBaseline([
        BaselineFile("modified.md", "oldhash", [0.1]*1024),
        BaselineFile("unchanged.md", get_hash("unchanged content"), [0.2]*1024),
        BaselineFile("removed.md", "removedhash", [0.3]*1024)
    ])
    
    res = run_layer2([f_mod, f_add, f_unchanged], baseline, tmp_path)
    
    assert len(res.diffs) == 4
    
    disp_paths = {d.filepath: d for d in res.displacements}
    assert "modified.md" in disp_paths
    assert "added.md" in disp_paths
    assert "removed.md" in disp_paths
    assert "unchanged.md" not in disp_paths

def test_formula_integration():
    from sentinel.layer2 import SemanticDisplacement, Layer2Result
    from sentinel.scoring.formula import compute_score, compute_verdict, score_breakdown
    from sentinel.rules.base import ScanResult, Finding
    
    # Simulate L2 generating a result
    l2_res = Layer2Result(
        diffs=[],
        displacements=[
            SemanticDisplacement("f1", 0.8, "attack", 0.9),
            SemanticDisplacement("f2", 0.2, "benign", 0.9)
        ]
    )
    
    # We must pass highest attack displacement into formula as DisplacementResult
    max_attack_dist = l2_res.max_attack_displacement
    dr = DisplacementResult(magnitude=max_attack_dist, direction="attack" if max_attack_dist > 0 else "benign")
    
    scan_res = ScanResult(filename="project", findings=[])
    scan_res.displacement = dr
    
    score = compute_score(scan_res)
    assert score == 100 - (0.8 * 30 * 1.5)
    
