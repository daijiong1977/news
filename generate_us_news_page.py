#!/usr/bin/env python3
"""Fetch the latest US news from Mediastack and render a simple HTML page."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

API_URL = "http://api.mediastack.com/v1/news"
SOURCES = ("abc", "cnn", "bbc", "npr")
API_FETCH_LIMIT = 100
MAX_PER_SOURCE = 5
MAX_TOTAL_ARTICLES = 30


def build_query(api_key: str) -> str:
    """Construct the Mediastack query for the past 24 hours of US news."""
    end_time = dt.datetime.utcnow()
    start_time = end_time - dt.timedelta(days=1)
    params = {
        "access_key": api_key,
        "countries": "us",
        "languages": "en",
        "sources": ",".join(SOURCES),
    "sort": "popularity",
        "date": f"{start_time:%Y-%m-%d},{end_time:%Y-%m-%d}",
        "limit": API_FETCH_LIMIT,
        "offset": 0,
    }
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def fetch_articles(api_key: str, limit: int) -> list[dict]:
    """Call the API and return decorated article dictionaries."""
    url = build_query(api_key)
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.load(response)
    articles = payload.get("data", [])

    now_utc = dt.datetime.now(dt.timezone.utc)
    cutoff = now_utc - dt.timedelta(days=1)
    display_limit = min(max(limit, 0), MAX_TOTAL_ARTICLES)
    if display_limit == 0:
        return []
    filtered: list[dict] = []
    source_counts: dict[str, int] = {}

    for article in articles:
        if display_limit and len(filtered) >= display_limit:
            break

        published_raw = article.get("published_at")
        if not published_raw:
            continue
        try:
            published = dt.datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if published < cutoff:
            continue

        source_name = article.get("source") or "Unknown source"
        source_key = normalize_source(source_name)
        if source_counts.get(source_key, 0) >= MAX_PER_SOURCE:
            continue

        article["_published_dt"] = published
        article["_content_text"] = resolve_content(article)
        filtered.append(article)
        source_counts[source_key] = source_counts.get(source_key, 0) + 1

    return filtered


def normalize_source(source: str) -> str:
    """Normalize the source name for counting constraints."""
    return source.strip().lower() if source and source.strip() else "unknown"


def resolve_content(article: dict) -> str:
    """Return the best-available article content, fetching from the URL if needed."""
    for field in ("content", "description", "snippet"):
        value = article.get(field)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                return cleaned

    link = article.get("url")
    if isinstance(link, str) and link:
        fetched = extract_text_from_url(link)
        if fetched:
            return fetched
    return ""


def extract_text_from_url(url: str) -> str:
    """Fetch text content from an article URL, returning a trimmed summary."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text" not in content_type:
                return ""
            charset = response.headers.get_content_charset() or "utf-8"
            raw_html = response.read(512_000).decode(charset, errors="replace")
    except (urllib.error.URLError, UnicodeDecodeError, ValueError):
        return ""

    paragraph_parser = ParagraphExtractor()
    paragraph_parser.feed(raw_html)
    paragraphs = paragraph_parser.get_paragraphs()
    if paragraphs:
        summary = "\n\n".join(paragraphs[:5])
        return summary[:1500].strip()

    fallback_parser = PlainTextExtractor()
    fallback_parser.feed(raw_html)
    text = fallback_parser.get_text()
    return text[:1500].strip()


class ParagraphExtractor(HTMLParser):
    """Collect paragraph text while skipping non-content sections."""

    SKIP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside", "form"}

    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._skip_depth = 0
        self._buffer: list[str] = []
        self._paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        tag_lower = tag.lower()
        if tag_lower in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag_lower == "p" and self._skip_depth == 0:
            self._capture = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        tag_lower = tag.lower()
        if tag_lower in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag_lower == "p" and self._capture:
            text = _normalize_whitespace("".join(self._buffer))
            if text:
                self._paragraphs.append(text)
            self._buffer = []
            self._capture = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._capture and self._skip_depth == 0:
            self._buffer.append(data)

    def get_paragraphs(self) -> list[str]:
        return self._paragraphs


class PlainTextExtractor(HTMLParser):
    """Fallback HTML parser that strips tags while skipping scripts/styles."""

    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        return _normalize_whitespace(" ".join(self._chunks))


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def render_html(articles: list[dict]) -> str:
    """Build the HTML document for the selected articles."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    items: list[str] = []
    for article in articles:
        title = html.escape(article.get("title") or "Untitled")
        link = html.escape(article.get("url") or "#")
        content_text = article.get("_content_text", "")
        if content_text:
            content_html = html.escape(content_text).replace("\n", "<br>")
        else:
            content_html = "No summary available."
        published_dt = article.get("_published_dt", dt.datetime.now(dt.timezone.utc))
        published_str = published_dt.strftime("%Y-%m-%d %H:%M UTC")
        source = html.escape(article.get("source") or "Unknown source")
        items.append(
            "\n        <article class=\"story\">\n"
            f"            <h2><a href=\"{link}\" target=\"_blank\" rel=\"noopener noreferrer\">{title}</a></h2>\n"
            f"            <p class=\"meta\">Published {published_str} · {source}</p>\n"
            f"            <p>{content_html}</p>\n"
            "        </article>"
        )
    articles_html = "\n".join(items) if items else "<p>No stories retrieved.</p>"
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <title>US News Digest</title>\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 900px; line-height: 1.6; }\n"
        "        h1 { text-align: center; }\n"
        "        .story { border-bottom: 1px solid #ddd; padding: 1.5rem 0; }\n"
        "        .story:last-of-type { border-bottom: none; }\n"
        "        .meta { color: #555; font-size: 0.9rem; }\n"
        "        a { color: #0b5ed7; text-decoration: none; }\n"
        "        a:hover { text-decoration: underline; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <h1>Latest US News (Past 24 Hours)</h1>\n"
        f"    <p class=\"meta\">Generated {now}</p>\n"
        f"    {articles_html}\n"
        "</body>\n"
        "</html>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a US news HTML digest from Mediastack.")
    parser.add_argument(
        "--key",
        dest="api_key",
        default=os.environ.get("MEDIASTACK_API_KEY"),
        help="Mediastack API key (defaults to MEDIASTACK_API_KEY env variable)",
    )
    parser.add_argument(
        "--output",
        default="us_news.html",
        help="Output HTML file path (default: us_news.html)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Maximum stories to include (capped at 30, default: 30)",
    )
    args = parser.parse_args()

    if not args.api_key:
        parser.error("Provide an API key via --key or the MEDIASTACK_API_KEY environment variable.")

    try:
        articles = fetch_articles(args.api_key, args.limit)
    except urllib.error.URLError as exc:  # type: ignore[attr-defined]
        sys.exit(f"Failed to reach Mediastack API: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"API response was not valid JSON: {exc}")

    html_doc = render_html(articles)
    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print(f"Wrote {len(articles)} stories to {output_path}")


if __name__ == "__main__":
    main()
