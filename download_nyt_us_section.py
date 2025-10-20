#!/usr/bin/env python3
"""Download titles, links, and full text for the NYTimes U.S. section."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from generate_us_news_page import ParagraphExtractor, PlainTextExtractor  # type: ignore

BASE_URL = "https://www.nytimes.com/section/us"
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
MAX_SECTION_HTML = 1_200_000
MAX_ARTICLE_HTML = 600_000
FETCH_DELAY = 0.75


def build_section_url(page: int) -> str:
    if page <= 1:
        return BASE_URL
    return f"{BASE_URL}?{urllib.parse.urlencode({'page': page})}"


def normalize_link(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = "https://www.nytimes.com" + href
    if not href.startswith("https://www.nytimes.com"):
        return None
    if href.startswith("https://www.nytimes.com/by/"):
        return None
    if href.startswith("https://www.nytimes.com/spotlight/"):
        return None
    if href.startswith("https://www.nytimes.com/section/") and "/" not in href.rstrip("/")[len("https://www.nytimes.com/section/") :]:
        return None
    return href.split("#", 1)[0]


class SectionArticleParser(HTMLParser):
    """Collect article links and titles from the section landing page."""

    def __init__(self) -> None:
        super().__init__()
        self._in_article = False
        self._current: dict[str, str | None] | None = None
        self._title_parts: list[str] = []
        self._capture_title = False
        self._anchor_stack: list[str | None] = []
        self.articles: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        tag_lower = tag.lower()
        if tag_lower == "article":
            self._in_article = True
            self._current = {"title": None, "url": None}
        elif self._in_article and tag_lower == "a":
            attr_map = {key.lower(): value for key, value in attrs}
            url = normalize_link(attr_map.get("href"))
            self._anchor_stack.append(url)
        elif self._in_article and tag_lower == "h3":
            self._capture_title = True
            self._title_parts = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        tag_lower = tag.lower()
        if tag_lower == "article":
            if self._current and self._current.get("title") and self._current.get("url"):
                self.articles.append({
                    "title": self._current["title"] or "",
                    "url": self._current["url"] or "",
                })
            self._in_article = False
            self._current = None
        elif self._in_article and tag_lower == "h3":
            self._capture_title = False
            title = "".join(self._title_parts).strip()
            if title and self._current and not self._current.get("title"):
                self._current["title"] = " ".join(title.split())
            self._title_parts = []
        elif self._in_article and tag_lower == "a":
            url = self._anchor_stack.pop() if self._anchor_stack else None
            if self._current and not self._current.get("url") and url:
                self._current["url"] = url

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._capture_title and self._in_article:
            self._title_parts.append(data)


def fetch_url(url: str, max_bytes: int, referer: str | None = None) -> str:
    headers = BASE_HEADERS.copy()
    headers.setdefault("Referer", referer or BASE_URL)
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text" not in content_type:
            raise ValueError(f"Unexpected content type for {url}: {content_type}")
        charset = response.headers.get_content_charset() or "utf-8"
        raw = response.read(max_bytes)
    return raw.decode(charset, errors="replace")


def extract_article_text(url: str) -> str:
    try:
        html = fetch_url(url, MAX_ARTICLE_HTML)
    except (urllib.error.URLError, ValueError):  # type: ignore[attr-defined]
        return ""

    paragraph_parser = ParagraphExtractor()
    paragraph_parser.feed(html)
    paragraphs = paragraph_parser.get_paragraphs()
    if paragraphs:
        return "\n\n".join(paragraphs)

    fallback_parser = PlainTextExtractor()
    fallback_parser.feed(html)
    return fallback_parser.get_text()


def deduplicate_articles(articles: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for article in articles:
        url = article.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(article)
    return unique


def render_html(articles: list[dict[str, str]]) -> str:
    rows = []
    for entry in articles:
        title = entry.get("title", "Untitled")
        url = entry.get("url", "#")
        body = entry.get("content", "")
        safe_title = html_escape(title)
        safe_url = html_escape(url)
        safe_body = html_escape(body).replace("\n", "<br>\n")
        rows.append(
            "        <article class=\"story\">\n"
            f"            <h2><a href=\"{safe_url}\">{safe_title}</a></h2>\n"
            f"            <p>{safe_body}</p>\n"
            "        </article>"
        )
    stories = "\n".join(rows) if rows else "        <p>No stories were captured.</p>"
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <title>NYTimes U.S. Section</title>\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 900px; line-height: 1.6; }\n"
        "        .story { border-bottom: 1px solid #ddd; padding: 1.5rem 0; }\n"
        "        .story:last-of-type { border-bottom: none; }\n"
        "        h2 { margin-bottom: 0.5rem; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <h1>NYTimes U.S. Section</h1>\n"
        f"    {stories}\n"
        "</body>\n"
        "</html>\n"
    )


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download NYTimes U.S. section stories.")
    parser.add_argument("--page", type=int, default=2, help="Section page number (default: 2)")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of articles to fetch")
    parser.add_argument(
        "--json-output",
        default="nyt_us_section.json",
        help="Output JSON path (default: nyt_us_section.json)",
    )
    parser.add_argument(
        "--html-output",
        default="",
        help="Optional HTML output path",
    )
    args = parser.parse_args()

    section_url = build_section_url(args.page)
    try:
        section_html = fetch_url(section_url, MAX_SECTION_HTML)
    except (urllib.error.URLError, ValueError) as exc:  # type: ignore[attr-defined]
        sys.exit(f"Failed to download section page: {exc}")

    parser = SectionArticleParser()
    parser.feed(section_html)
    collected = deduplicate_articles(parser.articles)

    if args.limit > 0:
        collected = collected[: args.limit]

    results: list[dict[str, str]] = []
    for index, article in enumerate(collected, start=1):
        time.sleep(FETCH_DELAY)
        content = extract_article_text(article["url"])
        results.append({
            "title": article["title"],
            "url": article["url"],
            "content": content,
        })
        print(f"[{index}/{len(collected)}] {article['title']}", flush=True)

    with open(args.json_output, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} stories to {args.json_output}")

    if args.html_output:
        html_doc = render_html(results)
        with open(args.html_output, "w", encoding="utf-8") as fh:
            fh.write(html_doc)
        print(f"Wrote HTML output to {args.html_output}")


if __name__ == "__main__":
    main()
