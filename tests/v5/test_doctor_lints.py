import shutil
from pathlib import Path
import pytest

from sentinel.doctor.lints import check_file, apply_fixes
from sentinel import core


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "doctor"


def test_d001_broken_include():
    """D001 flags broken include; twin with existing include passes clean."""
    bad_file = FIXTURES_DIR / "d001_broken_include.md"
    findings = check_file(bad_file, root=FIXTURES_DIR)
    assert len(findings) == 1
    assert findings[0]["id"] == "D001"
    assert findings[0]["line"] == 2
    assert findings[0]["fix"] is not None

    twin_file = FIXTURES_DIR / "d001_twin.md"
    twin_findings = check_file(twin_file, root=FIXTURES_DIR)
    assert twin_findings == []


def test_d002_missing_path():
    """D002 flags backticked paths that do not exist; twin with existing path passes clean."""
    bad_file = FIXTURES_DIR / "d002_missing_path.md"
    findings = check_file(bad_file, root=FIXTURES_DIR)
    assert len(findings) == 1
    assert findings[0]["id"] == "D002"
    assert findings[0]["line"] == 2
    assert "src/phantom_controller.ts" in findings[0]["message"]
    assert findings[0]["fix"] is None

    twin_file = FIXTURES_DIR / "d002_twin.md"
    twin_findings = check_file(twin_file, root=FIXTURES_DIR)
    assert twin_findings == []


def test_d003_manifest_scripts(tmp_path: Path):
    """D003 flags undefined scripts across package.json, Makefile, and pyproject.toml."""
    # Setup package.json
    (tmp_path / "package.json").write_text('{"scripts": {"build": "tsc", "test": "jest"}}', encoding="utf-8")
    # Setup Makefile
    (tmp_path / "Makefile").write_text("build:\n\techo ok\nlint:\n\techo ok\n", encoding="utf-8")
    # Setup pyproject.toml
    (tmp_path / "pyproject.toml").write_text('[project.scripts]\ncli = "pkg:main"\n', encoding="utf-8")

    # Bad instruction referencing non-existent scripts
    bad_instructions = tmp_path / "CLAUDE.md"
    bad_instructions.write_text(
        "Run `npm run compile:wasm` before push.\n"
        "Run `make release` to deploy.\n"
        "Run `poetry run bench` for benchmarks.\n",
        encoding="utf-8",
    )

    findings = check_file(bad_instructions, root=tmp_path)
    ids = [f["id"] for f in findings]
    assert ids.count("D003") == 3

    # Twin instruction referencing valid scripts
    twin_instructions = tmp_path / "AGENTS.md"
    twin_instructions.write_text(
        "Run `npm run build` before push.\n"
        "Run `make lint` to check.\n",
        encoding="utf-8",
    )
    twin_findings = check_file(twin_instructions, root=tmp_path)
    assert twin_findings == []


def test_d004_duplicate_rules():
    """D004 flags duplicate rules and provides auto-fix; twin passes clean."""
    bad_file = FIXTURES_DIR / "d004_duplicate_rule.md"
    findings = check_file(bad_file, root=FIXTURES_DIR)
    assert len(findings) == 1
    assert findings[0]["id"] == "D004"
    assert findings[0]["line"] == 4
    assert findings[0]["fix"] is not None

    twin_file = FIXTURES_DIR / "d004_twin.md"
    twin_findings = check_file(twin_file, root=FIXTURES_DIR)
    assert twin_findings == []


def test_apply_fixes(tmp_path: Path):
    """Test auto-fixes apply cleanly in-place."""
    target = tmp_path / "CLAUDE.md"
    target.write_text(
        "# Instructions\n"
        "@include missing.md\n"
        "- Follow style guidelines carefully\n"
        "- Run pytest before committing\n"
        "- Follow style guidelines carefully\n",
        encoding="utf-8",
    )

    findings = check_file(target, root=tmp_path)
    assert len(findings) == 2  # D001 and D004

    content = target.read_text(encoding="utf-8")
    fixed_content, count = apply_fixes(content, findings)
    assert count == 2

    # Write and re-check
    target.write_text(fixed_content, encoding="utf-8")
    remaining = check_file(target, root=tmp_path)
    assert remaining == []
    assert "@include missing.md" not in fixed_content
    assert fixed_content.count("Follow style guidelines carefully") == 1


def test_hygiene_does_not_convict():
    """Instruction hygiene findings are NOT security flaws and never score or convict."""
    from sentinel import contract
    bad_file = FIXTURES_DIR / "d001_broken_include.md"
    rep = contract.scan_text("CLAUDE.md", bad_file.read_text(encoding="utf-8"))
    # Must be CLEAN: broken includes or duplicate rules are not exfiltration or malware
    assert rep["verdict"] == "CLEAN"
    assert rep["trust_score"] == 100
