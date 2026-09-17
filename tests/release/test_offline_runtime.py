import pytest
import os
import subprocess
from pathlib import Path

def test_offline_runtime():
    # In a real test suite this might use iptables or network namespaces.
    # Here we simulate offline by un-setting the huggingface/Groq vars 
    # and ensuring no crash occurs when run on local samples.
    
    # Run CLI without network access dependencies
    # sentinel scan samples/trapdoor_style_demo.md
    
    env = dict(os.environ)
    env.pop("GROQ_API_KEY", None)
    env.pop("GITHUB_TOKEN", None)
    
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "sentinel.cli", "scan", "samples/trapdoor_style_demo.md", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env
    )
    
    # Exit code is 1 because it's a compromised fixture
    assert result.returncode == 1, "Should complete and return 1 (findings detected)"
    
    # Must output JSON containing the findings
    assert "S1" in result.stdout
    assert "S5" in result.stdout
