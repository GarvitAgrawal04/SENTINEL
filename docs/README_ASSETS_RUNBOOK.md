# Sentinel README & Visual Assets Runbook

This runbook documents the automated, zero-slop visual asset pipeline for Sentinel's `README.md`. It explains how to generate the architecture diagrams, capture automated browser screenshots, compile terminal demo GIFs, run extreme stress tests, and verify that 100% of links and buttons are active and functional.

---

## 1. Quick Reference: One-Command Rebuild

To regenerate all SVG diagrams, run link checks, and verify integrity:

```bash
# 1. Activate your virtual environment
source .venv/bin/activate       # macOS / Linux
.venv\Scripts\Activate.ps1       # Windows PowerShell

# 2. Build all SVG diagrams & illustrations (zero external dependencies)
python docs/build_readme_assets.py

# 3. Verify all internal anchors, image paths, and SVGs
pytest tests/v5/test_readme.py

# 4. Verify all external HTTP links and release assets (requires internet)
python docs/check_readme_links.py
```

---

## 2. Architecture Diagram Generator

The Sentinel architecture diagram (`docs/img/architecture-light.svg` and `docs/img/architecture-dark.svg`) is generated programmatically using standard library Python. It requires zero external graphics software, node packages, or cloud APIs.

### Files Involved
- `scripts/generate_architecture_diagram.py`: Standalone SVG vector generator implementing the Apple/Samsung luxury-minimal aesthetic (smooth rounded rectangles, terracotta/cobalt/indigo/sage/amber/rose color system, animated SVG flow lines, and dual dark/light themes).
- `docs/build_readme_assets.py`: Central asset builder that generates all buttons, badges, diagrams, and illustrations.

### How to Run
```bash
# Generate architecture SVGs directly:
python scripts/generate_architecture_diagram.py

# Or generate all assets (banner, architecture, score, benchmark, buttons):
python docs/build_readme_assets.py
```

### Visual Specifications
- **Dimensions:** 1280 x 930 viewBox, high-DPI crisp vector text.
- **Entry Points:** Command Line, Gate, Pull Request, Web App & REST API, VS Code Extension.
- **Engine Pipeline (6 Stages):**
  - **L0 Discover:** `core.py` (instruction files, hooks, VS Code tasks, tool configs)
  - **L1 Detect:** `core.py` · `prose.py` (26 deterministic rules, fixed weights)
  - **L2 Diff:** `gitdiff.py` · `lock.py` (base vs head, approvals read from base)
  - **L3 Doctor:** `doctor/` (graph hierarchy, D001-D008 hygiene, safe fixes)
  - **L4 Time-Warp:** `timewarp/` (multi-session sandbox, virtual clocks, replay)
  - **L5 Score:** `core.py` (100 - penalties, clean / suspicious / compromised)
- **Outputs:** Terminal, Gate refusal, PR comment, CI-signed `AGENTS.lock`, JSON API.
- **Trust Boundaries:** PRs cannot approve themselves, only CI can sign, scanner never executes target code, supply chain pinned to full 40-char commit SHAs.

---

## 3. Automated Screenshot Engine (Playwright)

Sentinel includes an automated browser capture engine that launches a local FastAPI server in a background thread, opens Chromium via Playwright, navigates through the UI states, and captures pixel-perfect high-DPI screenshots for both light and dark themes.

### Files Involved
- `docs/take_screenshots.py`: Headless browser automation script.
- Output artifacts saved to `docs/img/`:
  - `shot-scanner-light.png` & `shot-scanner-dark.png` (Main scanner view)
  - `shot-measured-light.png` & `shot-measured-dark.png` (Empirical benchmark reproduction tab)
  - `shot-doctor-light.png` & `shot-doctor-dark.png` (Instruction Doctor graph and auto-fixes)
  - `shot-timewarp-light.png` & `shot-timewarp-dark.png` (Time-Warp simulation view)
  - `shot-lints-light.png` & `shot-lints-dark.png` (Hygiene diagnostics and token savings)
  - `browser-demo.gif` (Live browser recording)

### How to Run
```bash
# Ensure playwright is installed in your virtual environment:
pip install playwright pillow
playwright install chromium

# Run the automated screenshot engine:
python docs/take_screenshots.py
```

The script will:
1. Bind a random local port (e.g. `http://127.0.0.1:8765`).
2. Start the Sentinel FastAPI application.
3. Launch Chromium at 1280x820 viewport with 2x device scale factor (Retina quality).
4. Cycle through dark and light color schemes.
5. Capture each interface state and save PNGs directly to `docs/img/`.
6. Terminate the background server cleanly upon completion.

---

## 4. Terminal Milestone Animation (`demo.gif`)

The interactive 4-phase terminal animation at the top of the README is generated programmatically to ensure it reflects real engine output across 4 key milestones.

### Files Involved
- `scripts/build_demo_gif.py`: Terminal frame compositor and GIF encoder (Pillow-based, standard library rendering).
- Output: `docs/img/demo.gif`

### How to Run
```bash
python scripts/build_demo_gif.py
```

### The 4 Milestones Demonstrated
1. **Milestone 1 (Static Scan):** Scanning `CLAUDE.md` — reveals 792 hidden zero-width characters and exfiltration instruction (`COMPROMISED 10/100`).
2. **Milestone 2 (Time-Warp Sandbox):** Multi-session replay catches dormant sleeper attack acting only from the 3rd session onward (`SUSPICIOUS [D1]`).
3. **Milestone 3 (Instruction Doctor):** Deterministic hygiene check cleans duplicate rules and dead imports, saving 247 tokens (`-247 tokens`).
4. **Milestone 4 (Rewrite Gate):** Red-team test blocks poisoned suggestion attempting `curl | bash` reverse shell (`0 escapes, 100% blocked`).

---

## 5. Extreme Industrial Stress-Testing Suite

To prove industrial resilience, Sentinel includes an extreme soak and stress testing suite derived from analyzing 388 repositories and 9,529 ecosystem skills.

### Files Involved
- `tests/v5/test_extreme_stress.py`: Pytest suite verifying edge cases, large payloads, recursion depth, and thread safety.
- `bench/extreme_stress_runner.py`: High-concurrency benchmark harness measuring lines/sec, memory leak, and throughput.
- `reports/ECOSYSTEM_STRESS_ANALYSIS.md`: Formal stress-testing engineering report.
- `reports/extreme_stress_report.html`: Luxury-minimal editorial HTML visualization.

### How to Run
```bash
# Run pytest stress tests:
pytest tests/v5/test_extreme_stress.py -v

# Run the 64-worker soak benchmark:
python bench/extreme_stress_runner.py
```

### Key Performance Baselines
- **Megadoc Soak:** 50,000 lines parsed in 2.56s (**19,544 lines/sec**, 0.0 MB memory leak).
- **Megaline Hostility:** 500,000 characters on a single line handled in 1.45s (**344,874 chars/sec**, 0 stack overflow).
- **High Concurrency:** 64 parallel threads processing 2,000 scans in 4.61s (**433.5 scans/sec**, 100% thread safe).
- **Include Hierarchy:** 100 levels of nested `@include` directives traversed in **< 15 ms** with instant cycle loop abort.

---

## 6. Verifying Links and Working Buttons

Every button, link, and anchor in `README.md` must work. Broken links or 404 errors fail CI.

### 1. Offline Verification (`pytest tests/v5/test_readme.py`)
Validates:
- Every image path referenced in the markdown exists on disk and is tracked by Git (`git ls-files`).
- Every `#anchor` link lands on an actual heading in `README.md`.
- All button SVGs (`docs/img/btn-*.svg`) are wrapped in clickable anchor tags.
- Light and dark variants exist for all diagrams and SVGs.
- The committed SVGs in `docs/img/` exactly match the output of `docs/build_readme_assets.py`.

### 2. Online Verification (`python docs/check_readme_links.py`)
Validates:
- Every external URL (GitHub releases, PyPI, Vercel demo, badges, VS Code download) answers with HTTP 200.
- Releases and downloadable assets (such as `sentinel-md.vsix`) are actively published.

### How to Upload New Release Assets
If an extension release asset URL returns 404:
```bash
# Upload the extension package to the latest GitHub release
gh release upload v1.0.0 frontend/sentinel-md.vsix --clobber
```

---

## 7. Quality Invariants Summary

When editing or updating `README.md`:
1. **Zero AI Slop:** Keep language precise, clear, and direct. Avoid generic marketing buzzwords.
2. **Palette Harmony:** Use clean, editorial palettes (Apple / Samsung design language). Strictly avoid neon cyan, Matrix-style green-on-black terminal clichés.
3. **No UI Changes:** Do not alter `frontend/` files. The project web app remains untouched.
4. **All Tests Pass:** The entire 340-test suite, `sentinel selftest`, and `sentinel scan .` must remain completely green.
