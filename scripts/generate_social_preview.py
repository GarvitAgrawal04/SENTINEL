"""Generate the 1280x640 social preview image (OpenGraph / GitHub card) for Sentinel."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "img" / "social-preview.png"


def create_social_preview():
    w, h = 1280, 640
    img = Image.new("RGBA", (w, h), (13, 17, 23, 255))  # GitHub dark mode canvas
    draw = ImageDraw.Draw(img)

    # Subtle background gradient and border
    for y in range(h):
        alpha = int(20 + 25 * (y / h))
        draw.line([(0, y), (w, y)], fill=(18, 26, 40, alpha))

    # Outer border
    draw.rectangle([10, 10, w - 10, h - 10], outline=(48, 54, 61, 255), width=2)
    # Inner accent border line
    draw.rectangle([14, 14, w - 14, h - 14], outline=(36, 87, 245, 120), width=1)

    # Decorative background grid dots
    for gx in range(40, w - 40, 40):
        for gy in range(40, h - 40, 40):
            draw.point((gx, gy), fill=(30, 40, 60, 180))

    # Shield Icon Emblem at top-left
    # Draw Shield
    sx, sy = 60, 60
    # Shield shape points
    shield_pts = [
        (sx + 35, sy),
        (sx + 70, sy + 15),
        (sx + 70, sy + 55),
        (sx + 35, sy + 85),
        (sx, sy + 55),
        (sx, sy + 15),
    ]
    draw.polygon(shield_pts, fill=(36, 87, 245, 255), outline=(59, 130, 246, 255))
    # Shield checkmark
    draw.line([(sx + 20, sy + 45), (sx + 32, sy + 58), (sx + 54, sy + 32)], fill=(255, 255, 255, 255), width=5)

    # Load system or default font
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 46)
        font_subtitle = ImageFont.truetype("arial.ttf", 22)
        font_pill = ImageFont.truetype("arialbd.ttf", 15)
        font_card_head = ImageFont.truetype("arialbd.ttf", 19)
        font_card_body = ImageFont.truetype("arial.ttf", 15)
        font_footer = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font_title = font_subtitle = font_pill = font_card_head = font_card_body = font_footer = ImageFont.load_default()

    # Title & Subtitle
    draw.text((150, 62), "SENTINEL", fill=(255, 255, 255, 255), font=font_title)
    draw.text((150, 118), "Agent Trust Engine · Security Scanner for AI Coding Instructions", fill=(140, 155, 180, 255), font=font_subtitle)

    # Status Pills / Badges
    pills = [
        ("99.7% PRECISION", (34, 197, 94, 255)),
        ("0 FP ON 930 REPOS", (59, 130, 246, 255)),
        ("TIME-WARP SANDBOX", (168, 85, 247, 255)),
        ("INSTRUCTION DOCTOR", (234, 179, 8, 255)),
        ("SIGNED AGENTS.LOCK", (20, 184, 166, 255)),
    ]
    px = 60
    for text, color in pills:
        bbox = font_pill.getbbox(text) if hasattr(font_pill, "getbbox") else (0, 0, len(text)*8, 14)
        pw = bbox[2] - bbox[0] + 20
        draw.rounded_rectangle([px, 170, px + pw, 198], radius=8, fill=(22, 27, 34, 255), outline=color, width=1)
        draw.text((px + 10, 175), text, fill=color, font=font_pill)
        px += pw + 12

    # 3 Feature Showcase Cards
    cards = [
        (
            "Layer 1-3 Precision Detection",
            [
                "• 26 static rules with published weights",
                "• 0 false COMPROMISED on 930 public repos",
                "• Catches hidden text, autorun, exfiltration",
                "• Layer 3 semantic judge: 84.88% holdout recall",
            ],
            (59, 130, 246, 255),
        ),
        (
            "Time-Warp Multi-Moment Sandbox",
            [
                "• Catches dormant sleeper instructions",
                "• Detonates across 11 temporal/branch scenarios",
                "• Replays model calls from cassettes (0 keys in CI)",
                "• 10/10 attacks caught, 0 false alarms on twins",
            ],
            (168, 85, 247, 255),
        ),
        (
            "Instruction Doctor & Rewrite Gate",
            [
                "• D001-D008 deterministic hygiene checks",
                "• Context window reduction (median -20 tokens)",
                "• VS Code Quick Fixes & gated Safe Rewrite",
                "• 30/30 poisoned injection rewrites blocked (0 escapes)",
            ],
            (34, 197, 94, 255),
        ),
    ]

    card_w = 360
    card_h = 240
    card_y = 220
    for i, (head, points, accent) in enumerate(cards):
        cx = 60 + i * (card_w + 30)
        # Card background
        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + card_h], radius=12, fill=(22, 27, 34, 240), outline=(48, 54, 61, 255), width=1)
        # Top accent bar
        draw.rounded_rectangle([cx + 1, card_y + 1, cx + card_w - 1, card_y + 6], radius=3, fill=accent)
        # Card header
        draw.text((cx + 16, card_y + 20), head, fill=(255, 255, 255, 255), font=font_card_head)
        # Bullet points
        line_y = card_y + 60
        for pt in points:
            draw.text((cx + 16, line_y), pt, fill=(160, 175, 195, 255), font=font_card_body)
            line_y += 34

    # Footer banner
    draw.line([(60, 500), (w - 60, 500)], fill=(48, 54, 61, 255), width=1)
    footer_text = "PyPI: pip install sentinel-md  |  OpenVSX: sentinel-md  |  SARIF 2.1.0  |  CycloneDX SBOM  |  Sigstore Keyless  |  Apache-2.0"
    draw.text((60, 530), footer_text, fill=(140, 155, 175, 255), font=font_footer)
    author_text = "Built by Mayan Kamboj & Garvit Agrawal  ·  https://github.com/GarvitAgrawal04/SENTINEL"
    draw.text((60, 565), author_text, fill=(100, 120, 145, 255), font=font_footer)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Saved social preview card: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    create_social_preview()
