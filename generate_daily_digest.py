#!/usr/bin/env python3
"""Generate and email daily news digest from configured RSS sources."""

from __future__ import annotations

import argparse
import datetime as dt
import email.mime.multipart
import email.mime.text
import gzip
import html
import json
import pathlib
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from html.parser import HTMLParser
from typing import Any

from generate_us_news_page import ParagraphExtractor, PlainTextExtractor  # type: ignore
from db_utils import insert_article, extract_image_url  # type: ignore

CONFIG_FILE = pathlib.Path("config.json")

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
    """Strip tags from HTML snippets."""

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


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        print(f"✗ Config file not found: {CONFIG_FILE}", file=sys.stderr)
        print("Run setup_config.py to create configuration", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalise_text(value: str) -> str:
    """Normalize text encoding."""
    if not value:
        return ""
    result = html.unescape(value)
    for src, dst in ASCII_REPLACEMENTS.items():
        result = result.replace(src, dst)
    return result.replace("\r", "")


def fetch_url(url: str, max_bytes: int = 1_000_000, binary: bool = False) -> bytes | str:
    """Fetch URL with compression handling."""
    headers = BASE_HEADERS.copy()
    request = urllib.request.Request(url, headers=headers)
    try:
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
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise ValueError(f"Failed to fetch {url}: {e}") from e


def parse_pub_date(raw: str) -> dt.datetime | None:
    """Parse publication date string."""
    import email.utils

    try:
        dt_obj = email.utils.parsedate_to_datetime(raw)
        if dt_obj is None:
            return None
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
        return dt_obj
    except (TypeError, ValueError):
        return None


def is_within_hours(pub_date_str: str, hours: int) -> bool:
    """Check if publication date is within lookback hours."""
    pub_date = parse_pub_date(pub_date_str)
    if not pub_date:
        return True  # Include if we can't parse the date
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - pub_date
    return delta.total_seconds() <= hours * 3600


def fetch_rss_feed(url: str) -> list[dict[str, str]]:
    """Fetch and parse RSS feed."""
    try:
        xml_text = fetch_url(url, max_bytes=2_000_000)
    except ValueError as e:
        print(f"Warning: Could not fetch feed: {e}", file=sys.stderr)
        return []

    if not isinstance(xml_text, str):
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"Warning: Could not parse RSS feed: {e}", file=sys.stderr)
        return []

    items: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        title = normalise_text((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = normalise_text((item.findtext("description") or "").strip())

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description,
            }
        )

    return items


def extract_article_content(link: str, title: str) -> str:
    """Extract article content from link."""
    try:
        html_text = fetch_url(link, max_bytes=3_000_000)
    except ValueError as e:
        print(f"Warning: Could not fetch article: {e}", file=sys.stderr)
        return ""

    if not isinstance(html_text, str):
        return ""

    # Try ParagraphExtractor first
    parser = ParagraphExtractor()
    try:
        parser.feed(html_text)
        paragraphs = parser.get_paragraphs()
        if paragraphs:
            content = "\n\n".join(p.strip() for p in paragraphs if p.strip())
            if content:
                return normalise_text(content)
    except Exception as e:
        print(f"Warning: Parser error for {link}: {e}", file=sys.stderr)

    # Fallback to PlainTextExtractor
    try:
        fallback = PlainTextExtractor()
        fallback.feed(html_text)
        content = fallback.get_text()
        return normalise_text(content)
    except Exception as e:
        print(f"Warning: Fallback parser error for {link}: {e}", file=sys.stderr)
        return ""


def strip_snippet(snippet: str) -> str:
    """Strip HTML tags from snippet."""
    stripper = SnippetStripper()
    stripper.feed(snippet)
    return normalise_text(stripper.text())


def clean_pbs_content(content: str) -> str:
    """For PBS News articles, remove metadata and footer content but keep article body."""
    if not content:
        return content
    
    import re
    
    # Remove all author/AP attributions at the START only
    content = re.sub(r'^([A-Za-zá\s]+,\s*(?:Associated\s+Press|PolitiFact)\s*)+', '', content, flags=re.IGNORECASE)
    
    # Remove "Leave your feedback" text
    content = re.sub(r'Leave\s+your\s+feedback', '', content, flags=re.IGNORECASE)
    
    # Remove "This article originally appeared on..." lines
    content = re.sub(r'This\s+article\s+originally\s+appeared\s+on\s+[A-Za-z]+\.', '', content, flags=re.IGNORECASE)
    
    # Remove "Read More" sentence/links
    content = re.sub(r'\s*\[?Read\s+More\]?\s*', ' ', content, flags=re.IGNORECASE)
    
    # **CRITICAL FIX**: The article content is interrupted by newsletter promotions in the middle.
    # Remove ONLY the newsletter section that appears in the middle: "Subscribe to Here's the Deal..."
    # and "Linda Weavil..." text that follows it - but keep everything else
    content = re.sub(
        r'Subscribe\s+to\s+Here\'?s\s+the\s+Deal[^\n]*\n[^\n]*\n[^\n]*Linda\s+Weavil.*?(?=\n[A-Za-z])',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove "Support trusted journalism" footer at the very end
    content = re.sub(r'Support\s+trusted\s+journalism.*?$', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove the repeated author bylines at the end (after the article ends)
    # Match pattern: "Name, Associated Press" appearing 2+ times in a row
    content = re.sub(
        r'([A-Za-zá\s]+,\s*(?:Associated\s+Press|PolitiFact)\s*){2,}\s*$',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove leading punctuation and whitespace
    content = re.sub(r'^[\s.,\-()"""\s]*', '', content)
    
    # Normalize multiple spaces/newlines to single space
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()


def clean_techradar_content(content: str) -> str:
    """For TechRadar articles, remove promotional content and footer."""
    if not content:
        return content
    
    import re
    
    # Remove newsletter signup prompts
    content = re.sub(
        r'Sign\s+up\s+to\s+the\s+TechRadar\s+Pro\s+newsletter.*?(?=\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove "Follow TechRadar on Google News" and related social media promotions
    content = re.sub(
        r'Follow\s+TechRadar\s+on\s+Google\s+News.*?(?=\n\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove "And of course you can also follow TechRadar on TikTok" sections
    content = re.sub(
        r'And\s+of\s+course\s+you\s+can\s+also\s+follow\s+TechRadar.*?(?=\n\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove author bio sections that start with author names
    # Usually format: "Firstname has been writing about..." or similar
    content = re.sub(
        r'[A-Z][a-z]+\s+has\s+been\s+(?:writing|covering|reporting).*?(?=\n\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove comment section prompts
    content = re.sub(
        r'You\s+must\s+confirm\s+your\s+public\s+display\s+name.*?(?=\n\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    content = re.sub(
        r'Please\s+(?:logout|login|signup).*?(?=\n\n|$)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove generic footer text
    content = re.sub(r'Please\s+wait\.\.\.$', '', content, flags=re.IGNORECASE)
    
    # Normalize multiple spaces/newlines to single space
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()


def clean_sciencedaily_content(content: str) -> str:
    """For Science Daily articles, remove related articles section that appears at the end."""
    if not content:
        return content
    
    import re
    
    # Find where the main article ends
    # Science Daily includes related article links at the end after "Story Source:"
    # The structure is: [article content] [Story Source: ...] [Related articles list]
    
    # Remove the "Story Source:" line entirely
    story_source_match = re.search(r'Story\s+Source:[^\n]*', content, re.IGNORECASE)
    if story_source_match:
        # Remove everything from "Story Source:" onwards
        end_pos = story_source_match.start()
        content = content[:end_pos].rstrip()
    else:
        # If no "Story Source", look for common metadata markers
        cite_match = re.search(r'Cite\s+This\s+Page:[^\n]*', content, re.IGNORECASE)
        if cite_match:
            end_pos = cite_match.start()
            content = content[:end_pos].rstrip()
    
    # Remove trailing metadata/note lines
    content = re.sub(
        r'\s*Note:\s+Content\s+may\s+be\s+edited[^\n]*',
        '',
        content,
        flags=re.IGNORECASE
    )
    
    # Remove journal reference
    content = re.sub(
        r'\s*Journal\s+Reference:[^\n]*',
        '',
        content,
        flags=re.IGNORECASE
    )
    
    # Normalize multiple spaces/newlines to single space
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()


def get_top_articles(
    items: list[dict[str, str]], count: int, hours: int
) -> list[dict[str, str]]:
    """Get top N articles from the last N hours."""
    recent = [item for item in items if is_within_hours(item["pub_date"], hours)]
    return recent[:count]


def process_sources(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Process all configured RSS sources and insert into database."""
    sources = config.get("rss_sources", [])
    articles_per_source = config.get("digest_settings", {}).get("articles_per_source", 3)
    hours_lookback = config.get("digest_settings", {}).get("hours_lookback", 24)

    all_articles: list[dict[str, Any]] = []

    for source in sources:
        if not source.get("enabled"):
            continue

        print(f"Fetching: {source['name']}", file=sys.stderr)
        items = fetch_rss_feed(source["url"])
        
        # Get more items than needed to account for skipped audio/video content
        top_items = get_top_articles(items, articles_per_source * 3, hours_lookback)

        articles_added = 0
        for item in top_items:
            if articles_added >= articles_per_source:
                break
            
            snippet = strip_snippet(item.get("description", ""))
            pub_date = parse_pub_date(item.get("pub_date", ""))
            pub_date_iso = pub_date.isoformat() if pub_date else dt.datetime.now(dt.timezone.utc).isoformat()

            print(f"  Extracting: {item['title'][:50]}...", file=sys.stderr)
            content = extract_article_content(item["link"], item["title"])

            # Skip articles that are audio/video content
            if "watch the full episode" in content.lower():
                print(f"    Skipping (audio/video): {item['title'][:50]}...", file=sys.stderr)
                time.sleep(0.3)
                continue

            # Clean PBS News content by removing everything before "Read More"
            if "PBS" in source["name"]:
                content = clean_pbs_content(content)
            
            # Clean TechRadar content by removing promotional footers
            if "TechRadar" in source["name"]:
                content = clean_techradar_content(content)
            
            # Clean Science Daily content by removing related articles and metadata
            if "Science Daily" in source["name"]:
                content = clean_sciencedaily_content(content)

            # Extract first image URL from content
            image_url = None
            try:
                html_text = fetch_url(item["link"], max_bytes=3_000_000)
                if isinstance(html_text, str):
                    image_url = extract_image_url(html_text)
            except Exception:
                pass

            # Insert article into database
            # Create summary from snippet (first 500 chars for better preview)
            summary = snippet[:500] if snippet else ""
            
            article_id = insert_article(
                title=item["title"],
                date_iso=pub_date_iso,
                source=source["name"],
                link=item["link"],
                content=content or snippet,
                snippet=snippet,
                image_url=image_url,
                summary=summary,
            )

            if article_id:
                article = {
                    "id": article_id,
                    "source": source["name"],
                    "title": item["title"],
                    "link": item["link"],
                    "pub_date": pub_date_iso,
                    "snippet": snippet,
                }
                all_articles.append(article)
                articles_added += 1
                time.sleep(0.3)  # Be respectful to servers
            else:
                print(f"    Duplicate article (skipped): {item['title'][:50]}...", file=sys.stderr)

    return all_articles


def html_escape(value: str) -> str:
    """Escape HTML special characters."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html(articles: list[dict[str, Any]]) -> str:
    """Render articles as HTML."""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Group by source
    by_source: dict[str, list[dict[str, Any]]] = {}
    for article in articles:
        source = article["source"]
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(article)

    articles_html: list[str] = []
    for source in by_source:
        articles_html.append(
            f'    <section class="source-section">\n'
            f'        <h2 class="source-title">{html_escape(source)}</h2>'
        )
        for article in by_source[source]:
            title = html_escape(article["title"])
            link = html_escape(article["link"])
            pub_date = article["pub_date"]
            content_lines = [html_escape(line) for line in article.get("content", "").split("\n") if line.strip()]
            
            articles_html.append(
                f'        <article class="story">\n'
                f'            <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>\n'
                f'            <p class="meta">{pub_date}</p>\n'
                f'            <div class="content">\n'
            )
            for line in content_lines[:10]:  # Limit to first 10 lines
                articles_html.append(f'                <p>{line}</p>')
            articles_html.append('            </div>\n        </article>')
        articles_html.append('    </section>')

    html_doc = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "    <title>Daily News Digest</title>\n"
        "    <style>\n"
        "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 2rem; background: #f5f5f5; }\n"
        "        .container { max-width: 900px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n"
        "        header { text-align: center; margin-bottom: 2rem; border-bottom: 2px solid #007bff; padding-bottom: 1rem; }\n"
        "        header h1 { margin: 0; color: #333; }\n"
        "        header p { margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem; }\n"
        "        .source-section { margin: 2rem 0; }\n"
        "        .source-title { color: #007bff; margin-top: 2rem; margin-bottom: 1rem; border-left: 4px solid #007bff; padding-left: 1rem; }\n"
        "        .source-section:first-of-type .source-title { margin-top: 0; }\n"
        "        article.story { margin: 1.5rem 0; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; background: #fafafa; }\n"
        "        article.story h3 { margin: 0 0 0.5rem 0; }\n"
        "        article.story a { color: #007bff; text-decoration: none; }\n"
        "        article.story a:hover { text-decoration: underline; }\n"
        "        .meta { margin: 0 0 1rem 0; color: #666; font-size: 0.85rem; }\n"
        "        .content p { margin: 0.5rem 0; line-height: 1.6; color: #333; }\n"
        "        .content p:first-child { margin-top: 0; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <div class=\"container\">\n"
        "        <header>\n"
        "            <h1>Daily News Digest</h1>\n"
        f"            <p>Generated {html_escape(now)}</p>\n"
        "        </header>\n"
        + "\n".join(articles_html)
        + "\n    </div>\n</body>\n</html>\n"
    )
    return html_doc


def send_email(
    to_addresses: list[str],
    html_content: str,
    smtp_config: dict[str, Any],
) -> bool:
    """Send email with digest."""
    if not smtp_config.get("enabled"):
        print("SMTP is not enabled", file=sys.stderr)
        return False

    gmail_address = smtp_config.get("gmail_address")
    gmail_password = smtp_config.get("gmail_app_password")

    if not gmail_address or not gmail_password:
        print("SMTP credentials not configured", file=sys.stderr)
        return False

    try:
        print(f"Connecting to SMTP server...", file=sys.stderr)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(gmail_address, gmail_password)

        msg = email.mime.multipart.MIMEMultipart("alternative")
        msg["Subject"] = f"Daily News Digest - {dt.datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = gmail_address
        msg["To"] = ", ".join(to_addresses)

        html_part = email.mime.text.MIMEText(html_content, "html")
        msg.attach(html_part)

        print(f"Sending to {len(to_addresses)} recipient(s)...", file=sys.stderr)
        server.sendmail(gmail_address, to_addresses, msg.as_string())
        server.quit()

        print("✓ Email sent successfully", file=sys.stderr)
        return True

    except smtplib.SMTPAuthenticationError:
        print("✗ Authentication failed. Check email and app password.", file=sys.stderr)
        return False
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Failed to send email: {e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and email daily news digest.")
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send digest via email",
    )
    parser.add_argument(
        "--html-output",
        help="Override HTML output file",
    )
    parser.add_argument(
        "--json-output",
        help="Override JSON output file",
    )
    args = parser.parse_args()

    config = load_config()
    digest_settings = config.get("digest_settings", {})

    print("Generating daily digest...", file=sys.stderr)
    articles = process_sources(config)

    if not articles:
        print("No new articles found", file=sys.stderr)
        return

    print(f"Found {len(articles)} new articles", file=sys.stderr)

    # Generate HTML from database
    print("Generating HTML from database...", file=sys.stderr)
    import subprocess
    result = subprocess.run([sys.executable, "generate_html_from_db.py"], capture_output=True, text=True)
    print(result.stdout, file=sys.stderr)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)

    # Send email if requested
    if args.send_email:
        recipients = config.get("recipients", [])
        if recipients:
            html_output = digest_settings.get("output_html", "daily_digest.html")
            try:
                with open(html_output, "r", encoding="utf-8") as f:
                    html_content = f.read()
                send_email(recipients, html_content, config.get("smtp", {}))
            except Exception as e:
                print(f"Error sending email: {e}", file=sys.stderr)
        else:
            print("No email recipients configured", file=sys.stderr)


if __name__ == "__main__":
    main()
