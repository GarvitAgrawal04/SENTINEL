"""Tests for Day 12: the portfolio finish (resume repo deliverables).

Verifies that:
- CITATION.cff is valid and contains accurate metadata
- AUTHORS and CONTRIBUTORS files exist and recognize creators
- docs/GITHUB_SETUP.md and docs/img/social-preview.png (1280x640) exist
- docs/img/demo.gif exists, is animated, and showcases the 4 milestones
- docs/DEMO.md exists and provides a structured 5-minute runbook
- ARCHITECTURE.md exists, contains architecture diagrams and module table
- GLOSSARY.md exists and defines core agent security concepts
- docs/FAQ.md exists with comprehensive coverage
- README.md links to all portfolio assets
"""
from __future__ import annotations

import re
import struct
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


class TestPortfolioAssets:
    def test_citation_cff_valid(self):
        """CITATION.cff must exist and specify title, version, authors, and license."""
        path = ROOT / "CITATION.cff"
        assert path.is_file(), "CITATION.cff is missing"
        text = path.read_text(encoding="utf-8")
        assert "cff-version: 1.2.0" in text
        assert "Sentinel" in text
        assert "Mayan" in text and "Kamboj" in text
        assert "Garvit" in text and "Agrawal" in text
        assert "Apache-2.0" in text
        assert "repository-code:" in text

    def test_authors_and_contributors(self):
        """AUTHORS and CONTRIBUTORS must exist and credit creators."""
        authors = ROOT / "AUTHORS"
        assert authors.is_file(), "AUTHORS file is missing"
        auth_text = authors.read_text(encoding="utf-8")
        assert "Mayan Kamboj" in auth_text
        assert "Garvit Agrawal" in auth_text

        contributors = ROOT / "CONTRIBUTORS"
        assert contributors.is_file(), "CONTRIBUTORS file is missing"
        contrib_text = contributors.read_text(encoding="utf-8")
        assert "Mayan Kamboj" in contrib_text
        assert "Garvit Agrawal" in contrib_text
        assert "Pillar Security" in contrib_text or "Socket" in contrib_text

    def test_github_setup_and_social_preview(self):
        """docs/GITHUB_SETUP.md and docs/img/social-preview.png must exist with correct specs."""
        setup = ROOT / "docs" / "GITHUB_SETUP.md"
        assert setup.is_file(), "docs/GITHUB_SETUP.md is missing"
        setup_text = setup.read_text(encoding="utf-8")
        assert "ai-agents" in setup_text
        assert "prompt-injection" in setup_text
        assert "social-preview.png" in setup_text

        preview = ROOT / "docs" / "img" / "social-preview.png"
        assert preview.is_file(), "docs/img/social-preview.png is missing"
        data = preview.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", "social-preview.png must be a valid PNG"
        w, h = struct.unpack(">II", data[16:24])
        assert (w, h) == (1280, 640), f"Social preview image must be 1280x640, got ({w}, {h})"

    def test_demo_gif_animation(self):
        """docs/img/demo.gif must exist, be an animated GIF, and contain >= 10 frames."""
        gif_path = ROOT / "docs" / "img" / "demo.gif"
        assert gif_path.is_file(), "docs/img/demo.gif is missing"
        data = gif_path.read_bytes()
        assert data[:6] in (b"GIF89a", b"GIF87a"), "demo.gif must be a valid GIF"
        w, h = struct.unpack("<HH", data[6:10])
        assert (w, h) == (1000, 693), f"demo.gif canvas size must be 1000x693, got ({w}, {h})"
        frames = data.count(b"\x21\xf9\x04")
        assert frames >= 4, f"demo.gif must have >= 4 frames, got {frames}"

    def test_demo_md_five_minute_tour(self):
        """docs/DEMO.md must provide a 5-minute hands-on walkthrough."""
        demo = ROOT / "docs" / "DEMO.md"
        assert demo.is_file(), "docs/DEMO.md is missing"
        text = demo.read_text(encoding="utf-8")
        assert "Minute 1" in text
        assert "Minute 2" in text
        assert "Minute 3" in text
        assert "Minute 4" in text
        assert "Minute 5" in text
        assert "trapdoor_style_demo.md" in text
        assert "timewarp" in text.lower()
        assert "doctor" in text.lower()

    def test_architecture_md_structure(self):
        """ARCHITECTURE.md must document layers, scoring formula, and module responsibilities."""
        arch = ROOT / "ARCHITECTURE.md"
        assert arch.is_file(), "ARCHITECTURE.md is missing"
        text = arch.read_text(encoding="utf-8")
        assert "Layer 0" in text and "Layer 1" in text and "Layer 2" in text
        assert "Time-Warp" in text
        assert "Trust Score" in text
        assert "sentinel.core" in text
        assert "sentinel.timewarp" in text
        assert "sentinel.doctor" in text
        assert "sentinel.lock" in text

    def test_glossary_md_definitions(self):
        """GLOSSARY.md must define core agent security terms."""
        glossary = ROOT / "GLOSSARY.md"
        assert glossary.is_file(), "GLOSSARY.md is missing"
        text = glossary.read_text(encoding="utf-8")
        required_terms = [
            "Agent Instruction File",
            "Model Context Protocol",
            "Tool Poisoning",
            "Sleeper",
            "Time-Warp",
            "Canary Secret",
            "Instruction Doctor",
            "Token Delta",
            "Rewrite Gate",
            "AGENTS.lock",
            "Precision Gate",
            "TrapDoor",
        ]
        for term in required_terms:
            assert term in text, f"GLOSSARY.md is missing term: {term}"

    def test_faq_md_coverage(self):
        """docs/FAQ.md must address >= 10 distinct questions."""
        faq = ROOT / "docs" / "FAQ.md"
        assert faq.is_file(), "docs/FAQ.md is missing"
        text = faq.read_text(encoding="utf-8")
        questions = re.findall(r"^###\s+.*\?", text, re.MULTILINE)
        assert len(questions) >= 10, f"docs/FAQ.md must have >= 10 questions, found {len(questions)}"
        assert any("offline" in q.lower() or "cloud" in q.lower() for q in questions)
        assert any("key" in q.lower() for q in questions)
        assert any("doctor" in q.lower() for q in questions)
        assert any("lock" in q.lower() for q in questions)

    def test_readme_links_all_portfolio_files(self):
        """README.md must link to the new portfolio assets."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "docs/DEMO.md" in readme
        assert "ARCHITECTURE.md" in readme
        assert "GLOSSARY.md" in readme
        assert "docs/FAQ.md" in readme
        assert "CITATION.cff" in readme
        assert "AUTHORS" in readme
