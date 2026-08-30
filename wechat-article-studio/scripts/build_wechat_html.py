#!/usr/bin/env python3
"""Build WeChat-compatible inline-style HTML from a Markdown article."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


ACCENT = "#4F46E5"
ACCENT_2 = "#34D399"
INK = "#09090B"
TEXT = "#27272A"
MUTED = "#64748B"
PAPER = "#FFFFFF"
SOFT = "#F8FAFC"
SOURCE_RE = re.compile(r"\[(S\d{2,})\]")
IMAGE_RE = re.compile(r'^!\[([^\]]*)\]\(([^\s\)]+)(?:\s+"([^"]*)")?\)$')
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)")
RAW_URL_RE = re.compile(r"https?://[^\s]+")
SECTION_RE = re.compile(r"^((?:Hunt for|illli(?: for)?)[^｜]+｜.+|彩蛋时间)$", re.I)
ITEM_HEADING_RE = re.compile(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5 :]


def inline(text: str) -> str:
    text = SOURCE_RE.sub("", text)
    links: list[tuple[str, str]] = []

    def stash_link(match: re.Match[str]) -> str:
        links.append((match.group(1), match.group(2).replace("\\_", "_")))
        return f"@@LINK{len(links) - 1}@@"

    text = LINK_RE.sub(stash_link, text)
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"\*\*([^*]+)\*\*",
        r'<strong style="font-weight:700;color:#171A22;">\1</strong>',
        escaped,
    )
    escaped = re.sub(
        r"`([^`]+)`",
        r'<code style="font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#F0EEFF;color:#5B4BD8;padding:2px 5px;border-radius:4px;font-size:0.88em;">\1</code>',
        escaped,
    )
    for index, (label, url) in enumerate(links):
        anchor = (
            f'<a href="{html.escape(url, quote=True)}" '
            f'style="color:{ACCENT};text-decoration:none;border-bottom:1px solid #C7D2FE;">'
            f'{html.escape(label)}</a>'
        )
        escaped = escaped.replace(f"@@LINK{index}@@", anchor)
    return escaped


def split_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    buffer: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []
            continue
        standalone_item = ITEM_HEADING_RE.match(line.strip()) and len(line.strip()) <= 80
        if IMAGE_RE.match(line.strip()) or line.startswith(("#", "> ", "- ")) or SECTION_RE.match(line.strip()) or standalone_item:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []
            blocks.append(line.strip())
        else:
            buffer.append(line.strip())
    if buffer:
        blocks.append("\n".join(buffer))
    return blocks


def source_buttons(urls: list[str]) -> str:
    links = []
    for index, url in enumerate(urls, 1):
        label = "查看原文" if len(urls) == 1 else f"来源 {index}"
        links.append(
            f'<a href="{html.escape(url.replace("\\_", "_"), quote=True)}" '
            f'style="display:inline-block;margin:0 8px 8px 0;padding:7px 13px;border:1px solid #C7D2FE;'
            f'border-radius:999px;color:{ACCENT};text-decoration:none;font-size:13px;line-height:1.2;">{label} ↗</a>'
        )
    return '<section style="margin:10px 0 30px;">' + "".join(links) + "</section>"


def stats_block(text: str) -> str | None:
    pairs = re.findall(r"(\d+)\s*(条新鲜\s*资讯|个有用\s*工具|个有趣\s*案例|个鲜明\s*观点)", text)
    if len(pairs) < 3:
        return None
    cells = []
    for number, label in pairs:
        cells.append(
            '<span style="display:inline-block;vertical-align:top;box-sizing:border-box;width:24%;min-width:72px;'
            'padding:14px 4px;text-align:center;">'
            f'<strong style="display:block;font-size:25px;line-height:1;color:{ACCENT};font-weight:800;">{number}</strong>'
            f'<span style="display:block;margin-top:7px;color:{MUTED};font-size:12px;line-height:1.35;">{html.escape(label.replace(" ", ""))}</span>'
            '</span>'
        )
    return (
        f'<section style="margin:20px 0 34px;padding:8px 4px;background:{SOFT};border-radius:14px;'
        'border:1px solid #ECEEF4;text-align:center;">' + "".join(cells) + "</section>"
    )


def build_content(body: str, image_prefix: str = "", date_label: str = "") -> tuple[str, str]:
    title = ""
    pieces: list[str] = []
    item_number = 0
    current_section = ""
    source_queue: list[str] = []

    def flush_sources() -> None:
        nonlocal source_queue
        if source_queue:
            pieces.append(source_buttons(source_queue))
            source_queue = []

    for block in split_blocks(body):
        if block.startswith("# "):
            title = block[2:].strip()
            continue

        section_text = re.sub(r"^#{1,3}\s+", "", block).strip()
        section_match = SECTION_RE.match(section_text)
        if section_match:
            flush_sources()
            current_section = section_text
            item_number = 0
            if "｜" in section_text:
                english, chinese = [part.strip() for part in section_text.split("｜", 1)]
            else:
                english, chinese = "BONUS", section_text
            pieces.append(
                f'<section style="margin:48px 0 26px;padding:22px 22px 20px;background:linear-gradient(135deg,#FFFFFF 0%,#F8FAFC 58%,#EEF2FF 100%);border:1px solid #E2E8F0;border-left:5px solid {ACCENT};border-radius:18px;'
                'box-shadow:0 10px 26px rgba(79,70,229,.07);">'
                f'<span style="display:block;color:{ACCENT};font-size:11px;line-height:1;letter-spacing:2px;font-weight:700;">{html.escape(english.upper())}</span>'
                f'<strong style="display:block;margin-top:9px;color:{INK};font-size:23px;line-height:1.3;font-weight:800;">{html.escape(chinese)}</strong>'
                '</section>'
            )
            continue

        image_match = IMAGE_RE.match(block)
        if image_match:
            flush_sources()
            alt, rel, caption = image_match.groups()
            src = image_prefix + rel.replace("\\", "/")
            is_lead = rel.lower().endswith("_002.gif")
            radius = "4px" if is_lead else "12px"
            margin = "8px 0 26px" if is_lead else "18px 0 28px"
            pieces.append(
                f'<section style="margin:{margin};text-align:center;line-height:0;">'
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt or "文章配图", quote=True)}" '
                f'style="display:block;width:100%;height:auto;margin:0 auto;border-radius:{radius};" />'
                + (f'<span style="display:block;margin-top:9px;color:{MUTED};font-size:12px;line-height:1.5;">{html.escape(caption)}</span>' if caption else "")
                + '</section>'
            )
            continue

        if RAW_URL_RE.fullmatch(block.replace("\\_", "_")):
            source_queue.append(block.replace("\\_", "_"))
            continue
        raw_urls = RAW_URL_RE.findall(block.replace("\\_", "_"))
        if raw_urls and re.sub(RAW_URL_RE, "", block.replace("\\_", "_")).strip() == "":
            source_queue.extend(raw_urls)
            continue

        flush_sources()
        stat = stats_block(block)
        if stat:
            pieces.append(stat)
            continue

        if ITEM_HEADING_RE.match(block) and len(block) <= 80:
            item_number += 1
            number = f"{item_number:02d}"
            pieces.append(
                f'<section style="margin:38px 0 17px;padding:0 0 0 15px;border-left:4px solid {ACCENT};">'
                f'<span style="display:block;margin-bottom:7px;color:{ACCENT};font-size:11px;line-height:1;letter-spacing:1.6px;font-weight:800;">'
                f'{html.escape(current_section.split("｜", 1)[0].upper() if current_section else "WEEKLY")} · {number}</span>'
                f'<strong style="display:block;color:{INK};font-size:20px;line-height:1.5;font-weight:800;">{inline(block)}</strong>'
                '</section>'
            )
            continue

        if block.startswith(("## ", "### ")):
            level = 2 if block.startswith("## ") else 3
            text = block[3:].strip() if level == 2 else block[4:].strip()
            # Long markdown headings in scraped articles are usually ordinary body paragraphs.
            if level == 3 and len(text) > 45 and not re.match(r"^[\U0001F300-\U0001FAFF]", text):
                pieces.append(
                    f'<p style="margin:0 0 19px;text-align:justify;">{inline(text)}</p>'
                )
                continue
            item_number += 1
            number = f"{item_number:02d}"
            pieces.append(
                f'<section style="margin:38px 0 17px;padding:0 0 0 15px;border-left:4px solid {ACCENT};">'
                f'<span style="display:block;margin-bottom:7px;color:{ACCENT};font-size:11px;line-height:1;letter-spacing:1.6px;font-weight:800;">'
                f'{html.escape(current_section.split("｜", 1)[0].upper() if current_section else "WEEKLY")} · {number}</span>'
                f'<strong style="display:block;color:{INK};font-size:20px;line-height:1.5;font-weight:800;">{inline(text)}</strong>'
                '</section>'
            )
            continue

        if block.startswith("> "):
            pieces.append(
                f'<blockquote style="margin:24px 0;padding:18px 20px;background:#EEF2FF;border-left:4px solid {ACCENT};'
                f'border-radius:0 12px 12px 0;color:#3730A3;font-size:15px;line-height:1.8;">{inline(block[2:])}</blockquote>'
            )
            continue

        if block.startswith("- "):
            items = [line[2:].strip() for line in block.splitlines() if line.startswith("- ")]
            rows = "".join(
                f'<li style="margin:8px 0;padding-left:4px;">{inline(item)}</li>'
                for item in items
            )
            pieces.append(f'<ul style="margin:16px 0 24px;padding-left:22px;">{rows}</ul>')
            continue

        if block.lower().startswith("prompts:"):
            prompt_lines = block.splitlines()
            pieces.append(
                f'<section style="margin:18px 0 26px;padding:18px 20px;background:{SOFT};border-radius:12px;border:1px solid #E9EAF0;">'
                '<strong style="display:block;margin-bottom:8px;color:#5B4BD8;font-size:13px;letter-spacing:1px;">PROMPTS</strong>'
                + "".join(f'<code style="display:block;margin:5px 0;color:#555B68;font-size:13px;line-height:1.6;">{html.escape(line)}</code>' for line in prompt_lines[1:])
                + '</section>'
            )
            continue

        paragraphs = [line for line in block.splitlines() if line.strip()]
        for paragraph in paragraphs:
            pieces.append(
                f'<p style="margin:0 0 19px;text-align:justify;">{inline(paragraph)}</p>'
            )

    flush_sources()
    content = (
        f'<section data-wechat-theme="ai-weekly" style="box-sizing:border-box;margin:0 auto;padding:0 8px;max-width:677px;'
        f'background:{PAPER};color:{TEXT};font-size:16px;line-height:1.9;letter-spacing:.02em;'
        f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;">'
        f'<section style="display:block;margin:0 0 24px;padding:0 0 13px;border-bottom:1px solid #E2E8F0;">'
        f'<span style="display:inline-block;color:{ACCENT};font-size:11px;line-height:1;letter-spacing:2px;font-weight:800;">illli AI STUDIO</span>'
        f'<span style="display:inline-block;margin-left:10px;color:#94A3B8;font-size:11px;line-height:1;letter-spacing:1.5px;">WEEKLY DISPATCH</span>'
        f'<span style="float:right;color:{ACCENT_2};font-size:11px;line-height:1;letter-spacing:1px;">{html.escape(date_label)}</span>'
        '</section>'
        '<section style="margin:0 0 26px;">'
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:5px 10px;background:#EEF2FF;border-radius:999px;color:#4338CA;font-size:12px;line-height:1.2;">AI 产品</span>'
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:5px 10px;background:#ECFDF5;border-radius:999px;color:#047857;font-size:12px;line-height:1.2;">创意实践</span>'
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:5px 10px;background:#FFFBEB;border-radius:999px;color:#B45309;font-size:12px;line-height:1.2;">行业观察</span>'
        '</section>'
        + "".join(pieces)
        + '<section style="margin:48px 0 10px;text-align:center;color:#B4B8C2;font-size:11px;letter-spacing:3px;">END</section>'
        + '</section>'
    )
    return title, content


def build_preview(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title or '公众号文章预览')}</title>
  <style>
    *{{box-sizing:border-box}} body{{margin:0;background:#eef0f5;color:{TEXT}}}
    .phone{{width:min(100%,740px);margin:28px auto;padding:34px 24px 70px;background:#fff;box-shadow:0 18px 60px rgba(23,26,34,.12)}}
    .title{{max-width:677px;margin:0 auto 24px;color:{INK};font:800 28px/1.35 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}
    @keyframes illli-rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
    @keyframes illli-breathe{{0%,100%{{box-shadow:0 10px 26px rgba(79,70,229,.05)}}50%{{box-shadow:0 14px 34px rgba(79,70,229,.14)}}}}
    .phone>h1{{animation:illli-rise .6s ease-out both}}
    [data-wechat-theme="ai-weekly"]>section{{animation:illli-rise .7s ease-out both}}
    [data-wechat-theme="ai-weekly"]>section:nth-child(3n){{animation-delay:.08s}}
    [data-wechat-theme="ai-weekly"]>section[style*="linear-gradient"]{{animation:illli-rise .8s ease-out both,illli-breathe 5s ease-in-out 1s infinite}}
    @media(prefers-reduced-motion:reduce){{.phone>h1,[data-wechat-theme="ai-weekly"]>section{{animation:none!important}}}}
    @media(max-width:760px){{.phone{{margin:0;padding:24px 14px 60px;box-shadow:none}}.title{{font-size:24px}}}}
  </style>
</head>
<body><main class="phone"><h1 class="title">{html.escape(title)}</h1>{content}</main></body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Markdown article")
    parser.add_argument("--output", required=True, help="Body-only WeChat HTML output")
    parser.add_argument("--preview", help="Standalone browser preview HTML")
    parser.add_argument("--image-prefix", default="", help="Optional URL/path prefix for images")
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    meta, body = parse_frontmatter(source.read_text(encoding="utf-8"))
    title, content = build_content(body, args.image_prefix, meta.get("date", "2026 · 08 · 30"))
    title = meta.get("title") or title
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    if args.preview:
        preview = Path(args.preview).expanduser().resolve()
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_text(build_preview(title, content), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
