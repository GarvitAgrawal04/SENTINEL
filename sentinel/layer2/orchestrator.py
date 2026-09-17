from pathlib import Path
from typing import List, Optional

from sentinel.layer2 import Layer2Result, FileChangeType, DiffResult, SemanticDisplacement
from sentinel.layer2.diff import compute_diff
from sentinel.layer2.displacement import compute_displacement
from sentinel.manifest.sentinel_lock import BaselineProvider

def run_layer2(
    current_files: List[Path],
    baseline: BaselineProvider,
    base_dir: Optional[Path] = None
) -> Layer2Result:
    """
    Execute the Layer 2 pipeline:
    1. Deterministic file diff against baseline.
    2. Semantic displacement calculation for modified and added files.
    """
    diffs = compute_diff(current_files, baseline, base_dir)
    
    displacements = []
    
    for diff in diffs:
        if diff.change_type == FileChangeType.UNCHANGED:
            # No semantic displacement if structurally identical
            continue
            
        elif diff.change_type == FileChangeType.REMOVED:
            # File deleted - typically 100% displacement but direction might be benign or attack
            # For V1, we simply mark it with 1.0 distance
            displacements.append(SemanticDisplacement(
                filepath=diff.filepath,
                cosine_distance=1.0,
                direction="unknown",
                confidence=1.0
            ))
            
        elif diff.change_type == FileChangeType.ADDED:
            # Read content
            filepath = base_dir / diff.filepath if base_dir else Path(diff.filepath)
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""
                
            disp = compute_displacement(content, None, diff.filepath)
            displacements.append(disp)
            
        elif diff.change_type == FileChangeType.MODIFIED:
            # Read content
            filepath = base_dir / diff.filepath if base_dir else Path(diff.filepath)
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""
                
            baseline_file = baseline.get_file(diff.filepath)
            baseline_emb = baseline_file.embedding if baseline_file else None
            
            disp = compute_displacement(content, baseline_emb, diff.filepath)
            displacements.append(disp)
            
    return Layer2Result(diffs=diffs, displacements=displacements)
