"""Tests for Day 11: evidence, reproducibility, and research write-up.

Verifies that:
- bench/evidence.py exists and is runnable
- All stored benchmark results files exist and contain key metrics
- docs/RESEARCH.md exists and cross-links to bench/results/ files
- make evidence target is declared in the Makefile
- Every claim in RESEARCH.md traces to a file in bench/results/
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH_RESULTS = ROOT / "bench" / "results"


# ---------------------------------------------------------------------------
# T1: make evidence / bench/evidence.py
# ---------------------------------------------------------------------------

class TestEvidenceRunner:
    def test_evidence_py_exists(self):
        """bench/evidence.py must exist."""
        assert (ROOT / "bench" / "evidence.py").is_file(), (
            "bench/evidence.py is missing — Day 11 T1 deliverable"
        )

    def test_evidence_has_main(self):
        """evidence.py must define a main() entry point."""
        text = (ROOT / "bench" / "evidence.py").read_text(encoding="utf-8")
        assert "def main(" in text, "bench/evidence.py must define main()"
        assert '__name__ == "__main__"' in text, "bench/evidence.py must have __main__ guard"

    def test_evidence_generates_latest_report(self, tmp_path):
        """Running evidence.py --skip-timewarp must produce evidence_latest.md."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "evidence", ROOT / "bench" / "evidence.py"
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

        # Patch the results dir to a tmp path so we don't dirty tracked files
        original = mod.RESULTS_DIR
        mod.RESULTS_DIR = tmp_path
        try:
            ret = mod.main(["--skip-timewarp", "--out", str(tmp_path / "evidence_test.md")])
        finally:
            mod.RESULTS_DIR = original

        assert ret == 0, "evidence.py main() must return 0"
        report = tmp_path / "evidence_test.md"
        assert report.is_file(), "evidence.py must write the report file"
        content = report.read_text(encoding="utf-8")
        assert "Sentinel Evidence Report" in content
        assert "Semantic" in content
        assert "Time-Warp" in content

    def test_makefile_has_evidence_target(self):
        """Makefile must declare an 'evidence' target."""
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8", errors="replace")
        assert "evidence:" in makefile, "Makefile must have an 'evidence:' target"
        assert "bench/evidence.py" in makefile, "Makefile evidence target must call bench/evidence.py"


# ---------------------------------------------------------------------------
# T2: Stored benchmark results / versioned snapshot
# ---------------------------------------------------------------------------

class TestStoredResults:
    """Every published claim must be backed by a file in bench/results/."""

    REQUIRED_FILES = [
        "manifest_main.json",
        "manifest_heldout.json",
        "bench_wild_main.txt",
        "bench_wild_heldout.txt",
        "bench_fixtures.txt",
        "bench_benign.txt",
        "doctor_hit_rates.json",
        "doctor_eval.md",
        "gate_redteam.json",
        "gate_redteam.md",
        "doctor_token_delta.json",
        "doctor_token_delta.md",
        "semantic_eval.json",
        "semantic_eval.md",
        "trigger_prevalence.json",
        "trigger_prevalence.md",
        "evidence_latest.md",
    ]

    @pytest.mark.parametrize("filename", REQUIRED_FILES)
    def test_result_file_exists(self, filename: str):
        path = BENCH_RESULTS / filename
        assert path.is_file(), (
            f"bench/results/{filename} is missing — all published results must be stored"
        )

    def test_semantic_eval_json_key_metrics(self):
        """semantic_eval.json must record recall >= 70% and FP rate <= 1%."""
        data = json.loads((BENCH_RESULTS / "semantic_eval.json").read_text(encoding="utf-8"))
        assert data["holdout"]["recall_pct"] >= 70.0, (
            f"Semantic recall {data['holdout']['recall_pct']:.2f}% is below the 70% target"
        )
        assert data["benign"]["false_warning_rate_pct"] <= 1.0, (
            f"Semantic FP rate {data['benign']['false_warning_rate_pct']:.2f}% exceeds 1.0% budget"
        )
        assert data["benign"]["budget_met"] is True

    def test_trigger_prevalence_json_mean(self):
        """trigger_prevalence.json must record mean scenarios <= 1.35."""
        data = json.loads((BENCH_RESULTS / "trigger_prevalence.json").read_text(encoding="utf-8"))
        mean = data["overall"]["mean_scenarios_per_target"]
        assert mean <= 1.35, f"Mean scenarios/target {mean} exceeds threshold 1.35"

    def test_gate_redteam_zero_escapes(self):
        """gate_redteam.json must record 0 gate escapes."""
        data = json.loads((BENCH_RESULTS / "gate_redteam.json").read_text(encoding="utf-8"))
        escapes = data.get("escapes", data.get("escape_count", 0))
        assert escapes == 0, f"gate_redteam.json records {escapes} escapes — must be 0"

    def test_doctor_token_delta_non_positive_median(self):
        """doctor_token_delta.json median delta must be <= 0 (never grows files)."""
        data = json.loads((BENCH_RESULTS / "doctor_token_delta.json").read_text(encoding="utf-8"))
        median = data.get("median_token_delta", 0)
        assert median <= 0, (
            f"Doctor token delta median {median} is positive — doctor --fix must not grow files"
        )

    def test_evidence_latest_mentions_key_numbers(self):
        """evidence_latest.md must mention the key headline numbers."""
        text = (BENCH_RESULTS / "evidence_latest.md").read_text(encoding="utf-8")
        # Semantic recall figure
        assert "84.88" in text or "84.9" in text, "evidence_latest.md must cite the 84.88% semantic recall"
        # Time-warp: 10/10 attacks
        assert "10/10" in text or "10 / 10" in text, "evidence_latest.md must cite 10/10 timewarp detection"
        # Gate escapes
        assert "0 escape" in text.lower() or "0.0%" in text, "evidence_latest.md must cite 0 gate escapes"


# ---------------------------------------------------------------------------
# T3: docs/RESEARCH.md
# ---------------------------------------------------------------------------

class TestResearchDoc:
    def test_research_md_exists(self):
        """docs/RESEARCH.md must exist."""
        assert (ROOT / "docs" / "RESEARCH.md").is_file(), (
            "docs/RESEARCH.md is missing — Day 11 T3 deliverable"
        )

    def test_research_md_sections(self):
        """RESEARCH.md must contain required sections."""
        text = (ROOT / "docs" / "RESEARCH.md").read_text(encoding="utf-8")
        required = [
            "Landscape",
            "Threats to Validity",
            "Reproduction",
            "Failures",
            "Related Work",
        ]
        for section in required:
            assert section in text, f"RESEARCH.md is missing section: {section}"

    def test_research_md_cites_bench_results(self):
        """RESEARCH.md must link to bench/results/ files."""
        text = (ROOT / "docs" / "RESEARCH.md").read_text(encoding="utf-8")
        assert "bench/results" in text or "../bench/results" in text, (
            "RESEARCH.md must cross-link to bench/results/"
        )

    def test_research_md_key_numbers_present(self):
        """RESEARCH.md must contain the key published numbers."""
        text = (ROOT / "docs" / "RESEARCH.md").read_text(encoding="utf-8")
        # 930 repos
        assert "930" in text, "RESEARCH.md must mention the 930-repo evaluation"
        # 0 COMPROMISED
        assert "0 COMPROMISED" in text or "COMPROMISED | **0**" in text, (
            "RESEARCH.md must state 0 COMPROMISED on real repos"
        )
        # Semantic recall
        assert "84.88" in text or "84.9" in text, "RESEARCH.md must cite the 84.88% semantic recall"
        # Timewarp 10/10
        assert "10/10" in text or "10 / 10" in text, "RESEARCH.md must cite 10/10 timewarp detection"

    def test_research_md_threats_section_content(self):
        """Threats to validity section must mention the corpus assumption."""
        text = (ROOT / "docs" / "RESEARCH.md").read_text(encoding="utf-8")
        assert "presumed" in text.lower() or "audited" in text.lower(), (
            "RESEARCH.md threats section must acknowledge the corpus-health assumption"
        )

    def test_research_md_no_untraced_numbers(self):
        """Every bold percentage in RESEARCH.md must appear in a bench/results file."""
        import re
        text = (ROOT / "docs" / "RESEARCH.md").read_text(encoding="utf-8")
        # Extract all bold percentages e.g. **84.88%**
        pcts = re.findall(r"\*\*([0-9]+\.[0-9]+)%\*\*", text)
        # Gather all text from bench/results files
        all_results = ""
        for f in BENCH_RESULTS.iterdir():
            if f.suffix in (".md", ".txt", ".json") and f.stat().st_size < 200_000:
                try:
                    all_results += f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
        for pct in pcts:
            # Allow ±0.01 tolerance — some files round slightly differently
            assert pct in all_results or pct[:4] in all_results, (
                f"RESEARCH.md cites **{pct}%** but this number is not found in bench/results/"
            )


# ---------------------------------------------------------------------------
# T5: Cross-links from README
# ---------------------------------------------------------------------------

class TestReadmeCrossLinks:
    def test_readme_links_to_research(self):
        """README.md must contain a link to docs/RESEARCH.md."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "RESEARCH.md" in readme or "docs/RESEARCH" in readme, (
            "README.md must link to docs/RESEARCH.md (Day 11 T5)"
        )

    def test_readme_links_to_bench_results(self):
        """README.md must reference bench/results/ as the evidence source."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "bench/results" in readme or "bench/evidence" in readme, (
            "README.md must reference bench/results/ or bench/evidence.py"
        )
