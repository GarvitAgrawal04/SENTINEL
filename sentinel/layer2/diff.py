import hashlib
from pathlib import Path
from typing import List, Optional

from sentinel.layer2 import DiffResult, FileChangeType
from sentinel.manifest.sentinel_lock import BaselineProvider

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize_path(filepath: str) -> str:
    """Deterministic path normalization (forward slashes, relative if possible)."""
    return Path(filepath).as_posix()

def compute_diff(
    current_files: List[Path],
    baseline: BaselineProvider,
    base_dir: Optional[Path] = None
) -> List[DiffResult]:
    """
    Compare current files on disk against the baseline provider.
    """
    results = []
    
    # Check all current files
    seen_paths = set()
    for current_file in current_files:
        if not current_file.exists() or not current_file.is_file():
            continue
            
        rel_path = current_file.relative_to(base_dir) if base_dir else current_file
        norm_path = normalize_path(str(rel_path))
        seen_paths.add(norm_path)
        
        current_hash = compute_sha256(current_file)
        baseline_file = baseline.get_file(norm_path)
        
        if baseline_file:
            if current_hash == baseline_file.sha256:
                change = FileChangeType.UNCHANGED
            else:
                change = FileChangeType.MODIFIED
            
            results.append(DiffResult(
                filepath=norm_path,
                change_type=change,
                current_hash=current_hash,
                baseline_hash=baseline_file.sha256
            ))
        else:
            results.append(DiffResult(
                filepath=norm_path,
                change_type=FileChangeType.ADDED,
                current_hash=current_hash,
                baseline_hash=None
            ))
            
    # Check baseline for removed files
    for baseline_file in baseline.get_all_files():
        if baseline_file.filepath not in seen_paths:
            results.append(DiffResult(
                filepath=baseline_file.filepath,
                change_type=FileChangeType.REMOVED,
                current_hash=None,
                baseline_hash=baseline_file.sha256
            ))
            
    return results
