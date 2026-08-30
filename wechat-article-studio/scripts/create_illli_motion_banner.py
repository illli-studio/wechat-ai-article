#!/usr/bin/env python3
"""Create a lightweight animated GIF banner that can be used in WeChat articles."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "assets" / "fonts" / "NotoSansSC-Regular.ttf"
LOGO = ROOT / "assets" / "brand" / "illli-logo.png"


def make_frame(frame: int, total: int, size: tuple[int, int]) -> Image.Image:
    width, height = size
    phase = frame / total * math.tau
    image = Image.new("RGBA", size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Soft lavender-to-mint light that moves without changing the layout.
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    purple_x = int(width * (0.78 + 0.10 * math.sin(phase)))
    green_x = int(width * (0.12 + 0.08 * math.cos(phase)))
    purple_y = int(height * 0.16)
    green_y = int(height * 0.88)
    gd.ellipse((purple_x - 220, purple_y - 220, purple_x + 220, purple_y + 220), fill=(79, 70, 229, 60))
    gd.ellipse((green_x - 180, green_y - 180, green_x + 180, green_y + 180), fill=(52, 211, 153, 52))
    glow = glow.filter(ImageFilter.GaussianBlur(34))
    image = Image.alpha_composite(image, glow)
    draw = ImageDraw.Draw(image)

    for x in range(0, width, 36):
        draw.line((x, 0, x, height), fill=(100, 116, 139, 16), width=1)
    for y in range(0, height, 36):
        draw.line((0, y, width, y), fill=(100, 116, 139, 14), width=1)

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo_h = 34
    logo = logo.resize((int(logo.width * logo_h / logo.height), logo_h), Image.Resampling.LANCZOS)
    text_font = ImageFont.truetype(str(FONT), 23)
    label = "illli WEEKLY  ·  超灵感 AI 工作室"
    label_width = draw.textbbox((0, 0), label, font=text_font)[2]
    x, y = 42, 35
    pill_width = 28 + logo.width + 16 + label_width
    draw.rounded_rectangle((x - 14, y - 10, x + pill_width, y + 52), radius=30, fill=(255, 255, 255, 220), outline=(199, 210, 254, 255), width=2)
    image.alpha_composite(logo, (x, y))
    draw.text((x + logo.width + 16, y + 4), label, font=text_font, fill=(30, 41, 59, 255))

    title_font = ImageFont.truetype(str(FONT), 38)
    draw.text((42, 106), "灵感不止于想象", font=title_font, fill=(9, 9, 11, 255))
    draw.text((42, 156), "超灵感让它落地", font=title_font, fill=(79, 70, 229, 255))
    pulse = 4 + int(3 * (1 + math.sin(phase)) / 2)
    for i, color in enumerate(((79, 70, 229, 230), (52, 211, 153, 220), (251, 191, 36, 220))):
        cx = width - 90 - i * 30
        cy = 50 + (pulse if i == 1 else 0)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color)
    draw.line((42, height - 31, width - 42, height - 31), fill=(148, 163, 184, 135), width=1)
    small = ImageFont.truetype(str(FONT), 15)
    draw.text((42, height - 25), "AI 产品  ·  创意实践  ·  行业观察", font=small, fill=(71, 85, 105, 255))
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--duration", type=int, default=90)
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = [make_frame(i, args.frames, (640, 260)) for i in range(args.frames)]
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=args.duration, loop=0, optimize=True, disposal=2)
    print(output)


if __name__ == "__main__":
    main()
