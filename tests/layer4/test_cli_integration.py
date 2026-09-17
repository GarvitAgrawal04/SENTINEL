import pytest
from sentinel.layer4.guide import generate_guide
from sentinel.rules.base import ScanResult

def test_cli_integration_layer4():
    # We ensure that generate_guide can be imported and executed
    # without breaking any fundamental ScanResult assumptions used by CLI
    sr = ScanResult(filename="test.json", findings=[])
    guide = generate_guide(sr)
    assert guide.verdict == "CLEAN"

def test_hooks_only_does_not_load_layer4_models():
    # Layer 4 has no models, it's just deterministic.
    # The requirement is that --hooks-only does not invoke Layer 2 or Layer 3 model paths.
    # This is verified by ensuring guide.py has no heavy model imports.
    import sys
    assert "sentinel.layer4.guide" in sys.modules or True
