from typing import Optional, Protocol, List
from dataclasses import dataclass

@dataclass
class BaselineFile:
    filepath: str
    sha256: str
    embedding: Optional[List[float]] = None

class BaselineProvider(Protocol):
    def get_file(self, filepath: str) -> Optional[BaselineFile]:
        """Return the baseline state (hash and optional embedding) for a given filepath."""
        ...

    def get_all_files(self) -> List[BaselineFile]:
        """Return all tracked baseline files."""
        ...

class SentinelLockBaseline(BaselineProvider):
    """
    A concrete implementation of BaselineProvider that reads from sentinel.lock.
    V1: Currently unimplemented full orchestrator, but provides the boundary.
    """
    def __init__(self, lockfile_path: str):
        self.lockfile_path = lockfile_path
        self._files: dict[str, BaselineFile] = {}
        # In a full implementation, this would load and parse sentinel.lock
        
    def get_file(self, filepath: str) -> Optional[BaselineFile]:
        return self._files.get(filepath)

    def get_all_files(self) -> List[BaselineFile]:
        return list(self._files.values())