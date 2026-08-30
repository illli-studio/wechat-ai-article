#!/usr/bin/env python3
"""Prepare or create a WeChat Official Account article draft.

Dry-run is the default. Network writes require both --send and
--confirm-create-draft plus account credentials in environment variables.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import mimetypes
import os
import re
import secrets
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image


API = "https://api.weixin.qq.com/cgi-bin"
IMAGE_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.I)
H1_RE = re.compile(r"(?m)^#\s+(.+)$")
PARAGRAPH_RE = re.compile(r"(?m)^(?!#|!\[|https?://|\s*$)(.+)$")


def clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def article_meta(markdown: str) -> tuple[str, str]:
    title_match = H1_RE.search(markdown)
    title = title_match.group(1).strip() if title_match else "AI 周报"
    digest = ""
    for match in PARAGRAPH_RE.finditer(markdown):
        candidate = re.sub(r"\*\*|`", "", match.group(1)).strip()
        if candidate and not candidate.startswith("Hunt for"):
            digest = candidate
            break
    return clip(title, 64), clip(digest or "本周 AI 重要资讯、工具、案例与观点，一次看完。", 120)


def request_json(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errcode") not in (None, 0):
        raise RuntimeError(f"WeChat API error {result.get('errcode')}: {result.get('errmsg', 'unknown error')}")
    return result


def access_token() -> str:
    existing = os.environ.get("WECHAT_ACCESS_TOKEN", "").strip()
    if existing:
        return existing
    app_id = os.environ.get("WECHAT_APP_ID", "").strip()
    app_secret = os.environ.get("WECHAT_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise RuntimeError("Set WECHAT_ACCESS_TOKEN or both WECHAT_APP_ID and WECHAT_APP_SECRET.")
    query = urllib.parse.urlencode({"grant_type": "client_credential", "appid": app_id, "secret": app_secret})
    result = request_json(f"{API}/token?{query}")
    token = result.get("access_token", "")
    if not token:
        raise RuntimeError("WeChat did not return an access token.")
    return token


def multipart_upload(url: str, field: str, path: Path) -> dict:
    boundary = "----CodexWechat" + secrets.token_hex(12)
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="{field}"; filename="{path.name}"\r\n'.encode())
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(url, data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errcode") not in (None, 0):
        raise RuntimeError(f"WeChat upload error {result.get('errcode')}: {result.get('errmsg', 'unknown error')}")
    return result


def compatible_image(path: Path, temp_dir: Path) -> Path:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif"}:
        return path
    converted = temp_dir / f"{path.stem}.png"
    with Image.open(path) as image:
        image.seek(0)
        image.convert("RGB").save(converted, "PNG", optimize=True)
    print(f"WARNING: converted {path.name} to static PNG for WeChat API compatibility", file=sys.stderr)
    return converted


def local_image_paths(content: str, html_path: Path) -> list[Path]:
    result: list[Path] = []
    for match in IMAGE_SRC_RE.finditer(content):
        src = html_lib.unescape(match.group(2))
        if src.startswith(("https://", "http://", "data:")):
            continue
        path = (html_path.parent / urllib.parse.unquote(src)).resolve()
        if path not in result:
            result.append(path)
    return result


def rewrite_images(content: str, html_path: Path, replacements: dict[Path, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        src = html_lib.unescape(match.group(2))
        if src.startswith(("https://", "http://", "data:")):
            return match.group(0)
        local = (html_path.parent / urllib.parse.unquote(src)).resolve()
        return match.group(1) + replacements.get(local, src) + match.group(3)
    return IMAGE_SRC_RE.sub(replace, content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--cover", required=True)
    parser.add_argument("--payload-out", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--open-comments", action="store_true")
    parser.add_argument("--fans-only-comments", action="store_true")
    parser.add_argument("--send", action="store_true", help="Perform uploads and create the draft")
    parser.add_argument("--confirm-create-draft", action="store_true", help="Required together with --send")
    args = parser.parse_args()

    markdown_path = Path(args.markdown).expanduser().resolve()
    html_path = Path(args.html).expanduser().resolve()
    cover_path = Path(args.cover).expanduser().resolve()
    output_path = Path(args.payload_out).expanduser().resolve()
    for path in (markdown_path, html_path, cover_path):
        if not path.is_file():
            raise SystemExit(f"Missing file: {path}")

    markdown = markdown_path.read_text(encoding="utf-8")
    content = html_path.read_text(encoding="utf-8")
    title, digest = article_meta(markdown)
    images = local_image_paths(content, html_path)
    missing = [str(path) for path in images if not path.is_file()]
    if missing:
        raise SystemExit("Missing article images:\n- " + "\n- ".join(missing))

    if args.send != args.confirm_create_draft:
        raise SystemExit("A live draft requires both --send and --confirm-create-draft.")

    if args.send:
        token = access_token()
        replacements: dict[Path, str] = {}
        with tempfile.TemporaryDirectory(prefix="wechat-draft-") as temp:
            temp_dir = Path(temp)
            for image in images:
                upload_path = compatible_image(image, temp_dir)
                result = multipart_upload(f"{API}/media/uploadimg?access_token={urllib.parse.quote(token)}", "media", upload_path)
                replacements[image] = result["url"]
            content = rewrite_images(content, html_path, replacements)
            cover_upload = multipart_upload(
                f"{API}/material/add_material?access_token={urllib.parse.quote(token)}&type=image",
                "media",
                compatible_image(cover_path, temp_dir),
            )
        thumb_media_id = cover_upload["media_id"]
    else:
        replacements = {path: f"wx-upload://{path.name}" for path in images}
        content = rewrite_images(content, html_path, replacements)
        thumb_media_id = "LOCAL_PREVIEW_COVER_MEDIA_ID"

    article = {
        "article_type": "news",
        "title": title,
        "author": clip(args.author, 16),
        "digest": digest,
        "content": content,
        "content_source_url": args.source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1 if args.open_comments else 0,
        "only_fans_can_comment": 1 if args.fans_only_comments else 0,
    }
    payload = {"articles": [article]}
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.send:
        token = access_token()
        response = request_json(f"{API}/draft/add?access_token={urllib.parse.quote(token)}", payload)
        result = {"request": payload, "response": response}
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"DRAFT CREATED: {response.get('media_id', '')}")
    else:
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"DRY RUN OK: {len(images)} inline images, title={len(title)} chars, html={len(content)} chars")
        print(output_path)


if __name__ == "__main__":
    main()
