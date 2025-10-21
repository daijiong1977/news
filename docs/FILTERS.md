# Filters and Heuristics — news project

This document lists the current filters, rules, and site-specific heuristics used by the mining/preview pipeline in this repository. Use this as a reference when adding new feeds, tuning thresholds, or creating site-specific scrapers.

Files & entry points
- Main collector and cleaning code: `data_collector.py`
- Batch preview runner: `scripts/batch_collect_preview.py`
- Age-13 filter runner: `scripts/run_age13_filter.py`
- Age-13 banned-word list: `config/age13_banned.txt`
- Preview artifact outputs: `*.html` files in repo root (e.g. `batch_review_*.html`, `bbc_business_preview_*.html`)

Principles
- Preview-first: The pipeline prefers to generate a preview page with downloaded images and cleaned content for human review; nothing is inserted into the DB until the user explicitly approves.
- Conservative image selection: prefer explicit OpenGraph/twitter images and srcset entries; avoid selecting logos/placeholders or PNGs that are likely icons.
- Safety-first content filtering: certain content is dropped outright (age-13 banned words), while other items are skipped from processing (video, transcripts, filler).
- Per-feed resilience: long-running feeds cannot block the entire run — a per-feed timeout is enforced by default.

Global filters (applied by `clean_paragraphs()`)
- HTML unescape: raw feed HTML entities are unescaped and normalized (smart ASCII replacements for common punctuation and ellipses).
- Drop very short paragraphs: paragraphs shorter than ~30 characters are removed (to skip bylines, tags, or boilerplate).
  - Exact threshold used in code: paragraphs with length < 30 characters are removed by default. This value is configurable in `clean_paragraphs()`.
- Byline detection and removal:
  - Exact matches to a configured set of publisher byline names are removed.
  - Repeated two-word names (e.g., "Nick Schifrin Nick Schifrin") are treated as bylines and removed.
  - Short all‑caps or short proper-case lines (2–3 words) are removed as likely bylines.
  - Name-with-colon patterns that match known byline names are removed.
- Promo and emoji filtering:
  - Paragraphs that start with promo emojis (✅, 🔒, 🔥, ⭐, ✨, 💥, 🚨, 🎉) and are short are dropped.
  - Short promotional lines containing percentages, "off", "save", "discount", or explicit sale-related phrases are removed.
  - Common ad/affiliate terms (e.g., 'sign up', 'sponsored', 'affiliate commission', 'buy now', 'vpn', 'nordvpn') are removed when appearing as short lines.
- Boilerplate removal:
  - Known publisher boilerplate (e.g., "Follow TechRadar") and funding statements ("Funding:") are removed.
  - Trailing footers that look like addresses, copyright, or short numeric sequences are stripped from the end of the article content.
- 'Related:' lines: paragraphs starting with `Related:` are removed.
- Duplicate paragraphs: consecutive duplicate paragraphs are suppressed.
- Minimum paragraph/content thresholds: content must produce a non-empty cleaned result; separate pipelines (sport preview, batch) may require extra character-length thresholds.
  - Explicit content-length thresholds currently used in the codebase:
    - Global default (all feeds except sport): cleaned content length must be between 2300 and 4500 characters (inclusive). This is the standard range used for preview acceptance unless a caller or per-feed rule overrides it.
    - Sport preview/short-listing (strict): cleaned content length >= 1500 characters (historical value).
    - Sport preview (relaxed): cleaned content length >= 1200 characters (applied during later re-runs to improve yield).

Age-13 banned-word filter (strict removal)
- Location: `config/age13_banned.txt` — a newline-separated list of words/phrases.
- Behavior: when the compiled regex (case-insensitive word boundary aware) matches anywhere in an article's combined text (title + cleaned paragraphs), the article is dropped (not cleaned) and not included in previews.
- Regex used (conceptually): `(?i)(?<!\w)(word1|word2|...)(?!\w)` — ensures whole-word-ish matching and case-insensitive.
- Example entries: `rape`, `rapist`, `fuck`, `blowjob`, `pedophile`, `incest`, `murder`, `suicide` (the list is configurable).

High-level skip filters
- Video detection: `is_video_article(title, description, url)` looks for keywords/phrases indicating the piece is video-first ("Watch:", "video:", "full episode") — these are skipped.
- Transcript detection: `is_transcript_article(content, title)` detects interview/transcript formats and skips them (various heuristics for speaker patterns, 'transcript' + 'audio', repeated 'Name: quote' patterns).
- Games/filler detection: `is_games_or_filler_article()` detects puzzles, wordle-style pieces and drops them.

Image selection and rules
- Preference order when collecting candidates (applies to preview and DB image download helpers):
  1. OpenGraph meta: `<meta property="og:image">`
  2. Twitter meta: `<meta name="twitter:image">`
  3. `<link rel="image_src">` if present
  4. `<picture>` / `<source>` entries (parse `srcset` and pick best entry with `_choose_best_from_srcset()`)
  5. Article selectors: `article img`, `div.article img`, `div.main img`, `figure img`, `img` (with srcset handling)
- Normalization & filtering:
  - Resolve relative URLs with `urljoin(article_url, src)`.
  - Skip images with URL hints of favicons/logo/placeholders (filename or path containing `favicon`, `logo`, `placeholder`, `spacer`, `blank`, `icons`, etc.).
  - Prefer JPG/JPEG/WEBP; skip PNGs by default (PNG often used for logos/placeholders).
  - Exclude images whose download Content-Type is `image/png`.
  - Minimal bytes gate: require `>= 2000` bytes for preview downloads (used in quick previews); stricter runs use higher thresholds (common strict value: `>= 70000` bytes). These values are settable in code.
    - Explicit image byte thresholds used by scripts and in code:
      - Quick preview threshold: `min_image_bytes = 2000` (2KB) — used for fast previews where any reasonable image is acceptable.
      - Batch/strict threshold: `min_image_bytes = 70000` (70KB) — used for batch collection and sport short-listing to prefer full-resolution article images.
      - When selecting an image candidate the downloader also checks the HTTP `Content-Type` header and rejects `image/png`.
- Srcset parsing: `_choose_best_from_srcset(srcset)` picks the largest width or highest density entry from a comma-separated srcset.
- Scoring (present but used primarily for DB path): `_score_image_candidate()` scores preferred hosts (e.g., BBC's `ichef.bbci.co.uk`), same-origin images, and larger width markers; however preview downloads generally accept the first valid candidate following the preference order to avoid selecting unrelated large CDN assets.

Image filter requirements (clean-image rules)

- Purpose: these rules apply when deciding whether an image candidate is acceptable as the "clean" article image (for preview and eventual DB record). Implemented in `download_image_preview()` and `download_and_record_image()`.
- Priority of sources (first-match wins unless rejected by filters):
  1. OpenGraph meta (`<meta property="og:image">`)
  2. Twitter meta (`<meta name="twitter:image">`)
  3. `<link rel="image_src">`
  4. `<picture>` / `<source>` (`srcset` parsed and best candidate chosen)
  5. Article-specific selectors (`article img`, `figure img`, `div.article img`, etc.)

- Format and content-type rules:
  - Prefer `image/jpeg`, `image/jpg`, `image/webp`. These are treated as first-class candidates.
  - Reject `image/png` (PNG commonly used for logos, icons, and placeholders) by Content-Type check.
  - If Content-Type is not provided or ambiguous, inspect file extension and prefer `.jpg`, `.jpeg`, `.webp` and deprioritize `.png`.

- URL-based rejection blacklist (case-insensitive substring checks):
  - If the image URL contains any of: `favicon`, `logo`, `placeholder`, `spacer`, `blank`, `icon`, `icons`, `sprite`, `badge`, `pixel` → reject candidate.

- Size thresholds (downloaded bytes):
  - Quick preview: `min_image_bytes = 2000` (2 KB) — used for fast runs.
  - Batch/strict and default clean-image gate: `min_image_bytes = 70000` (70 KB) — used for batch processing and when we want high-quality images for DB records.
  - Per-feed overrides: scripts or callers may pass a different `min_image_bytes` to accept smaller images for certain feeds.

- Additional heuristics:
  - If an image URL has explicit size hints in `srcset` (e.g., `... 800w`), prefer the larger width candidate when selecting from `srcset`.
  - Prefer same-origin images (host matching article host) and known article CDNs (e.g., BBC's `ichef.bbci.co.uk`) in scoring if multiple candidates remain.
  - If multiple candidates meet all rules, choose the first candidate in the preference order above; this avoids picking large unrelated site chrome images.

- Failure modes & fallbacks:
  - If no candidate passes the clean-image checks, the preview may still be produced without an image (caller can decide to drop the article if image is required).
  - For WAF/403 issues (e.g., TheStreet), the downloader may record the failure in `debug/` and skip the image; advanced options: proxy, headless browser (Playwright), or site-specific allowance policies.

- Where to change these rules in the code:
  - `download_image_preview()` — quick preview downloader and pre-checks.
  - `download_and_record_image()` — image download used during DB insertion (applies stricter checks and records metadata).
  - `_choose_best_from_srcset()` — parse & prefer larger width or density entries.
  - `_score_image_candidate()` — adjust scoring weights for preferred hosts or same-origin bias.


Per-source / catalog special rules and notes
- BBC (news / sport / entertainment):
  - Image hosts like `ichef.bbci.co.uk` are preferred in scoring.
  - Title & paragraph unescaping: titles/HTML entities are unescaped before output to avoid numeric-entity literals in previews.
- TechRadar:
  - Frequently contains promotional lines and boilerplate; `clean_paragraphs()` aggressively strips TechRadar-specific phrases.
  - Image selection prefers meta/srcset order to avoid picking site chrome images.
- TheStreet:
  - Observed 403 responses for article page requests. Debugging steps saved under `debug/the_street/` include attempts with different headers and `cloudscraper`. This may be a WAF/Cloudflare or IP-based block — a different approach (headless browser, proxy, or publisher API) may be required.
- Sport feeds: special content thresholds have been used historically:
  - Original special: accept if cleaned content >= 1500 characters and image >= 70,000 bytes (used for sport short-listing).
  - Later relaxed to: cleaned content >= 1200 characters and image >= 70,000 bytes (applied during re-runs for better yield).

Batch and preview runners (rules summary)
- `scripts/batch_collect_preview.py`:
  - Backs up DB & image dir.
  - Clears `articles` and `article_images` tables and removes local images.
  - Enables all feeds and parses top 20 items per feed; accepts up to 3 clean articles per feed.
  - Uses `min_image_bytes=70000` for the batch (trusts larger images) and saves preview HTML with `Saved full page` links.
- `collect_preview()` in `data_collector.py`:
  - Default: iterate enabled feeds, parse top 20 items, accept up to `num_per_source` (default 5) items with a qualifying preview image.
  - `min_image_bytes` parameter controls preview strictness.

Timeouts and robustness
- Per-feed timeout: `collect_preview()` and `collect_articles()` accept a `per_feed_timeout` (default 240 seconds). If a feed's per-item processing exceeds this, the feed results are aborted and the collector moves to the next feed.
  - Exact timeout default: `per_feed_timeout = 240` seconds (4 minutes) in the current implementation.
- Request timeouts are used on HTTP calls (typical `requests.get(..., timeout=10)` for pages; preview runs sometimes use lower thresholds to speed up runs).

Where to change behavior
- `data_collector.py` — main spot to change:
  - `clean_paragraphs()` — adjust removal heuristics and PROMO/AD lists.
  - `download_image_preview()` and `download_and_record_image()` — modify image candidate rules, min byte thresholds, and PNG handling.
  - `is_video_article()`, `is_transcript_article()`, `is_games_or_filler_article()` — change skip heuristics.
  - `collect_preview()` and `collect_articles()` — adjust `num_per_source`, `min_image_bytes`, and `per_feed_timeout`.

  Summary of numeric thresholds and filter conditions (one place)

  - Paragraph removal: paragraph.length < 30 → drop.
  - Duplicate paragraph suppression: consecutive duplicates removed.
  - Promo/emoji short-line drop: short lines (typically < 80 chars) starting with promo emojis or matching promo/ad patterns are removed.
  - Minimum cleaned content length (per-run):
    - Global default (non-sport): 2300 <= cleaned_chars <= 4500 and image_bytes meets the configured `min_image_bytes` for the run.
    - Sport strict: cleaned_chars >= 1500 and image_bytes >= 70000.
    - Sport relaxed: cleaned_chars >= 1200 and image_bytes >= 70000.
    - Batch collect: uses `min_image_bytes = 70000` and otherwise follows the global default cleaned_chars range unless the batch caller explicitly sets a different `min_chars`/override for a feed.
    - Quick preview: `min_image_bytes = 2000` (2 KB) and quick previews typically do not enforce the global upper/lower char bounds unless the caller passes `min_chars`/`max_chars`.
  - Image candidate acceptance:
    - Skip if URL contains any of: `favicon`, `logo`, `placeholder`, `spacer`, `blank`, `icon`, `icons`, `sprite`.
    - Reject if HTTP Content-Type == `image/png`.
    - Require downloaded bytes >= configured `min_image_bytes`.
  - Age-13 banned words: match anywhere in title + cleaned paragraphs using case-insensitive word boundaries; if any match → drop article entirely (not included in preview).
  - Skip filters: if `is_video_article()` or `is_transcript_article()` returns True → skip article.

  If you'd like, I can also change the code to centralize these numeric defaults into a single `config/thresholds.json` (or constants block) so they're easier to review and tune. That would be a small code change (1 file edit + tests).
- `config/age13_banned.txt` — add/remove banned words for the age-13 filter.
- `scripts/*` — batch scripts implement particular collection strategies and thresholds.

How to add a site-specific rule
1. Prefer simple heuristics in `clean_paragraphs()` for generic cleanup.
2. If the site requires DOM-specific fixes (e.g., remove certain container text, or select a particular `picture` element), add small logic into `download_image_preview()` or create a per-source helper (e.g., `_select_image_for_techradar(html, base_url)`).
3. Add tests or a small runner script under `scripts/` and generate a preview HTML for inspection before modifying DB behavior.

Notes & future ideas
- Consider a small site-policy file per feed (e.g., `config/site_rules/the_street.json`) to describe exceptions (user-agent, use-cloudscraper, allow-png) rather than hard-coding many source checks.
- For stubborn WAF-protected sites (TheStreet), consider a headless browser approach (Playwright) behind an allowed IP or a publisher API if one exists.
- Add a `requirements.txt` to pin exact versions for reproducible runs (`requests`, `beautifulsoup4`, `cloudscraper`, `playwright` if used).

Change log
- 2025-10-21: Initial documentation generated from the implementation in `data_collector.py`, `scripts/` and configuration files.

---

If you'd like, I can expand this document with per-feed tables (feed name → active thresholds → notes) or generate a `config/site_rules/` scaffold so site exceptions are data-driven.