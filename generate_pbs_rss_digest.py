#!/usr/bin/env python3
"""Build an HTML digest from the PBS NewsHour headlines RSS feed."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import gzip
import html
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

FEED_URL = "https://www.pbs.org/newshour/feeds/rss/headlines"
MAX_ITEMS = 15
MAX_FEED_BYTES = 1_500_000
MAX_ARTICLE_BYTES = 2_500_000
REQUEST_DELAY = 0.5
ASSET_DIR = pathlib.Path("pbs_assets")
DEFAULT_HTML = "pbs_rss_digest.html"
DEFAULT_JSON = "pbs_rss_digest.json"

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
IMG_PATTERN = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
OG_PATTERN = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', re.I)
TRIM_PREFIXES = (
    "Read More:",
    "READ MORE:",
    "Watch:",
    "WATCH:",
    "Notice:",
    "NOTICE:",
)
TRIM_CONTAINS = (
    "Support trusted journalism",
    "Support Provided By:",
    "Subscribe to Here’s the Deal",
    "Subscribe to Here's the Deal",
)
ASCII_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
}


class SnippetStripper(HTMLParser):
    """Strip tags from short HTML snippets."""

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

    def text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def fetch_url(url: str, max_bytes: int, referer: str | None = None, binary: bool = False) -> bytes | str:
    headers = BASE_HEADERS.copy()
    headers.setdefault("Referer", referer or FEED_URL)
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec
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


def parse_feed() -> list[dict[str, str]]:
    xml_text = fetch_url(FEED_URL, MAX_FEED_BYTES)
    if not isinstance(xml_text, str):
        raise ValueError("Expected textual response from PBS feed")
    root = ET.fromstring(xml_text)
    items: list[dict[str, str]] = []
    for item in root.findall("channel/item"):
        if len(items) >= MAX_ITEMS:
            break
        title = normalise_text((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = normalise_text((item.findtext("description") or "").strip())
        media_el = item.find("media:thumbnail", MEDIA_NS)
        if media_el is None:
            media_el = item.find("media:content", MEDIA_NS)
        image_url = media_el.get("url") if media_el is not None else None
        items.append(
            {
                "title": title,
                "link": link,
                "pub_date": pub_date,
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
    return dt_obj.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def strip_snippet(snippet: str) -> str:
    stripper = SnippetStripper()
    stripper.feed(snippet)
    return stripper.text()


def normalise_text(value: str) -> str:
    if not value:
        return ""
    result = html.unescape(value)
    for src, dst in ASCII_REPLACEMENTS.items():
        result = result.replace(src, dst)
    return result.replace("\r", "")


def find_article_image(html_text: str) -> str | None:
    match = OG_PATTERN.search(html_text)
    if match:
        return clean_image_url(match.group(1))
    match = IMG_PATTERN.search(html_text)
    if match:
        return clean_image_url(match.group(1))
    return None


def clean_image_url(url: str) -> str:
    joined = urllib.parse.urljoin("https://www.pbs.org/", url)
    return joined.split("?", 1)[0]


def download_image(url: str, dest: pathlib.Path) -> str | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    name = pathlib.Path(parsed.path).name or "image.jpg"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    dest_path = dest / safe
    if dest_path.exists():
        return str(dest_path)
    try:
        payload = fetch_url(url, 5_000_000, referer=url, binary=True)
    except (urllib.error.URLError, ValueError) as exc:  # type: ignore[attr-defined]
        print(f"Failed to download image {url}: {exc}", file=sys.stderr)
        return None
    if not isinstance(payload, bytes):
        return None
    dest_path.write_bytes(payload)
    return str(dest_path)


def extract_article(link: str) -> tuple[str, str | None]:
    try:
        html_text = fetch_url(link, MAX_ARTICLE_BYTES, referer=link)
    except (urllib.error.URLError, ValueError) as exc:  # type: ignore[attr-defined]
        print(f"Failed to fetch article {link}: {exc}", file=sys.stderr)
        return "", None
    if not isinstance(html_text, str):
        return "", None
    parser = ParagraphExtractor()
    parser.feed(html_text)
    paragraphs = clean_paragraphs(parser.get_paragraphs())
    if paragraphs:
        content = "\n\n".join(paragraphs).strip()
    else:
        fallback = PlainTextExtractor()
        fallback.feed(html_text)
        content = clean_fallback(fallback.get_text())
    image = find_article_image(html_text)
    return content, image


def clean_paragraphs(paragraphs: list[str]) -> list[str]:
    cleaned: list[str] = []
    for raw in paragraphs:
        text = normalise_text(raw.strip())
        if not text:
            continue
        upper_count = sum(1 for ch in text if ch.isupper())
        lower_count = sum(1 for ch in text if ch.islower())
        if upper_count and not lower_count and len(text.split()) <= 6:
            continue
        if text.lower() == "leave your feedback":
            continue
        if any(text.startswith(prefix) for prefix in TRIM_PREFIXES):
            continue
        if any(needle in text for needle in TRIM_CONTAINS):
            continue
        if cleaned and text == cleaned[-1]:
            continue
        cleaned.append(text)
    return cleaned


def clean_fallback(text: str) -> str:
    value = normalise_text(text)
    cleaned_lines: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() == "leave your feedback":
            continue
        if any(stripped.startswith(prefix) for prefix in TRIM_PREFIXES):
            continue
        if any(needle in stripped for needle in TRIM_CONTAINS):
            continue
        cleaned_lines.append(stripped)
    return "\n\n".join(cleaned_lines)


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html(entries: list[dict[str, str]], output_path: pathlib.Path) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    articles_html: list[str] = []
    for article in entries:
        title = html_escape(article["title"])
        link = html_escape(article["link"])
        pub_date = html_escape(article.get("pub_date_fmt", ""))
        raw_content = (article.get("content") or article.get("snippet") or "").strip()
        paragraphs = [html_escape(part.strip()) for part in raw_content.split("\n\n") if part.strip()]
        image_html = ""
        if article.get("image_local"):
            rel = html_escape(str(pathlib.Path(article["image_local"]).relative_to(output_path.parent)))
            image_html = f"        <div class=\"image\"><img src=\"{rel}\" alt=\"{title}\"></div>\n"
        snippet_html = ""
        if article.get("snippet") and article.get("content") and article["snippet"].strip() and article["snippet"].strip() not in article["content"]:
            snippet_html = f"        <p class=\"snippet\">{html_escape(article['snippet'].strip())}</p>\n"
        content_html = "\n".join(f"        <p>{para}</p>" for para in paragraphs) if paragraphs else "        <p>No article content available.</p>"
        articles_html.append(
            "    <article class=\"story\">\n"
            f"        <h2><a href=\"{link}\" target=\"_blank\" rel=\"noopener noreferrer\">{title}</a></h2>\n"
            f"        <p class=\"meta\">{pub_date}</p>\n"
            f"{image_html}"
            f"{snippet_html}"
            f"{content_html}\n"
            "    </article>"
        )
    html_doc = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <title>PBS NewsHour RSS Digest</title>\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 1000px; line-height: 1.6; }\n"
        "        header { text-align: center; margin-bottom: 2rem; }\n"
        "        article.story { border-bottom: 1px solid #ddd; padding: 1.5rem 0; }\n"
        "        article.story:last-of-type { border-bottom: none; }\n"
        "        h2 { margin-bottom: 0.6rem; }\n"
    "        .meta { color: #555; font-size: 0.9rem; }\n"
    "        .snippet { font-style: italic; color: #333; }\n"
    "        article.story p { margin: 0.6rem 0; }\n"
    "        .image { margin: 1rem 0; }\n"
        "        .image img { max-width: 100%; border-radius: 4px; height: auto; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <header>\n"
        "        <h1>PBS NewsHour Headlines</h1>\n"
        f"        <p>Generated {html_escape(now)}</p>\n"
        "    </header>\n"
        + "\n".join(articles_html)
        + "\n</body>\n</html>\n"
    )
    output_path.write_text(html_doc, encoding="utf-8")


def write_json(entries: list[dict[str, str]], output_path: pathlib.Path) -> None:
    import json

    serialisable = []
    for article in entries:
        record = {key: value for key, value in article.items() if key != "image_local"}
        serialisable.append(record)
    output_path.write_text(json.dumps(serialisable, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a digest from PBS NewsHour RSS feed.")
    parser.add_argument("--html-output", default=DEFAULT_HTML, help="HTML output file")
    parser.add_argument("--json-output", default=DEFAULT_JSON, help="JSON output file")
    parser.add_argument("--skip-json", action="store_true", help="Skip writing JSON output")
    parser.add_argument("--no-images", action="store_true", help="Skip downloading article images")
    parser.add_argument("--limit", type=int, default=MAX_ITEMS, help="Maximum number of articles to include")
    args = parser.parse_args()

    ASSET_DIR.mkdir(exist_ok=True)

    items = parse_feed()
    if args.limit > 0:
        items = items[: args.limit]

    collected: list[dict[str, str]] = []
    for idx, item in enumerate(items, start=1):
        time.sleep(REQUEST_DELAY)
        snippet = normalise_text(strip_snippet(item["description"]))
        content, article_image = extract_article(item["link"])
        image_url = article_image or item.get("image_url")
        image_local = None
        if image_url and not args.no_images:
            image_local = download_image(image_url, ASSET_DIR)
        entry = {
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
        if idx % 5 == 0:
            print(f"Processed {idx} articles", file=sys.stderr)

    html_output = pathlib.Path(args.html_output)
    render_html(collected, html_output)
    print(f"Wrote HTML output to {html_output}")

    if not args.skip_json:
        json_output = pathlib.Path(args.json_output)
        write_json(collected, json_output)
        print(f"Saved JSON data to {json_output}")


if __name__ == "__main__":
    main()
