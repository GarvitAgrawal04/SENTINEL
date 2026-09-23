#!/usr/bin/env python3
"""
scripts/generate_architecture_diagram.py
Generates world-class, eye-comforting, pixel-perfect SVG architecture diagrams for SENTINEL.
Standard library only; zero dependencies; deterministic output.
Generates:
  - docs/img/architecture-light.svg
  - docs/img/architecture-dark.svg
"""

import os
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "img"

SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace"

THEMES = {
    "light": {
        "bg": "#FAF9F6",
        "card_bg": "#FFFFFF",
        "card_subtle": "#F5F4EF",
        "engine_bg": "#F8F7F2",
        "border": "#E5E2D9",
        "border_subtle": "#EDEAE1",
        "border_engine": "#D9D5CA",
        "text_main": "#1C1917",
        "text_muted": "#57534E",
        "text_light": "#8C857B",
        "primary": "#C2410C",          # Warm Terracotta
        "primary_soft": "#FFEDD5",
        "accent_blue": "#2563EB",      # Cobalt Blue
        "accent_blue_soft": "#EFF6FF",
        "accent_indigo": "#4338CA",    # Royal Indigo
        "accent_indigo_soft": "#EEF2FF",
        "accent_green": "#15803D",     # Forest Green
        "accent_green_soft": "#DCFCE7",
        "accent_amber": "#B45309",     # Warm Amber
        "accent_amber_soft": "#FEF3C7",
        "accent_rose": "#BE123C",      # Crimson Rose
        "accent_rose_soft": "#FFE4E6",
        "flow_line": "#A8A29E",
        "flow_active": "#C2410C"
    },
    "dark": {
        "bg": "#141517",
        "card_bg": "#1C1D21",
        "card_subtle": "#22242A",
        "engine_bg": "#181A1F",
        "border": "#2E313A",
        "border_subtle": "#272930",
        "border_engine": "#333742",
        "text_main": "#F3F4F6",
        "text_muted": "#9CA3AF",
        "text_light": "#6B7280",
        "primary": "#FB923C",
        "primary_soft": "#2D1B11",
        "accent_blue": "#60A5FA",
        "accent_blue_soft": "#14253D",
        "accent_indigo": "#818CF8",
        "accent_indigo_soft": "#1E1F3B",
        "accent_green": "#4ADE80",
        "accent_green_soft": "#112C1B",
        "accent_amber": "#FBBF24",
        "accent_amber_soft": "#2E2410",
        "accent_rose": "#F87171",
        "accent_rose_soft": "#331616",
        "flow_line": "#4B5563",
        "flow_active": "#FB923C"
    }
}

SHIELD_PATH = "M12 2.6 4.5 5.4v6.2c0 4.6 3 8.4 7.5 9.8 4.5-1.4 7.5-5.2 7.5-9.8V5.4L12 2.6Z"
CHECK_PATH = "M8.4 12.2 11 14.8l4.8-5.2"


def T(x, y, text, size=14, weight=400, fill="#000", anchor="start", family=SANS, extra=""):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(text)}</text>'


def R(x, y, w, h, r=12, fill="none", stroke="none", sw=1.5, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def shield_icon(x, y, size, fill, check_color="#fff"):
    k = size / 24
    return (f'<g transform="translate({x},{y}) scale({k})">'
            f'<path d="{SHIELD_PATH}" fill="{fill}"/>'
            f'<path d="{CHECK_PATH}" fill="none" stroke="{check_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</g>')


def arrow(x1, y1, x2, y2, color, cls="", sw=2):
    head = f'<path d="M{x2 - 8},{y2 - 5} L{x2},{y2} L{x2 - 8},{y2 + 5}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>' if abs(y2 - y1) < 3 else \
           f'<path d="M{x2 - 5},{y2 - 8} L{x2},{y2} L{x2 + 5},{y2 - 8}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    return f'<path class="{cls}" d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{sw}" fill="none" stroke-linecap="round"/>' + head


def generate_architecture_svg(theme_name: str) -> str:
    c = THEMES[theme_name]
    W, H = 1280, 1020

    style = """
    @keyframes flow { to { stroke-dashoffset: -28; } }
    .flow { stroke-dasharray: 6 8; animation: flow 1.6s linear infinite; }
    @media (prefers-reduced-motion: reduce) { .flow { animation: none; } }
    """

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Sentinel System Architecture">')
    svg_parts.append(f'<title>SENTINEL — Complete System Architecture & Pipeline</title>')
    svg_parts.append(f'<style>{style}</style>')
    svg_parts.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}" rx="16"/>')

    # Header / Title Banner inside Diagram
    svg_parts.append(T(48, 48, "SENTINEL ARCHITECTURE", 13, 700, c["primary"], family=SANS, extra='letter-spacing="1.5"'))
    svg_parts.append(T(48, 76, "Autonomous Multi-Layer Agent Defense Engine", 24, 700, c["text_main"]))
    svg_parts.append(T(48, 98, "Zero-execution static verification, temporal Time-Warp replay, instruction hygiene & cryptographic trust boundaries.", 13.5, 400, c["text_muted"]))

    # =========================================================================
    # ROW 1: WHERE A SCAN STARTS (5 Entry Points)
    # =========================================================================
    svg_parts.append(T(48, 142, "WHERE A SCAN STARTS — 5 ENTRY POINTS", 12, 700, c["text_light"], extra='letter-spacing="1.2"'))

    entry_points = [
        ("Command Line", "sentinel scan .", "Instant offline audit", c["accent_blue"]),
        ("Execution Gate", "sentinel run -- claude", "Blocks toxic agent runs", c["primary"]),
        ("Pull Request Check", "GitHub Action", "PR comment + SARIF", c["accent_indigo"]),
        ("Web App & API", "POST /scan/text", "Interactive inspector", c["accent_green"]),
        ("IDE Extension", "VS Code · Cursor", "On-save inline warnings", c["accent_amber"]),
    ]

    card_w = 222
    card_h = 76
    gap = 18
    start_x = 48
    y_entry = 156

    for i, (title, cmd, sub, tag_col) in enumerate(entry_points):
        x = start_x + i * (card_w + gap)
        svg_parts.append(R(x, y_entry, card_w, card_h, 12, c["card_bg"], c["border"], 1.2))
        svg_parts.append(f'<circle cx="{x + 20}" cy="{y_entry + 24}" r="5" fill="{tag_col}"/>')
        svg_parts.append(T(x + 34, y_entry + 28, title, 15, 650, c["text_main"]))
        svg_parts.append(T(x + 20, y_entry + 48, cmd, 12.5, 500, c["text_muted"], family=MONO))
        svg_parts.append(T(x + 20, y_entry + 64, sub, 11.5, 400, c["text_light"]))
        # Connecting flow down to Engine
        arrow_x = x + card_w // 2
        svg_parts.append(arrow(arrow_x, y_entry + card_h, arrow_x, y_entry + card_h + 36, c["flow_line"], cls="flow"))

    # =========================================================================
    # ROW 2: THE 5-STAGE CORE ENGINE (L0 - L5)
    # =========================================================================
    y_engine = 268
    engine_h = 360
    svg_parts.append(R(36, y_engine, W - 72, engine_h, 20, c["engine_bg"], c["border_engine"], 1.5))
    svg_parts.append(T(58, y_engine + 36, "THE CORE ENGINE — 5-STAGE DETERMINISTIC & TIME-WARP PIPELINE", 12.5, 700, c["primary"], extra='letter-spacing="1.3"'))
    svg_parts.append(T(W - 58, y_engine + 36, "Deterministic · Offline · Zero External Network · Memory Bound", 12, 500, c["text_light"], anchor="end"))

    engine_stages = [
        ("L0", "Discover", "Surface Mapping", [
            "instruction files",
            "auto-run hook settings",
            "VS Code tasks.json",
            "unapproved MCP configs",
            "core.py"
        ], c["accent_blue"], c["accent_blue_soft"]),
        ("L1", "Detect", "Static Rules (S1–S26)", [
            "26 deterministic rules",
            "evasion normalization",
            "hook script inspection",
            "tool description poisoning",
            "core.py · prose.py"
        ], c["primary"], c["primary_soft"]),
        ("L2", "Diff", "Behavioral Delta", [
            "base vs head branch",
            "guardrail removed/flipped",
            "new auto-exec targets",
            "approvals read from BASE",
            "gitdiff.py · lock.py"
        ], c["accent_indigo"], c["accent_indigo_soft"]),
        ("L3", "Doctor", "Hygiene & Graph", [
            "@import DAG traversal",
            "cycle detection bombs",
            "token budget estimator",
            "D001–D008 safe quick-fixes",
            "doctor/graph.py · lints.py"
        ], c["accent_amber"], c["accent_amber_soft"]),
        ("L4", "Time-Warp", "Temporal Sandbox", [
            "virtual clock & state world",
            "cassette record/replay",
            "trigger scenario extraction",
            "catches session-3 sleepers",
            "timewarp/runner.py · clock.py"
        ], c["accent_rose"], c["accent_rose_soft"]),
        ("L5", "Score", "Scoring & Explain", [
            "100 − Σ penalties",
            "decisive force -> ≤ 39",
            "approval ceiling -> ≤ 79",
            "plain English impact + fix",
            "score_file · render.py"
        ], c["accent_green"], c["accent_green_soft"]),
    ]

    stage_w = 186
    stage_h = 270
    stage_gap = 14
    stage_start_x = 52
    stage_y = y_engine + 58

    for i, (layer_id, title, subtitle, points, col, soft_col) in enumerate(engine_stages):
        x = stage_start_x + i * (stage_w + stage_gap)
        svg_parts.append(R(x, stage_y, stage_w, stage_h, 14, c["card_bg"], c["border"], 1.2))
        
        # Layer Badge & Title
        svg_parts.append(R(x + 14, stage_y + 14, 38, 24, 6, col, "none"))
        svg_parts.append(T(x + 33, stage_y + 30, layer_id, 12, 700, "#FFFFFF", anchor="middle", family=MONO))
        svg_parts.append(T(x + 60, stage_y + 32, title, 16, 700, c["text_main"]))
        svg_parts.append(T(x + 16, stage_y + 54, subtitle, 11.5, 500, c["text_muted"]))
        svg_parts.append(f'<line x1="{x + 16}" y1="{stage_y + 66}" x2="{x + stage_w - 16}" y2="{stage_y + 66}" stroke="{c["border_subtle"]}" stroke-width="1"/>')

        # Bullet points
        for j, pt in enumerate(points[:-1]):
            by = stage_y + 92 + j * 32
            svg_parts.append(f'<circle cx="{x + 22}" cy="{by - 4}" r="2.5" fill="{col}"/>')
            svg_parts.append(T(x + 32, by, pt, 11.8, 400, c["text_muted"]))

        # Code file footer tag
        svg_parts.append(R(x + 14, stage_y + stage_h - 36, stage_w - 28, 22, 6, soft_col, "none"))
        svg_parts.append(T(x + stage_w // 2, stage_y + stage_h - 22, points[-1], 10.5, 600, col, anchor="middle", family=MONO))

        # Horizontal connecting flow
        if i < len(engine_stages) - 1:
            arrow_start_x = x + stage_w
            arrow_end_x = arrow_start_x + stage_gap
            arrow_mid_y = stage_y + stage_h // 2
            svg_parts.append(arrow(arrow_start_x, arrow_mid_y, arrow_end_x, arrow_mid_y, c["flow_line"]))

    # Connecting flow from Engine to Outputs
    for i in range(5):
        cx = start_x + i * (card_w + gap) + card_w // 2
        svg_parts.append(arrow(cx, y_engine + engine_h, cx, y_engine + engine_h + 38, c["flow_line"], cls="flow"))

    # =========================================================================
    # ROW 3: WHAT COMES OUT (5 Outputs)
    # =========================================================================
    y_out = y_engine + engine_h + 38
    svg_parts.append(T(48, y_out + 16, "WHAT COMES OUT — 5 VERIFIABLE ARTIFACTS", 12, 700, c["text_light"], extra='letter-spacing="1.2"'))

    outputs = [
        ("Terminal Output", "exit 0 clean · 3 susp · 2 comp", "CLI human review text", c["text_main"]),
        ("Agent Refusal", "sentinel: refusing to start", "Agent never runs in hazard", c["accent_rose"]),
        ("PR Diff & SARIF", "GitHub PR comment & scan", "Blocks hostile pull requests", c["accent_indigo"]),
        ("Signed Lock", "AGENTS.lock (ed25519)", "CI signed approval ledger", c["accent_green"]),
        ("Structured JSON", "verdicts, findings & lines", "Feeds web UI & VS Code", c["accent_blue"]),
    ]

    out_h = 76
    for i, (title, line1, line2, tag_col) in enumerate(outputs):
        x = start_x + i * (card_w + gap)
        svg_parts.append(R(x, y_out + 28, card_w, out_h, 12, c["card_bg"], c["border"], 1.2))
        svg_parts.append(f'<circle cx="{x + 20}" cy="{y_out + 50}" r="5" fill="{tag_col}"/>')
        svg_parts.append(T(x + 34, y_out + 54, title, 14.5, 650, c["text_main"]))
        svg_parts.append(T(x + 20, y_out + 74, line1, 12, 500, tag_col if tag_col == c["accent_rose"] else c["text_muted"], family=MONO if "exit" in line1 or "sentinel" in line1 else SANS))
        svg_parts.append(T(x + 20, y_out + 90, line2, 11.5, 400, c["text_light"]))

    # =========================================================================
    # ROW 4: TRUST BOUNDARIES & SECURITY INVARIANTS
    # =========================================================================
    y_trust = y_out + out_h + 50
    trust_h = 130
    svg_parts.append(R(36, y_trust, W - 72, trust_h, 16, c["accent_green_soft"], c["accent_green"], 1.2))
    svg_parts.append(shield_icon(58, y_trust + 22, 28, c["accent_green"], "#FFFFFF"))
    svg_parts.append(T(96, y_trust + 42, "FOUR NON-NEGOTIABLE TRUST BOUNDARIES", 13, 700, c["accent_green"], extra='letter-spacing="1.2"'))

    boundaries = [
        ("PR cannot approve itself", "Approvals & public keys read from base branch, never the incoming change."),
        ("Only CI can sign", "The private signing key is stored in a protected GitHub environment for main."),
        ("Zero-execution invariant", "Sentinel reads plain text; never executes, imports, or evals the scanned project."),
        ("Pinned supply chain", "All CI actions pinned to full 40-char commit SHAs; zero external runtime dependencies.")
    ]

    col_w = (W - 144) // 2
    for idx, (head, desc) in enumerate(boundaries):
        bx = 58 + (idx % 2) * col_w
        by = y_trust + 72 + (idx // 2) * 28
        svg_parts.append(f'<circle cx="{bx + 6}" cy="{by - 4}" r="3" fill="{c["accent_green"]}"/>')
        svg_parts.append(T(bx + 18, by, f"{head}: ", 13, 700, c["text_main"]))
        svg_parts.append(T(bx + 18 + int(len(head) * 7.8) + 12, by, desc, 13, 400, c["text_muted"]))

    svg_parts.append('</svg>\n')
    return "".join(svg_parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        content = generate_architecture_svg(theme)
        out_path = OUT / f"architecture-{theme}.svg"
        out_path.write_text(content, encoding="utf-8")
        print(f"Generated {out_path} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()
