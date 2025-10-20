#!/usr/bin/env python3
"""Build a NYTimes RSS digest with content and images."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import gzip
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from html.parser import HTMLParser

from generate_us_news_page import ParagraphExtractor, PlainTextExtractor  # type: ignore

FEEDS: dict[str, str] = {
    "World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "U.S.": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "Technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "Science": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
}

MAX_PER_FEED = 5
MAX_FEED_BYTES = 1_500_000
MAX_ARTICLE_BYTES = 2_500_000
REQUEST_DELAY = 0.6
ASSET_DIR = pathlib.Path("nyt_assets")
DEFAULT_HTML = "nyt_rss_digest.html"
DEFAULT_JSON = "nyt_rss_digest.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Accept-Encoding": "gzip, deflate",
}

MEDIA_NS = {"media": "http://search.yahoo.com/mrss/"}
OG_IMAGE_PATTERN = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', re.I)
IMG_PATTERN = re.compile(r'<img[^>]+src="([^"]+)"', re.I)


class _Stripper(HTMLParser):
    """Turn small HTML fragments into plain text."""

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def fetch_url(url: str, max_bytes: int, referer: str | None = None, binary: bool = False) -> bytes | str:
    headers = BASE_HEADERS.copy()
    headers.setdefault("Referer", referer or "https://www.nytimes.com/rss")
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec - controlled host
        raw = response.read(max_bytes)
        encoding = response.headers.get("Content-Encoding", "").lower()
        if "gzip" in encoding:
            raw = gzip.decompress(raw)
        elif "deflate" in encoding:
            raw = zlib.decompress(raw)
        if binary:
            return raw
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def parse_feed(feed_name: str, feed_url: str) -> list[dict[str, str]]:
    xml_text = fetch_url(feed_url, MAX_FEED_BYTES, referer="https://www.nytimes.com/rss")
    if not isinstance(xml_text, str):
        raise ValueError("Expected text response for RSS feed")
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall("channel/item"):
        if len(items) >= MAX_PER_FEED:
            break
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        media_el = item.find("media:content", MEDIA_NS)
        image_url = media_el.get("url") if media_el is not None else None
        items.append(
            {
                "category": feed_name,
                "title": title,
                "link": link,
                "pub_date": pub_date_raw,
                "description": description,
                "image_url": image_url,
            }
        )
    return items


def parse_pub_date(raw: str) -> str:
    try:
        dt_obj = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return raw
    if dt_obj is None:
        return raw
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    dt_local = dt_obj.astimezone()
    return dt_local.strftime("%Y-%m-%d %H:%M %Z")


def strip_html_snippet(fragment: str) -> str:
    stripper = _Stripper()
    stripper.feed(fragment)
    return stripper.get_text()


def extract_article_content(url: str) -> tuple[str, str | None]:
    try:
        html_text = fetch_url(url, MAX_ARTICLE_BYTES, referer=url)
    except (urllib.error.URLError, ValueError) as exc:  # type: ignore[attr-defined]
        print(f"Failed to fetch article {url}: {exc}", file=sys.stderr)
        return "", None
    if not isinstance(html_text, str):
        return "", None
    paragraph_parser = ParagraphExtractor()
    paragraph_parser.feed(html_text)
    paragraphs = paragraph_parser.get_paragraphs()
    if paragraphs:
        body = "\n\n".join(paragraphs[:8]).strip()
    else:
        fallback = PlainTextExtractor()
        fallback.feed(html_text)
        body = fallback.get_text().strip()
    image_url = find_article_image(html_text)
    return body, image_url


def find_article_image(html_text: str) -> str | None:
    match = OG_IMAGE_PATTERN.search(html_text)
    if match:
        return sanitize_image_url(match.group(1))
    match = IMG_PATTERN.search(html_text)
    if match:
        return sanitize_image_url(match.group(1))
    return None


def sanitize_image_url(url: str) -> str:
    parsed = urllib.parse.urljoin("https://www.nytimes.com/", url)
    clean, _, _ = parsed.partition("?")
    return clean


def download_image(url: str, dest_dir: pathlib.Path) -> str | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    name = pathlib.Path(parsed.path).name or "image.jpg"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    target = dest_dir / safe_name
    if target.exists():
        return str(target)
    try:
        binary = fetch_url(url, 5_000_000, referer=url, binary=True)
    except (urllib.error.URLError, ValueError) as exc:  # type: ignore[attr-defined]
        print(f"Failed to download image {url}: {exc}", file=sys.stderr)
        return None
    if not isinstance(binary, bytes):
        return None
    target.write_bytes(binary)
    return str(target)


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html(articles: list[dict[str, str]], output_path: pathlib.Path) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    grouped: dict[str, list[dict[str, str]]] = {}
    for entry in articles:
        grouped.setdefault(entry["category"], []).append(entry)
    sections: list[str] = []
    for category, items in grouped.items():
        rows: list[str] = []
        for article in items:
            title = html_escape(article["title"])
            link = html_escape(article["link"])
            pub_date = html_escape(article.get("pub_date_fmt", ""))
            snippet = html_escape(article.get("snippet", ""))
            content = html_escape(article.get("content", ""))
            image_html = ""
            image_path = article.get("image_local")
            if image_path:
                rel = html_escape(os.path.relpath(image_path, output_path.parent))
                image_html = f"<div class=\"image\"><img src=\"{rel}\" alt=\"{title}\"></div>"
            rows.append(
                "        <article class=\"story\">\n"
                f"            <h3><a href=\"{link}\" target=\"_blank\" rel=\"noopener noreferrer\">{title}</a></h3>\n"
                f"            <p class=\"meta\">{pub_date}</p>\n"
                f"            <p class=\"snippet\">{snippet}</p>\n"
                f"            {image_html}\n"
                f"            <p class=\"content\">{content}</p>\n"
                "        </article>"
            )
        section_html = (
            "    <section class=\"category\">\n"
            f"        <h2>{html_escape(category)}</h2>\n"
            "        " + "\n".join(rows) + "\n"
            "    </section>"
        )
        sections.append(section_html)
    page = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <title>NYTimes RSS Digest</title>\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 1100px; line-height: 1.6; }\n"
        "        header { text-align: center; margin-bottom: 2rem; }\n"
        "        section.category { margin-bottom: 2.5rem; }\n"
        "        article.story { border-bottom: 1px solid #ddd; padding: 1.5rem 0; }\n"
        "        article.story:last-of-type { border-bottom: none; }\n"
        "        h2 { margin-bottom: 1rem; border-bottom: 2px solid #000; padding-bottom: 0.4rem; }\n"
        "        h3 { margin: 0 0 0.4rem; }\n"
        "        .meta { color: #555; font-size: 0.9rem; }\n"
        "        .snippet { font-style: italic; color: #333; }\n"
        "        .content { margin-top: 0.8rem; white-space: pre-wrap; }\n"
        "        .image { margin: 1rem 0; }\n"
        "        .image img { max-width: 100%; height: auto; border-radius: 4px; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <header>\n"
        "        <h1>NYTimes RSS Digest</h1>\n"
        f"        <p>Generated {html_escape(now)}</p>\n"
        "    </header>\n"
        + "\n".join(sections)
        + "\n</body>\n</html>\n"
    )
    output_path.write_text(page, encoding="utf-8")


def write_json(articles: list[dict[str, str]], output_path: pathlib.Path) -> None:
    import json

    serialisable = []
    for entry in articles:
        serialisable.append({key: value for key, value in entry.items() if key != "image_local"})
    output_path.write_text(json.dumps(serialisable, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a NYTimes RSS digest page.")
    parser.add_argument("--html-output", default=DEFAULT_HTML, help="HTML output path")
    parser.add_argument("--json-output", default=DEFAULT_JSON, help="Optional JSON output path")
    parser.add_argument("--skip-json", action="store_true", help="Skip writing JSON output")
    parser.add_argument("--no-images", action="store_true", help="Do not download associated images")
    args = parser.parse_args()

    ASSET_DIR.mkdir(exist_ok=True)

    collected: list[dict[str, str]] = []
    for category, feed_url in FEEDS.items():
        try:
            items = parse_feed(category, feed_url)
        except Exception as exc:  # noqa: BLE001 - surface feed issues
            print(f"Failed to parse feed {category}: {exc}", file=sys.stderr)
            continue
        for item in items:
            time.sleep(REQUEST_DELAY)
            snippet = strip_html_snippet(item["description"])
            content, article_image = extract_article_content(item["link"])
            image_url = article_image or item.get("image_url")
            image_local = None
            if image_url and not args.no_images:
                image_local = download_image(image_url, ASSET_DIR)
            entry = {
                "category": category,
                "title": item["title"],
                "link": item["link"],
                "pub_date": item["pub_date"],
                "pub_date_fmt": parse_pub_date(item["pub_date"]),
                "snippet": snippet,
                "content": content,
            }
            if image_local:
                entry["image_local"] = image_local
            collected.append(entry)
            if len(collected) % 5 == 0:
                print(f"Processed {len(collected)} articles", file=sys.stderr)

    output_html = pathlib.Path(args.html_output)
    render_html(collected, output_html)
    print(f"Wrote HTML output to {output_html}" )

    if not args.skip_json:
        output_json = pathlib.Path(args.json_output)
        write_json(collected, output_json)
        print(f"Saved JSON data to {output_json}")


if __name__ == "__main__":
    main()
