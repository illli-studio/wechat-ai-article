#!/usr/bin/env python3
"""Create wide and square covers for an AI-news WeChat article."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "assets" / "fonts" / "NotoSansSC-Regular.ttf"
LOGO = ROOT / "assets" / "brand" / "illli-logo.png"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size=size)


def gradient(size: tuple[int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            t = (x / max(width - 1, 1)) * 0.65 + (y / max(height - 1, 1)) * 0.35
            r = int(255 - 8 * t)
            g = int(255 - 9 * t)
            b = int(255 - 2 * t)
            pixels[x, y] = (r, g, b)
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    radius = int(min(size) * 0.62)
    gd.ellipse((width - radius, -radius // 2, width + radius // 3, radius), fill=(79, 70, 229, 72))
    gd.ellipse((-radius // 2, height - radius // 2, radius, height + radius), fill=(52, 211, 153, 66))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=max(20, radius // 4)))
    return Image.alpha_composite(image.convert("RGBA"), glow)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    current = ""
    processed = 0
    for char in text:
        candidate = current + char
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            current = candidate
            processed += 1
        else:
            if len(lines) < max_lines - 1 and current:
                lines.append(current)
                current = char
                processed += 1
            else:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if processed < len(text) and lines:
        while draw.textbbox((0, 0), lines[-1] + "…", font=fnt)[2] > max_width and lines[-1]:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def draw_cover(size: tuple[int, int], title: str, subtitle: str, issue: str) -> Image.Image:
    width, height = size
    image = gradient(size)
    draw = ImageDraw.Draw(image)
    scale = width / 1080
    margin = int(70 * scale)

    # Subtle editorial grid and signal dots.
    grid = max(28, int(54 * scale))
    for x in range(0, width, grid):
        draw.line((x, 0, x, height), fill=(100, 116, 139, 15), width=1)
    for y in range(0, height, grid):
        draw.line((0, y, width, y), fill=(100, 116, 139, 13), width=1)
    dot_r = max(3, int(5 * scale))
    for i in range(6):
        cx = width - margin - i * int(24 * scale)
        cy = margin // 2
        alpha = 230 - i * 28
        draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=(52, 211, 153, alpha))

    watermark = Image.open(LOGO).convert("RGBA")
    watermark = watermark.crop(watermark.getbbox())
    mark_h = int(height * (0.43 if width / height > 1.8 else 0.42))
    mark_w = int(watermark.width * mark_h / watermark.height)
    watermark = watermark.resize((mark_w, mark_h), Image.Resampling.LANCZOS)
    alpha = watermark.getchannel("A").point(lambda value: int(value * 0.09))
    watermark.putalpha(alpha)
    mark_x = width - margin - mark_w
    mark_y = height - margin - mark_h - int(30 * scale)
    image.alpha_composite(watermark, (mark_x, mark_y))

    label_font = font(max(17, int(24 * scale)))
    title_size = max(40, int((64 if width / height > 1.8 else 72) * scale))
    title_font = font(title_size)
    sub_font = font(max(18, int(27 * scale)))
    small_font = font(max(15, int(20 * scale)))

    label = "illli WEEKLY  ·  超灵感 AI 工作室"
    label_box = draw.textbbox((0, 0), label, font=label_font)
    pad_x, pad_y = int(18 * scale), int(10 * scale)
    label_w = label_box[2] - label_box[0] + pad_x * 2
    label_h = label_box[3] - label_box[1] + pad_y * 2
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo_h = max(24, int(31 * scale))
    logo_w = int(logo.width * logo_h / logo.height)
    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    label_w += logo_w + int(14 * scale)
    draw.rounded_rectangle((margin, margin, margin + label_w, margin + label_h), radius=label_h // 2, fill=(255, 255, 255, 220), outline=(199, 210, 254, 255), width=max(1, int(2 * scale)))
    image.alpha_composite(logo, (margin + pad_x, margin + (label_h - logo_h) // 2))
    draw.text((margin + pad_x + logo_w + int(14 * scale), margin + pad_y - int(3 * scale)), label, font=label_font, fill=(30, 41, 59, 255))

    max_lines = 2 if width / height > 1.8 else 4
    title_top = margin + label_h + int(36 * scale)
    lines = wrap(draw, title, title_font, width - margin * 2, max_lines)
    line_height = int(title_size * 1.24)
    for i, line in enumerate(lines):
        draw.text((margin, title_top + i * line_height), line, font=title_font, fill=(9, 9, 11, 255))

    bottom = height - margin
    draw.line((margin, bottom - int(52 * scale), width - margin, bottom - int(52 * scale)), fill=(148, 163, 184, 115), width=1)
    if subtitle:
        draw.text((margin, bottom - int(40 * scale)), subtitle, font=sub_font, fill=(71, 85, 105, 255))
    issue_box = draw.textbbox((0, 0), issue, font=small_font)
    draw.text((width - margin - (issue_box[2] - issue_box[0]), bottom - int(37 * scale)), issue, font=small_font, fill=(52, 211, 153, 255))
    return image.convert("RGB")


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="JPEG", quality=94, optimize=True, progressive=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", default="本周 AI 大事，一次看完")
    parser.add_argument("--issue", default="WEEKLY")
    parser.add_argument("--wide", required=True, help="2.35:1 cover JPG")
    parser.add_argument("--square", required=True, help="1:1 share cover JPG")
    args = parser.parse_args()
    wide = Path(args.wide).expanduser().resolve()
    square = Path(args.square).expanduser().resolve()
    save(draw_cover((1080, 460), args.title, args.subtitle, args.issue), wide)
    save(draw_cover((1080, 1080), args.title, args.subtitle, args.issue), square)
    print(wide)
    print(square)


if __name__ == "__main__":
    main()
