from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

class FileChangeType(Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"

@dataclass
class DiffResult:
    filepath: str
    change_type: FileChangeType
    current_hash: Optional[str]
    baseline_hash: Optional[str]
    
@dataclass
class SemanticDisplacement:
    filepath: str
    cosine_distance: float
    direction: str  # "benign", "attack", or "unknown"
    confidence: Optional[float] = None

@dataclass
class Layer2Result:
    diffs: List[DiffResult]
    displacements: List[SemanticDisplacement]
    
    @property
    def max_attack_displacement(self) -> float:
        """Helper to get the highest attack displacement for formula consumption."""
        attack_disps = [d.cosine_distance for d in self.displacements if d.direction == "attack"]
        return max(attack_disps) if attack_disps else 0.0
