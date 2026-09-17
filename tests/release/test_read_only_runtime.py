import pytest
import subprocess
import hashlib
from pathlib import Path
import tempfile
import shutil

def get_hash(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def test_read_only_runtime():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy samples/trapdoor_style_demo.md to a temp file
        src = Path("samples/trapdoor_style_demo.md")
        dst = Path(temp_dir) / "trapdoor_style_demo.md"
        shutil.copy(src, dst)
        
        original_hash = get_hash(dst)
        
        import sys
        # Run Sentinel on it
        subprocess.run([sys.executable, "-m", "sentinel.cli", "scan", str(dst)])
        
        new_hash = get_hash(dst)
        assert original_hash == new_hash, "The scanner mutated the file!"
        
        # Run Hooks-only on it
        subprocess.run([sys.executable, "-m", "sentinel.cli", "scan", "--hooks-only", str(dst)])
        
        new_hash_2 = get_hash(dst)
        assert original_hash == new_hash_2, "The hooks-only scanner mutated the file!"
