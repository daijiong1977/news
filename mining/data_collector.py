#!/usr/bin/env python3
"""
Data Collector - RSS Feed Crawler
Collects articles from various RSS feeds stored in the database and stores them in articles table.
Maps sources to categories automatically from feeds table.
"""

import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
import pathlib
from html.parser import HTMLParser
import time

DB_FILE = pathlib.Path(__file__).parent.parent / "articles.db"
import json
CONFIG_PATH = pathlib.Path(__file__).parent / 'thresholds.json'
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as _f:
        THRESHOLDS = json.load(_f)
except Exception:
    # Fallback defaults if config not available
    THRESHOLDS = {
        'paragraph_min_length': 30,
        'cleaned_chars_min_global': 2300,
        'cleaned_chars_max_global': 4500,
        'sport_strict_min_chars': 1500,
        'sport_relaxed_min_chars': 1200,
        'collect_preview_min_image_bytes': 100000,
        'batch_min_image_bytes': 70000,
        'quick_min_image_bytes': 2000,
        'per_feed_timeout': 240,
        'num_per_source': 5,
    }


class ParagraphExtractor(HTMLParser):
    """Extract paragraphs from HTML."""
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current_p = []
        self.in_p = False
        self.in_script = False
        self.in_style = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True
        elif tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True
    
    def handle_endtag(self, tag):
        if tag == 'p' and self.in_p:
            text = ''.join(self.current_p).strip()
            if text and len(text) > 10:  # Skip very short text
                self.paragraphs.append(text)
            self.current_p = []
            self.in_p = False
        elif tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
    
    def handle_data(self, data):
        if self.in_p and not self.in_script and not self.in_style:
            self.current_p.append(data)
    
    def get_paragraphs(self):
        return self.paragraphs


def _choose_best_from_srcset(srcset):
    """Pick the best (largest) URL from a srcset string.
    srcset examples: 'a.jpg 100w, b.jpg 800w' or 'a.jpg 1x, b.jpg 2x'.
    Return the URL (first part) of the entry with the largest width or density.
    """
    if not srcset:
        return None
    parts = [p.strip() for p in srcset.split(',') if p.strip()]
    best_url = None
    best_val = -1.0
    for part in parts:
        # Split into URL and descriptor
        segs = part.split()
        url = segs[0]
        val = 0.0
        if len(segs) > 1:
            desc = segs[1]
            # handle width like '800w' or density like '2x'
            try:
                if desc.endswith('w'):
                    val = float(desc[:-1])
                elif desc.endswith('x'):
                    val = float(desc[:-1]) * 1000.0  # treat density as very large to prefer hi-res
                else:
                    val = float(desc)
            except Exception:
                val = 0.0
        else:
            # no descriptor: treat as default small
            val = 0.0
        if val > best_val:
            best_val = val
            best_url = url
    return best_url


def _score_image_candidate(img_url, article_url):
    """Return a score for an image candidate to prefer large/original media-host images.
    Heuristics:
      - prefer known media hosts (ichef.bbci.co.uk, bbci.co.uk)
      - prefer URLs with '/standard/<width>/' or '/branded_sport/<width>/' and larger widths
      - prefer same-origin images (domain contains article domain)
    """
    from urllib.parse import urlparse
    import re

    score = 0.0
    if not img_url:
        return score
    try:
        p = urlparse(img_url)
        host = p.netloc or ''
        path = p.path or ''
    except Exception:
        return score

    # known media hosts
    if 'ichef.bbci.co.uk' in host or 'bbci.co.uk' in host:
        score += 10000.0

    # prefer same-origin (bbc.com article vs bbc image)
    try:
        art_host = urlparse(article_url).netloc or ''
        if art_host and art_host in host:
            score += 2000.0
    except Exception:
        pass

    # parse width from typical BBC patterns
    m = re.search(r'/standard/(\d+)', path)
    if not m:
        m = re.search(r'/branded_sport/(\d+)', path)
    if m:
        try:
            w = float(m.group(1))
            score += w  # add width directly
        except Exception:
            pass

    # prefer webp/jpg over png placeholders
    if path.endswith('.webp'):
        score += 50.0
    if path.endswith('.jpg') or path.endswith('.jpeg'):
        score += 30.0

    # small penalty for things that look like logos
    low = (host + path).lower()
    if any(x in low for x in ('logo', 'favicon', 'apple-touch-icon', '/icons/', 'placeholder', 'spacer', 'blank')):
        score -= 5000.0

    return score


def clean_paragraphs(paragraphs):
    """Clean and filter paragraphs - remove bylines, feedback prompts, etc."""
    import html
    import re
    
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
    
    # Common byline patterns to detect (names that appear in PBS articles)
    BYLINE_NAMES = {
        'Nick Schifrin', 'Sonia Kopelev', 'Geoff Bennett', 'Amna Nawaz',
        'Stephanie Kotuby', 'Alexa Gold', 'Jonah Anderson', 'Ismael M. Belkoura',
        'Amalia Hout-Marchand', 'Leonardo Pini', 'Athan Yanos',
    }
    
    cleaned = []
    for raw in paragraphs:
        # Unescape HTML entities
        text = html.unescape(raw.strip())
        for src, dst in ASCII_REPLACEMENTS.items():
            text = text.replace(src, dst)
        text = text.replace("\r", "")
        
        if not text:
            continue
        
        # Check for byline patterns: repeated names or name:
        # Pattern 1: "Name Name" (duplicated name)
        stripped = text.strip()
        parts = stripped.split()
        if len(parts) == 2 and parts[0] == parts[1]:
            # Likely "Nick Schifrin Nick Schifrin" - skip it
            continue
        
        # Pattern 2: Direct byline name match
        if stripped in BYLINE_NAMES:
            continue
        
        # Pattern 3: Name with colon (e.g., "Nick Schifrin:")
        if len(parts) <= 3 and stripped.endswith(':'):
            name_part = stripped[:-1].strip()
            if name_part in BYLINE_NAMES:
                continue
        
        # Skip all-caps short text (like bylines)
        upper_count = sum(1 for ch in text if ch.isupper())
        lower_count = sum(1 for ch in text if ch.islower())
        if upper_count and not lower_count and len(text.split()) <= 6:
            continue
        
        # Skip short capitalized phrases (2-3 words, all caps) - generic byline pattern
        if len(parts) <= 3 and all(w[0].isupper() for w in parts if len(w) > 0):
            # If very short and all proper case, likely a byline
            if len(parts) <= 2 and len(text) < 40:
                continue
        
        # Skip feedback prompts
        if text.lower() == "leave your feedback":
            continue
        
        # Skip prefixes
        if any(text.startswith(prefix) for prefix in TRIM_PREFIXES):
            continue
        
        # Skip certain phrases
        if any(needle in text for needle in TRIM_CONTAINS):
            continue

        # Remove TechRadar/Engagement boilerplate often found at the end
        if text.startswith('You must confirm your public display name'):
            continue
        if text.startswith('Follow TechRadar') or 'Follow TechRadar' in text:
            continue

        # Remove funding statements like "Funding: ..." appearing as standalone paragraphs
        if text.startswith('Funding:') or text.startswith('Funding –'):
            continue

        # Remove common advertisement/comment boilerplate
        AD_REMOVE_CONTAINS = (
            'techradar',
            'sign up for',
            'sign up',
            'sign in',
            'log in',
            'login',
            'log out',
            'logout',
            'read our full guide',
                'you must confirm your public display name',
                'follow techradar',
                'vpn',
                'nordvpn',
                'sponsored',
                'affiliate',
                'affiliate commission',
                'buy now',
                'get the world',
        )
        low_text = text.lower()

        # Aggressive promo/emoji filtering
        # If the paragraph starts with common promo emojis and is short, drop it
        promo_emojis_start = ('✅', '🔒', '🔥', '⭐', '✨', '💥', '🚨', '🎉')
        if text.lstrip().startswith(promo_emojis_start) and len(text) < 220:
            continue

        # Remove lines that are mostly non-alphanumeric/emoji bullets or extremely short promo snippets
        if len(text) < 120 and re.match(r'^[\W_\s\p{So}\p{Cn}]+$', text) if False else False:
            # fallback: if it contains an emoji and is short, drop it
            if any(ch in text for ch in promo_emojis_start):
                continue

        # Remove explicit percent-off or sale lines when short / clearly promotional
        if ('%' in text or ' off' in low_text or '70% off' in low_text or 'save' in low_text or 'discount' in low_text):
            # drop short promotional lines or emoji-marked offers
            if len(text) < 220 or any(ch in text for ch in promo_emojis_start):
                continue

        # Remove obvious subscription/payment promotional lines
        if re.search(r'\b(subscription|subscribe|monthly|per month|per year|set you back|add to your TV package|\$\d|£\d|AU\$|CAN\$|\d+% off)\b', low_text):
            if len(text) < 300:
                continue

        # Remove common advertisement/comment boilerplate
        if any(k in low_text for k in AD_REMOVE_CONTAINS):
            continue

        # Remove paragraph-level 'Related:' markers often appended to feed summaries
        if stripped.lower().startswith('related:'):
            continue
        
        # Skip if less than paragraph_min_length (too short to be real content)
        if len(text) < THRESHOLDS.get('paragraph_min_length', 30):
            continue
        
        # Skip duplicates
        if cleaned and text == cleaned[-1]:
            continue

        # Remove sentences that mention specific source tokens (e.g., 'bbc', 'ars technica')
        # This helps drop publisher-credit sentences that sometimes appear inside content.
        SOURCE_TOKENS = [
            'bbc', 'ars technica', 'the street', 'science daily', 'techradar', 'pbs',
            'new york times', 'nyt'
        ]
        # Split into sentences (simple heuristic: split on sentence-ending punctuation)
        parts = re.split(r'(?<=[\.\?!])\s+', text)
        kept_parts = []
        low_tokens = [t.lower() for t in SOURCE_TOKENS]
        for part in parts:
            lp = part.lower()
            # If any source token appears in the sentence, drop this sentence
            if any(tok in lp for tok in low_tokens):
                continue
            kept_parts.append(part)

        # Rejoin kept sentences; if nothing remains, skip this paragraph
        if not kept_parts:
            continue
        text = ' '.join(kept_parts).strip()

        cleaned.append(text)
    
    # Post-processing: strip trailing footer lines that look like publisher addresses or copyright
    while cleaned:
        last = cleaned[-1]
        low_last = last.lower()
        # remove if contains copyright sign or publisher address hints or 'future us'
        if '©' in last or 'future us' in low_last or re.search(r'\b\d{5}\b', low_last) or 'full' in low_last and 'floor' in low_last:
            cleaned.pop()
            continue
        # also remove short lines that contain commas and numbers like addresses
        if len(last.split()) < 10 and re.search(r'\d', last) and ',' in last:
            cleaned.pop()
            continue
        break

    return cleaned


def fetch_article_content(url):
    """Fetch full article content from URL and extract text."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Extract paragraphs
        parser = ParagraphExtractor()
        parser.feed(response.text)
        raw_paragraphs = parser.get_paragraphs()
        
        # Clean whitespace from all paragraphs first
        import re
        cleaned_raw = []
        for p in raw_paragraphs:
            # Normalize whitespace
            clean_p = re.sub(r'\s+', ' ', p.strip())
            if clean_p:
                cleaned_raw.append(clean_p)
        
        # Find the start of actual content by looking for substantial paragraphs
        # Skip the first few paragraphs which are usually bylines/presenter names
        content_start = 0
        for i, p in enumerate(cleaned_raw):
            # Skip very short paragraphs (< 50 chars) - these are usually bylines
            if len(p) > 50:
                content_start = i
                break
        
        # Use paragraphs starting from content_start
        filtered_paragraphs = cleaned_raw[content_start:]
        
        # Clean and filter paragraphs
        paragraphs = clean_paragraphs(filtered_paragraphs)
        
        if paragraphs:
            content = "\n\n".join(paragraphs[:15])  # Take first 15 paragraphs
            return content[:5000]  # Limit to 5000 chars
        else:
            return ""
    except Exception as e:
        return ""


def get_feeds_from_db(conn):
    """Query all enabled feeds from database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.feed_id, f.feed_name, f.feed_url, f.category_id, c.category_name
        FROM feeds f
        JOIN categories c ON f.category_id = c.category_id
        WHERE f.enable = 1
        ORDER BY f.feed_name
    """)
    return cursor.fetchall()


def is_video_article(title, description, url):
    """Check if article is a video/show/segment (should be skipped).
    Only skip if it's clearly about watching/viewing video content."""
    # Only skip if explicitly marked as video content to watch
    video_keywords = [
        'watch:', 'video:', 'segment -',
        'pbs newshour episode', 'full episode',
        'video episode'
    ]
    
    combined = f"{title} {description} {url}".lower()
    
    for keyword in video_keywords:
        if keyword in combined:
            return True
    
    return False


def is_transcript_article(content, title=""):
    """Check if article is a transcript-style piece (mixed speaker names and dialogue).
    These are hard to clean and should be skipped for now."""
    if not content:
        return False
    
    content_lower = content.lower()
    title_lower = title.lower() if title else ""
    
    # EXPLICIT FILTERS: Skip if contains both "transcript" AND "audio"
    # These are clearly transcript/audio content, not news articles
    has_transcript = 'transcript' in content_lower or 'transcript' in title_lower
    has_audio = 'audio' in content_lower or 'audio' in title_lower
    
    if has_transcript and has_audio:
        return True
    
    # Also skip if just "transcript" appears prominently in title
    if 'transcript' in title_lower:
        return True
    
    # INTERVIEW DETECTION: "joins us" or "joins tonight" + speaker name patterns
    # These indicate interview-format articles, not news
    has_joins_phrase = ('joins us' in content_lower or 'joins tonight' in content_lower)
    
    # Check for speaker name patterns like "Name, Title:" or "Name:"
    import re
    speaker_pattern = r'^[A-Z][a-z\s\-\']+(?:,\s+[A-Z][a-z\s\-\.]+)?:\s*\w'
    speaker_lines = len([line for line in content.split('\n') if re.match(speaker_pattern, line)])
    
    # If has "joins us/tonight" + multiple speaker lines, it's an interview
    if has_joins_phrase and speaker_lines >= 2:
        return True
    
    # Strong transcript indicators - these strongly suggest it's a transcript
    strong_indicators = [
        'has the details.',
        'reports:',
        'tells the story.',
        'the full story.',
        'tells us more.',
        'has more.',
        'has this report.',
        'reports more.',
        'has our report.',
    ]
    
    # Speaker/dialogue markers - mixed throughout content
    dialogue_indicators = [
        'speaker:',
        'interviewer:',
        'voice-over:',
        'correspondent:',
        ': [',  # Format like: "Speaker: [quote]"
        ':" ',  # Format like speaker: "quote
    ]
    
    # Pattern: repeated "Name: quote" or "Name says" patterns (transcript style)
    interview_patterns = [
        'tells us',
        'tells the',
        'explains that',
        'argues that',
        'argues the',
        'contends that',
        'contends the',
        'warns that',
        'warns the',
    ]
    
    # Count indicators
    strong_count = sum(1 for indicator in strong_indicators if indicator in content_lower)
    dialogue_count = sum(1 for indicator in dialogue_indicators if indicator in content_lower)
    interview_count = sum(1 for pattern in interview_patterns if pattern in content_lower)
    
    # If strong indicators found, it's a transcript
    if strong_count >= 1:
        return True
    
    # If multiple dialogue patterns, it's likely a transcript
    if dialogue_count >= 2:
        return True
    
    # If multiple interview patterns mixed with other markers, it's a transcript
    if interview_count >= 3:
        return True
    
    # If combination of dialogue and interview patterns, it's a transcript
    if dialogue_count >= 1 and interview_count >= 2:
        return True
    
    return False


def is_games_or_filler_article(title, description, content):
    """Check if article is games/puzzles/filler content (should be skipped)."""
    combined = f"{title} {description} {content}".lower()
    
    # Games/puzzle keywords to filter out
    games_keywords = [
        'hints and answers',
        'game #',
        'puzzle',
        'wordle',
        'connections',
        'strands',
        'how to watch',
        'champions league',
    ]
    
    for keyword in games_keywords:
        if keyword in combined:
            return True
    
    return False


def article_exists(conn, url):
    """Check if article already exists by URL."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
    return cursor.fetchone() is not None


def generate_article_id(conn):
    """Generate article ID in format: yearmonthday + 2-digit counter.
    
    Examples:
    - 2025102401 (Oct 24, 2025, article 1)
    - 2025102402 (Oct 24, 2025, article 2)
    - 2025102501 (Oct 25, 2025, article 1)
    
    Returns: String ID like '2025102401'
    """
    today = datetime.now().strftime("%Y%m%d")
    cursor = conn.cursor()
    
    # Count articles for today
    cursor.execute("SELECT COUNT(*) FROM articles WHERE id LIKE ?", (f"{today}%",))
    count = cursor.fetchone()[0]
    
    # Generate next ID: today's date + 2-digit counter (01-99)
    next_number = count + 1
    if next_number > 99:
        raise ValueError(f"ERROR: Already {next_number-1} articles for today {today}, max is 99 per day")
    
    article_id = f"{today}{next_number:02d}"
    return article_id


def insert_article(conn, title, source, url, description, content, pub_date, category_id):
    """Insert article into database."""
    cursor = conn.cursor()
    
    try:
        # Generate article ID (format: yearmonthday + 2-digit counter)
        article_id = generate_article_id(conn)
        
        # Ensure title is unescaped and trimmed
        import html as _html
        safe_title = _html.unescape(title).strip() if title else ""

        cursor.execute("""
            INSERT INTO articles 
            (id, title, source, url, description, content, pub_date, crawled_at, category_id, deepseek_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            article_id,
            safe_title[:500] if safe_title else "",
            source[:100] if source else "",
            url[:500] if url else "",
            description[:1000] if description else "",
            content[:5000] if content else "",
            pub_date[:50] if pub_date else datetime.now().isoformat(),
            datetime.now().isoformat(),
            category_id
        ))
        conn.commit()
        return article_id
    except sqlite3.IntegrityError as e:
        print(f"  ✗ Duplicate URL or constraint error: {e}")
        return None


def download_and_record_image(conn, article_id, article_url, html_text):
    """Find first relevant image, download it, save locally under website/article_image/, and record in DB."""
    from bs4 import BeautifulSoup
    import os
    if not html_text:
        return None

    soup = BeautifulSoup(html_text, 'html.parser')
    # 1) Prefer OpenGraph / Twitter meta images
    meta_img = None
    og = soup.find('meta', property='og:image')
    if og and og.get('content'):
        meta_img = og.get('content')
    if not meta_img:
        tw = soup.find('meta', attrs={'name': 'twitter:image'})
        if tw and tw.get('content'):
            meta_img = tw.get('content')
    if not meta_img:
        link_img = soup.find('link', rel=lambda x: x and 'image_src' in x)
        if link_img and link_img.get('href'):
            meta_img = link_img.get('href')

    candidates = []
    if meta_img:
        candidates.append(meta_img)

    # 2) Collect candidate images from common containers and attributes (src, data-src, srcset)
    # include <picture> and <source> elements and choose best from srcset where present
    for pic in soup.find_all('picture'):
        # look for <source> entries first
        for src in pic.find_all('source'):
            # check srcset preferentially
            sset = src.get('srcset') or src.get('data-srcset')
            best = _choose_best_from_srcset(sset) if sset else None
            if best:
                candidates.append(best)
            elif src.get('src'):
                candidates.append(src.get('src'))
        # then any img inside picture
        img = pic.find('img')
        if img:
            sset = img.get('srcset') or img.get('data-srcset')
            if sset:
                best = _choose_best_from_srcset(sset)
                if best:
                    candidates.append(best)
            src = img.get('src') or img.get('data-src')
            if src:
                candidates.append(src)

    selectors = ['article img', 'div.article img', 'div.main img', 'figure img', 'img']
    for sel in selectors:
        for img in soup.select(sel):
            # prefer srcset/density
            sset = img.get('srcset') or img.get('data-srcset') or img.get('data-srcset')
            if sset:
                best = _choose_best_from_srcset(sset)
                if best:
                    candidates.append(best)
                    continue
            src = img.get('src') or img.get('data-src') or img.get('data-srcset')
            if src:
                candidates.append(src)

    # Normalize and filter candidates
    norm = []
    for c in candidates:
        if not c:
            continue
        full = urljoin(article_url, c)
        # skip obvious logos/favicons or tiny placeholders
        low = full.lower()
        if any(x in low for x in ('favicon', 'apple-touch-icon', '/icons/')):
            continue
        # skip if filename indicates placeholder or logo
        if any(x in low for x in ('logo', 'pbs-logo', 'placeholder', 'spacer', 'blank')):
            continue
        # skip png files (often logos/placeholders). prefer jpg/webp
        from urllib.parse import urlparse
        path = urlparse(full).path.lower()
        if path.endswith('.png'):
            continue
        if full in norm:
            continue
        norm.append(full)

    if not norm:
        return None

    # Try candidates in collected order (meta -> srcset -> selectors) and accept
    # the first valid image. Avoid relying on large-size heuristics which can
    # select the wrong asset; prefer explicit meta and src/srcset ordering.
    img_url = None
    img_bytes = None
    for cand in norm:
        try:
            resp = requests.get(cand, timeout=10, stream=True)
            resp.raise_for_status()
            ctype = resp.headers.get('content-type','').lower()
            # Skip png responses (often logos/placeholders delivered as png)
            if 'image/png' in ctype:
                resp.close()
                continue
            data = resp.content
            # tiny images are likely icons/placeholders; require minimal bytes
            min_bytes_gate = THRESHOLDS.get('quick_min_image_bytes', 2000)
            if not data or len(data) < min_bytes_gate:
                continue
            img_url = cand
            img_bytes = data
            break
        except Exception:
            continue

    # Save image file to website/article_image directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images_dir = os.path.join(base_dir, 'website', 'article_image')
    os.makedirs(images_dir, exist_ok=True)
    # Create a safe filename
    import hashlib
    h = hashlib.sha1(img_url.encode('utf-8')).hexdigest()[:12]
    ext = os.path.splitext(img_url)[1].split('?')[0]
    if not ext or len(ext) > 6:
        ext = '.jpg'
    fname = f'article_{article_id}_{h}{ext}'
    local_path = os.path.join(images_dir, fname)
    try:
        with open(local_path, 'wb') as f:
            f.write(img_bytes)
    except Exception:
        return None

    # Insert into article_images table
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO article_images (article_id, image_name, original_url, local_location, small_location) VALUES (?, ?, ?, ?, ?)",
            (article_id, fname, img_url, local_path, None)  # small_location populated by imgcompress.py
        )
        conn.commit()
        
        # Get the image_id that was just created
        image_id = cur.lastrowid
        
        # Update articles table to link to this image
        try:
            cur.execute(
                "UPDATE articles SET image_id = ? WHERE id = ?",
                (image_id, article_id)
            )
            conn.commit()
        except Exception as e:
            pass  # Image recorded but not linked - not fatal
        
        return local_path
    except Exception:
        return None


def download_image_preview(article_url, html_text, min_bytes=100_000):
    """Download best image candidate for preview only. Return local path or None.
    Requires image size >= min_bytes to accept.
    Does not touch the database."""
    from bs4 import BeautifulSoup
    import os, hashlib

    if not html_text:
        return None
    soup = BeautifulSoup(html_text, 'html.parser')

    # Prefer og:image/twitter:image
    candidates = []
    og = soup.find('meta', property='og:image')
    if og and og.get('content'):
        candidates.append(og.get('content'))
    tw = soup.find('meta', attrs={'name': 'twitter:image'})
    if tw and tw.get('content'):
        candidates.append(tw.get('content'))

    # Include picture/source and choose best srcset entries
    for pic in soup.find_all('picture'):
        for src in pic.find_all('source'):
            sset = src.get('srcset') or src.get('data-srcset')
            best = _choose_best_from_srcset(sset) if sset else None
            if best:
                candidates.append(best)
            elif src.get('src'):
                candidates.append(src.get('src'))
        img = pic.find('img')
        if img:
            sset = img.get('srcset') or img.get('data-srcset')
            if sset:
                best = _choose_best_from_srcset(sset)
                if best:
                    candidates.append(best)
            src = img.get('src') or img.get('data-src')
            if src:
                candidates.append(src)

    # gather images from common selectors
    for sel in ['article img', 'div.article img', 'div.main img', 'figure img', 'img']:
        for img in soup.select(sel):
            sset = img.get('srcset') or img.get('data-srcset')
            if sset:
                best = _choose_best_from_srcset(sset)
                if best:
                    candidates.append(best)
                    continue
            src = img.get('src') or img.get('data-src') or img.get('data-srcset')
            if src:
                # if multiple comma-separated, pick the first URL
                if ',' in src:
                    src = src.split(',')[0].split()[0]
                candidates.append(src)

    # normalize
    norm = []
    for c in candidates:
        if not c:
            continue
        full = urljoin(article_url, c)
        low = full.lower()
        # skip obvious logos/favicons/placeholder
        if any(x in low for x in ('favicon', 'apple-touch-icon', '/icons/')):
            continue
        if any(x in low for x in ('logo', 'pbs-logo', 'placeholder', 'spacer', 'blank')):
            continue
        # skip png files (often logos/placeholders). prefer jpg/webp
        from urllib.parse import urlparse
        path = urlparse(full).path.lower()
        if path.endswith('.png'):
            continue
        if full not in norm:
            norm.append(full)

    if not norm:
        return None

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images_dir = os.path.join(base_dir, 'website', 'article_image')
    os.makedirs(images_dir, exist_ok=True)
    from urllib.parse import urlparse

    # Determine effective minimum bytes: prefer explicit param, else config
    effective_min = min_bytes if min_bytes is not None else THRESHOLDS.get('collect_preview_min_image_bytes', 100000)

    # Try candidates in collected order and accept first valid one
    for cand in norm:
        try:
            r = requests.get(cand, timeout=10)
            r.raise_for_status()
            ctype = r.headers.get('content-type','').lower()
            if 'image/png' in ctype:
                continue
            data = r.content
            # Require at least the effective minimum bytes
            if not data or len(data) < effective_min:
                continue
            from urllib.parse import urlparse
            ext = os.path.splitext(urlparse(cand).path)[1]
            if not ext or len(ext) > 6:
                ext = '.jpg'
            h = hashlib.sha1(cand.encode('utf-8')).hexdigest()[:12]
            fname = f'preview_{h}{ext}'
            local_path = os.path.join(images_dir, fname)
            with open(local_path, 'wb') as f:
                f.write(data)
            return local_path
        except Exception:
            continue
    return None


def collect_preview(num_per_source=None, min_image_bytes=None, per_feed_timeout=None, max_articles=20, enable_all_feeds=False, feeds_override=None):
    """Collect articles but only download images for preview. Do NOT insert into DB.
    Produces a preview HTML file `preview_articles.html` showing accepted articles and local image paths.
    An article is accepted only if a qualifying image (>= min_image_bytes) is found and content passes cleaning.
    """
    # Apply defaults from THRESHOLDS if not provided
    if num_per_source is None:
        num_per_source = THRESHOLDS.get('num_per_source', 5)
    if min_image_bytes is None:
        min_image_bytes = THRESHOLDS.get('collect_preview_min_image_bytes', 100000)
    if per_feed_timeout is None:
        per_feed_timeout = THRESHOLDS.get('per_feed_timeout', 240)

    # If requested, temporarily enable all feeds for this run and restore later
    conn = None
    restore_flags = None
    import os, json
    try:
        if feeds_override is not None:
            feeds = feeds_override
            conn = None
        else:
            if not DB_FILE.exists():
                print(f"Warning: database {DB_FILE} not found — running with no feeds")
                feeds = []
                conn = None
            else:
                conn = sqlite3.connect(DB_FILE)
                if enable_all_feeds:
                    try:
                        cur = conn.cursor()
                        cur.execute('SELECT feed_id, enable FROM feeds')
                        restore_flags = cur.fetchall()
                        cur.execute('UPDATE feeds SET enable = 1')
                        conn.commit()
                    except Exception as e:
                        print(f"Warning: could not enable all feeds: {e}")
                try:
                    feeds = get_feeds_from_db(conn)
                except Exception as e:
                    print(f"Warning: failed to read feeds from DB: {e}")
                    feeds = []
    except Exception as e:
        print(f"Warning during feed setup: {e}")
        feeds = []
    import os, json
    preview_items = []
    per_feed_stats = []

    for feed_id, feed_name, feed_url, category_id, category_name in feeds:
        print(f"\n[{feed_name}] Fetching up to {max_articles}, targeting {num_per_source} clean preview articles")
        try:
            articles = parse_rss_feed(feed_url, feed_name, category_id, max_articles=max_articles)
        except Exception as e:
            print(f"  ✗ Failed to parse feed {feed_name}: {e}")
            # Skip this feed but do not abort the whole preview run
            articles = []
        kept = 0
        feed_start = time.time()
        found_total = len(articles)
        accepted_total = 0
        for art in articles:
            # If this feed is taking too long, abort remaining items and move to next feed
            if per_feed_timeout and (time.time() - feed_start) > per_feed_timeout:
                print(f"  ⊘ Timeout after {per_feed_timeout}s for feed: {feed_name}, moving to next feed")
                break
            if kept >= num_per_source:
                break
            # basic filters
            if is_video_article(art['title'], art['description'], art['url']):
                continue
            if is_transcript_article(art['content'], art['title']):
                continue
            # clean content paragraphs
            paras = art['content'].split('\n') if art['content'] else []
            cleaned = clean_paragraphs(paras)
            if not cleaned:
                continue
            # Try RSS-provided image first (avoids JS/anti-bot pages)
            img_local = None
            rss_img = art.get('rss_image')
            if rss_img:
                try:
                    # Attempt to download the RSS image and enforce min size/type
                    # Use download_image_preview by passing article URL and a fake HTML containing the image tag
                    fake_html = f"<html><body><img src=\"{rss_img}\"/></body></html>"
                    img_local = download_image_preview(art['url'], fake_html, min_bytes=min_image_bytes)
                    if img_local:
                        print(f"  ✓ Preview accepted via RSS image: {art['title'][:60]}... -> {img_local}")
                        # Before accepting based on RSS image, fetch the article content
                        full_content = fetch_article_content(art['url'])
                        if full_content:
                            preview_items.append({
                                'title': art['title'],
                                'url': art['url'],
                                'source': art['source'],
                                'content': full_content,
                                'image': img_local
                            })
                            kept += 1
                            accepted_total += 1
                            continue
                        else:
                            # If fetching/cleaning full content failed, ignore this item
                            print(f"  ⊘ Skipped (no full content): {art['title'][:60]}...")
                            img_local = None
                except Exception:
                    img_local = None

            # If no RSS image or it didn't qualify, fetch page and try preview image
            if not img_local:
                try:
                    resp = requests.get(art['url'], timeout=10)
                    resp.raise_for_status()
                    img_local = download_image_preview(art['url'], resp.text, min_bytes=min_image_bytes)
                    if not img_local:
                        print(f"  ⊘ Skipped (no large image): {art['title'][:60]}...")
                        continue
                    # We have a page image; ensure we can fetch & clean full article content
                    full_content = fetch_article_content(art['url'])
                    if not full_content:
                        print(f"  ⊘ Skipped (no full content after page fetch): {art['title'][:60]}...")
                        continue
                except Exception:
                    print(f"  ⊘ Skipped (page fetch/error): {art['title'][:60]}...")
                    continue
                # accepted via page image
                preview_items.append({
                    'title': art['title'],
                    'url': art['url'],
                    'source': art['source'],
                    'content': '\n\n'.join(cleaned),
                    'image': img_local
                })
                kept += 1
                accepted_total += 1
                print(f"  ✓ Preview accepted: {art['title'][:60]}... -> {img_local}")

        # record per-feed stats
        per_feed_stats.append({
            'feed_id': feed_id,
            'feed_name': feed_name,
            'feed_url': feed_url,
            'found_total': found_total,
            'accepted_total': accepted_total,
            'target': num_per_source
        })

    # generate preview HTML
    import html as _html
    out = ['<!doctype html>', '<html><head><meta charset="utf-8"><title>Preview Articles</title>',
           '<style>body{font-family:Arial,Helvetica,sans-serif;line-height:1.45;margin:20px} .article{margin-bottom:50px} img{max-width:700px;height:auto}</style>',
           '</head><body>', '<h1>Preview Articles</h1>']

    # Insert a simple per-feed summary table at the top
    out.append('<h2>Per-feed Summary</h2>')
    out.append('<ul>')
    for s in per_feed_stats:
        out.append(f"<li>{_html.escape(s['feed_name'])}: found={s['found_total']}, accepted={s['accepted_total']}, target={s['target']}</li>")
    out.append('</ul>')

    for it in preview_items:
        # Titles from feeds may contain numeric HTML entities (e.g. &#8216;) —
        # unescape them first so they render correctly, then escape for safety.
        title_text = _html.unescape(it.get('title') or '')
        out.append(f"<div class='article'><h2>{_html.escape(title_text)}</h2>")
        out.append(f"<p><em>{_html.escape(it.get('source') or '')} - <a href='{_html.escape(it.get('url') or '')}'>Original</a></em></p>")
        if it['image'] and os.path.exists(it['image']):
            out.append(f"<p><img src='{_html.escape(it['image'])}'></p>")
        for p in it['content'].split('\n\n'):
            out.append(f"<p>{_html.escape(p)}</p>")
        out.append('</div>')

    out.append('</body></html>')
    with open('preview_articles.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print('\nGenerated preview_articles.html with', len(preview_items), 'items')
    # Also write a machine-readable catalog for automated runs
    catalog = {
        'generated_at': datetime.now().isoformat(),
        'total_items': len(preview_items),
        'per_feed': per_feed_stats
    }
    try:
        with open('preview_catalog.json', 'w', encoding='utf-8') as cf:
            json.dump(catalog, cf, indent=2)
        print('Wrote preview_catalog.json')
    except Exception:
        print('Failed to write preview_catalog.json')

    # Restore feed enable flags if we modified them
    if conn and enable_all_feeds and restore_flags is not None:
        try:
            cur = conn.cursor()
            for fid, flag in restore_flags:
                cur.execute('UPDATE feeds SET enable = ? WHERE feed_id = ?', (flag, fid))
            conn.commit()
            print('Restored feed enable flags')
        except Exception:
            print('Warning: failed to restore feed enable flags')
    if conn:
        conn.close()
    return preview_items


def parse_rss_feed(feed_url, source_name, category_id, max_articles=1):
    """Parse RSS feed and extract articles."""
    articles = []
    
    try:
        print(f"\n  Fetching {source_name} feed...")
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # Handle different RSS formats
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//entry')  # Atom format
        
        for item in items[:max_articles]:
            # Extract fields (handle both RSS and Atom formats)
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else ""
            
            # Link/URL
            link_elem = item.find('link')
            url = ""
            if link_elem is not None:
                if link_elem.text:  # RSS format
                    url = link_elem.text
                else:  # Atom format
                    href = link_elem.get('href')
                    url = href if href else ""
            
            # Description/Summary
            desc_elem = item.find('description')
            if desc_elem is None:
                desc_elem = item.find('summary')
            description = desc_elem.text if desc_elem is not None else ""
            
            # Content (often in description or content:encoded)
            content = description
            content_encoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            if content_encoded is not None and content_encoded.text:
                content = content_encoded.text
            
            # Publication date
            pub_date_elem = item.find('pubDate')
            if pub_date_elem is None:
                pub_date_elem = item.find('published')
            pub_date = pub_date_elem.text if pub_date_elem is not None else datetime.now().isoformat()
            
            if title and url:
                # Fetch full article content from URL
                full_content = fetch_article_content(url)
                if not full_content:
                    full_content = content  # Fall back to RSS content

                # Try to extract an image from the RSS item itself (media:content, enclosure, or <img> in description)
                rss_image = None
                # media:content or enclosure
                media = item.find('{http://search.yahoo.com/mrss/}content')
                if media is None:
                    media = item.find('enclosure')
                if media is not None:
                    # prefer url attribute
                    rss_image = media.get('url') if hasattr(media, 'get') else None

                # fallback: try to find an <img> tag in the description HTML
                if not rss_image and description:
                    try:
                        from bs4 import BeautifulSoup
                        dsoup = BeautifulSoup(description, 'html.parser')
                        img = dsoup.find('img')
                        if img and img.get('src'):
                            rss_image = img.get('src')
                    except Exception:
                        rss_image = None

                articles.append({
                    'title': title,
                    'source': source_name,
                    'url': url,
                    'description': description[:500] if description else "",
                    'content': full_content[:5000] if full_content else "",
                    'pub_date': pub_date,
                    'category_id': category_id,
                    'rss_image': rss_image
                })
                
                # Be respectful - add delay between requests
                time.sleep(0.3)
        
        print(f"  ✓ Found {len(articles)} article(s)")
        return articles
        
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch feed: {e}")
        return []
    except ET.ParseError as e:
        print(f"  ✗ Failed to parse XML: {e}")
        return []


def collect_articles(num_per_source=None, per_feed_timeout=None):
    """Collect articles from RSS feeds stored in database.

    Policy: For each active feed, fetch up to 20 items and keep up to
    `num_per_source` clean articles (stop early when the target is reached).
    """

    # Apply defaults from THRESHOLDS if not provided
    if num_per_source is None:
        num_per_source = THRESHOLDS.get('num_per_source', 1)
    if per_feed_timeout is None:
        per_feed_timeout = THRESHOLDS.get('per_feed_timeout', 240)

    if not DB_FILE.exists():
        print(f"✗ Database not found: {DB_FILE}")
        return False

    conn = sqlite3.connect(DB_FILE)

    print("\n" + "=" * 70)
    print("COLLECTING ARTICLES FROM RSS FEEDS")
    print("=" * 70)
    print(f"Target: {num_per_source} article(s) per source")

    # Get feeds from database
    feeds = get_feeds_from_db(conn)
    if not feeds:
        print("✗ No active feeds found in database")
        conn.close()
        return False

    print(f"Found {len(feeds)} active feed(s)")

    collected = 0
    duplicates = 0

    for feed_id, feed_name, feed_url, category_id, category_name in feeds:
        print(f"\n[{feed_name}]")

        max_to_fetch = THRESHOLDS.get('max_fetch_per_feed', 20)
        target_count = num_per_source
        print(f"  Fetching up to {max_to_fetch}, targeting {target_count} clean articles from {feed_name}")

        # Fetch feed items
        articles = parse_rss_feed(feed_url, feed_name, category_id, max_to_fetch)
        feed_start = time.time()
        print(f"  ✓ Found {len(articles)} article(s) in feed")

        # Process fetched articles and insert up to `target_count` clean articles
        clean_count = 0
        for article in articles:
            # Per-feed timeout: stop processing this feed after per_feed_timeout seconds
            if per_feed_timeout and (time.time() - feed_start) > per_feed_timeout:
                print(f"  ⊘ Timeout after {per_feed_timeout}s for feed: {feed_name}, moving to next feed")
                break
            # Stop early if we've collected enough clean articles for this feed
            if clean_count >= target_count:
                print(f"  ✓ {feed_name}: Reached target of {target_count} clean articles, stopping")
                break

            # Skip video articles
            if is_video_article(article['title'], article['description'], article['url']):
                print(f"  ⊘ Skipped (VIDEO): {article['title'][:60]}...")
                continue

            # Skip transcript-style articles
            if is_transcript_article(article['content'], article['title']):
                print(f"  ⊘ Skipped (TRANSCRIPT): {article['title'][:60]}...")
                continue

            # Skip games/puzzles/filler content
            if is_games_or_filler_article(article['title'], article['description'], article['content']):
                print(f"  ⊘ Skipped (GAMES/FILLER): {article['title'][:60]}...")
                continue

            # Skip articles outside character range (configured bounds)
            content_length = len(article['content'] or "")
            # Allow per-category overrides: sports feeds often have shorter articles
            min_chars = THRESHOLDS.get('cleaned_chars_min_global', 2300)
            # detect sports/tennis feeds by category name or feed name
            is_sport = False
            try:
                if category_name and 'sport' in category_name.lower():
                    is_sport = True
            except Exception:
                pass
            try:
                if not is_sport and feed_name and 'tennis' in feed_name.lower():
                    is_sport = True
            except Exception:
                pass

            if is_sport:
                # prefer relaxed sport threshold if configured, else a strict sport one
                min_chars = THRESHOLDS.get('sport_relaxed_min_chars', THRESHOLDS.get('sport_strict_min_chars', min_chars))

            max_chars = THRESHOLDS.get('cleaned_chars_max_global', 4500)
            if content_length < min_chars or content_length > max_chars:
                print(f"  ⊘ Skipped (LENGTH {content_length} < min {min_chars} or > max {max_chars}): {article['title'][:60]}...")
                continue

            # Skip duplicates
            if article_exists(conn, article['url']):
                print(f"  ⊘ Duplicate: {article['title'][:60]}...")
                duplicates += 1
                continue

            # Insert article
            article_id = insert_article(
                conn,
                article['title'],
                article['source'],
                article['url'],
                article['description'],
                article['content'],
                article['pub_date'],
                article['category_id']
            )

            if article_id:
                print(f"  ✓ Inserted (ID {article_id}): {article['title'][:60]}...")
                collected += 1
                clean_count += 1
                # Attempt to download first image from the article page and record it
                try:
                    page_resp = requests.get(article['url'], timeout=10)
                    page_resp.raise_for_status()
                    saved = download_and_record_image(conn, article_id, article['url'], page_resp.text)
                    if saved:
                        print(f"    ✓ Image saved: {saved}")
                    else:
                        print(f"    ⊘ No image saved for article ID {article_id}")
                except Exception:
                    print(f"    ⊘ Failed to fetch page for images: {article['url']}")

    conn.close()

    print("\n" + "=" * 70)
    print(f"✓ Collection complete: {collected} new articles, {duplicates} duplicates")
    print("=" * 70)

    return collected > 0


def main():
    """Main function."""
    print("\n" + "="*70)
    print("DATA COLLECTOR - RSS Feed Aggregator")
    print("="*70)
    
    collect_articles(num_per_source=5)
    
    # Show what was collected
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0")
    unprocessed = cursor.fetchone()[0]
    cursor.execute("SELECT id, title, source, category_id FROM articles WHERE deepseek_processed = 0")
    articles = cursor.fetchall()
    conn.close()
    
    print(f"\nReady for processing: {unprocessed} unprocessed article(s)")
    for article_id, title, source, category_id in articles:
        print(f"  - ID {article_id}: {title[:60]}... (Source: {source}, Category ID: {category_id})")
    
    print("\nNext: Run data_processor.py to process these articles through Deepseek")


if __name__ == "__main__":
    main()
