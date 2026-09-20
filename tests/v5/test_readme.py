"""The README is the front door. Every image must exist in git, every button must point somewhere real, every #anchor must
land on a heading, and the diagrams must be exactly what their generator produces."""
import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text(encoding="utf-8")
ALLOWED_HOSTS = ("github.com/GarvitAgrawal04", "github.com/kambojmayan-png", "sentinel-ivory-two-76.vercel.app", "img.shields.io/",
                 "www.python.org/", "git-scm.com/", "www.apache.org/", "console.groq.com", "platform.openai.com", "console.anthropic.com",
                 "127.0.0.1:8000", "example.invalid", "docs.example.com", "staging.example.com", "collector.attacker.example", "attacker.example", "github.com/actions/",
                 "vercel.com", "api.github.com", "bun.sh", "get.docker.com", "pypi.org/project/")


def tracked():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception:
        pytest.skip("not a git checkout")
    if len(out) < 20:
        pytest.skip("not a git checkout")
    return set(out)


def slug(heading: str) -> str:
    """GitHub's heading anchor: lower-case, drop everything but letters, digits, spaces, hyphens and underscores, spaces to hyphens."""
    text = re.sub(r"`|\*|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def targets():
    md = re.findall(r"\]\(([^)\s]+)\)", README)
    html = re.findall(r'(?:href|src|srcset)="([^"]+)"', README)
    return md + html


def test_every_local_image_and_link_is_in_git():
    files = tracked()
    for t in targets():
        if t.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = t.split("#")[0]
        assert path in files or any(f.startswith(path.rstrip("/") + "/") for f in files), f"README points at {t}, which is not in git"


def test_every_anchor_lands_on_a_heading():
    in_code = False
    headings = set()
    for line in README.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"#{1,6} ", line):
            headings.add(slug(line.lstrip("#").strip()))
    for t in targets():
        if t.startswith("#"):
            assert t[1:] in headings, f"README links to {t}, and no heading has that anchor"


def test_every_external_link_goes_somewhere_we_meant():
    in_code = False
    prose = []
    for line in README.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code:
            prose.append(line)
    for t in re.findall(r'(?:\]\(|href="|src="|srcset=")(https?://[^)"\s]+)', "\n".join(prose)):
        assert any(h in t for h in ALLOWED_HOSTS), f"unexpected external link in the README: {t}"


def test_buttons_are_links_and_dark_mode_has_its_own_artwork():
    buttons = re.findall(r'<a href="([^"]+)"><img src="(docs/img/btn-[a-z-]+\.svg)"', README)
    assert len(buttons) >= 8                                             # every button image is wrapped in a link
    assert README.count('src="docs/img/btn-') == len(buttons), "a button image is not wrapped in a link"
    for name in ("banner", "how-it-works", "architecture", "benchmark", "score"):
        assert f'srcset="docs/img/{name}-dark.svg"' in README and f'src="docs/img/{name}-light.svg"' in README
    assert "ui-scanner.png" not in README and "ui-flow.png" not in README


def test_the_committed_diagrams_are_exactly_what_the_generator_makes(tmp_path):
    spec = importlib.util.spec_from_file_location("build_readme_assets", ROOT / "docs" / "build_readme_assets.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    gen.OUT = tmp_path
    gen.main()
    made = sorted(p.name for p in tmp_path.glob("*.svg"))
    assert len(made) >= 20
    for name in made:
        committed = ROOT / "docs" / "img" / name
        assert committed.is_file(), f"{name} is generated but not committed"
        assert committed.read_text(encoding="utf-8") == (tmp_path / name).read_text(encoding="utf-8"), \
            f"docs/img/{name} is stale: run python docs/build_readme_assets.py"


def test_the_chart_in_the_readme_uses_the_published_numbers():
    spec = importlib.util.spec_from_file_location("build_readme_assets", ROOT / "docs" / "build_readme_assets.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    assert gen.BENCH == [("Sentinel", 927, 3), ("Scanner B", 810, 120), ("Scanner A", 544, 386)]
    svg = (ROOT / "docs" / "img" / "benchmark-light.svg").read_text(encoding="utf-8")
    for text in ("99.7% pass", "87% pass", "58% pass", "3 false alarms", "120 false alarms", "386 false alarms"):
        assert text in svg
