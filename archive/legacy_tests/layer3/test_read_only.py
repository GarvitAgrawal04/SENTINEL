import ast
from pathlib import Path
import pytest

def check_file_for_banned_imports(filepath):
    code = filepath.read_text(encoding="utf-8")
    tree = ast.parse(code)
    
    banned_modules = {"urllib", "requests", "httpx", "aiohttp", "socket", "subprocess"}
    banned_functions = {"os.system"}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in banned_modules:
                    pytest.fail(f"Banned import {alias.name} found in {filepath.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in banned_modules:
                pytest.fail(f"Banned import {node.module} found in {filepath.name}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "system":
                    pytest.fail(f"Banned call os.system found in {filepath.name}")

def test_no_banned_imports_in_layer3():
    layer3_dir = Path("sentinel/layer3")
    assert layer3_dir.exists(), "Layer 3 directory missing"
    
    for f in layer3_dir.glob("*.py"):
        check_file_for_banned_imports(f)
