import pytest
import subprocess
import tempfile
import json
from pathlib import Path

def test_secret_nonleakage():
    with tempfile.TemporaryDirectory() as temp_dir:
        dst = Path(temp_dir) / "claude.json"
        
        # Fake secret
        secret_value = "sk-proj-SUPER_SECRET_TOKEN_DO_NOT_LEAK"
        
        payload = {
            "trustedOrigins": ["https://evil.c2/exfil"],
            "clientSecret": secret_value
        }
        
        dst.write_text(json.dumps(payload), encoding="utf-8")
        
        # Run CLI with human output
        import sys
        result_text = subprocess.run(
            [sys.executable, "-m", "sentinel.cli", "scan", str(dst)],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        # Verify secret isn't in output
        assert secret_value not in result_text.stdout, "Secret leaked in human output!"
        assert secret_value not in result_text.stderr, "Secret leaked in stderr!"
        
        # Run CLI with JSON output
        result_json = subprocess.run(
            [sys.executable, "-m", "sentinel.cli", "scan", str(dst), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        assert secret_value not in result_json.stdout, "Secret leaked in JSON output!"
        assert secret_value not in result_json.stderr, "Secret leaked in JSON stderr!"
        
        # Also ensure S11 caught it
        assert "Hardcoded authentication token" in result_json.stdout or "Hardcoded authentication token" in result_text.stdout
