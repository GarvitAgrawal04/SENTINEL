import pytest
from pathlib import Path

from sentinel.layer2.diff import compute_diff, compute_sha256, normalize_path
from sentinel.layer2 import FileChangeType
from sentinel.manifest.sentinel_lock import BaselineProvider, BaselineFile

class MockBaseline(BaselineProvider):
    def __init__(self, files):
        self._files = {f.filepath: f for f in files}
        
    def get_file(self, filepath: str) -> BaselineFile:
        return self._files.get(filepath)

    def get_all_files(self):
        return list(self._files.values())

def test_deterministic_diffing(tmp_path):
    # Setup mock files
    f1 = tmp_path / "unchanged.md"
    f1.write_text("hello world")
    
    f2 = tmp_path / "modified.md"
    f2.write_text("new content")
    
    f3 = tmp_path / "added.md"
    f3.write_text("added content")
    
    f1_hash = compute_sha256(f1)
    f2_hash = compute_sha256(f2)
    
    # Baseline
    baseline = MockBaseline([
        BaselineFile(filepath="unchanged.md", sha256=f1_hash),
        BaselineFile(filepath="modified.md", sha256="oldhash123"),
        BaselineFile(filepath="removed.md", sha256="removedhash456"),
    ])
    
    current_files = [f1, f2, f3]
    diffs = compute_diff(current_files, baseline, base_dir=tmp_path)
    
    diff_map = {d.filepath: d for d in diffs}
    
    assert diff_map["unchanged.md"].change_type == FileChangeType.UNCHANGED
    assert diff_map["modified.md"].change_type == FileChangeType.MODIFIED
    assert diff_map["added.md"].change_type == FileChangeType.ADDED
    assert diff_map["removed.md"].change_type == FileChangeType.REMOVED
    
def test_path_normalization():
    assert normalize_path("a\\b\\c.txt") == "a/b/c.txt"
    assert normalize_path("a/b/c.txt") == "a/b/c.txt"
