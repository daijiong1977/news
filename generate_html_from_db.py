#!/usr/bin/env python3
"""Generate HTML digest from database articles."""

import pathlib
import datetime as dt
import json
from db_utils import get_articles_by_source


def html_escape(value: str) -> str:
    """Escape HTML special characters."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html_from_db(output_file: str = "daily_digest.html") -> None:
    """Generate HTML digest from database articles."""
    # Load config to get articles_per_source setting
    config = {}
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception:
        pass
    
    limit_per_source = config.get("digest_settings", {}).get("articles_per_source", 3)
    articles_by_source = get_articles_by_source(limit_per_source=limit_per_source)
    
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    articles_html: list[str] = []
    
    for source in sorted(articles_by_source.keys()):
        articles = articles_by_source[source]
        
        articles_html.append(
            f'    <section class="source-section">\n'
            f'        <h2 class="source-title">{html_escape(source)}</h2>'
        )
        
        for article in articles:
            title = html_escape(article["title"])
            link = html_escape(article["link"])
            pub_date = article["date_iso"]
            summary = html_escape(article.get("summary", ""))
            image_file = article.get("image_file")
            content_file = article.get("content_file")
            
            articles_html.append(
                f'        <article class="story">\n'
                f'            <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>\n'
                f'            <p class="meta">{pub_date}</p>\n'
            )
            
            # Add image if available
            if image_file:
                image_path = pathlib.Path(image_file)
                if image_path.exists():
                    rel_image_path = html_escape(str(image_path))
                    articles_html.append(
                        f'            <div class="image-container">\n'
                        f'                <img src="{rel_image_path}" alt="{title[:50]}" class="article-image" />\n'
                        f'            </div>\n'
                    )
            
            # Add summary
            if summary:
                articles_html.append(
                    f'            <div class="summary">\n'
                    f'                <p>{summary}</p>\n'
                    f'            </div>\n'
                )
            
            # Add link to full content file if available
            if content_file:
                content_path = pathlib.Path(content_file)
                if content_path.exists():
                    rel_content_path = html_escape(str(content_path))
                    articles_html.append(
                        f'            <p class="content-link">'
                        f'<a href="{rel_content_path}" target="_blank">📄 Read full article</a>'
                        f'</p>\n'
                    )
            
            articles_html.append('        </article>')
        
        articles_html.append('    </section>')
    
    html_doc = (
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Daily News Digest</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        header {{ background: #fff; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        header h1 {{ color: #1a1a1a; margin-bottom: 0.5rem; }}
        header p {{ color: #666; font-size: 0.9rem; }}
        .source-section {{ background: #fff; margin-bottom: 2rem; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .source-section:first-of-type .source-title {{ margin-top: 0; }}
        .source-title {{ background: #007bff; color: white; padding: 1rem; margin: 0; font-size: 1.3rem; }}
        article.story {{ margin: 1.5rem; padding: 1.5rem; border: 1px solid #eee; border-radius: 4px; background: #fafafa; page-break-inside: avoid; }}
        article.story h3 {{ margin: 0 0 0.5rem 0; font-size: 1.1rem; }}
        article.story a {{ color: #007bff; text-decoration: none; }}
        article.story a:hover {{ text-decoration: underline; }}
        .meta {{ margin: 0 0 1rem 0; color: #666; font-size: 0.85rem; }}
        .image-container {{ margin: 1rem 0; text-align: center; }}
        .article-image {{ max-width: 100%; height: auto; max-height: 400px; border-radius: 4px; }}
        .summary {{ background: #f0f7ff; padding: 1rem; border-left: 4px solid #007bff; margin: 1rem 0; border-radius: 2px; }}
        .summary p {{ margin: 0; color: #333; font-size: 0.95rem; line-height: 1.5; }}
        .content-link {{ text-align: center; margin: 1rem 0; }}
        .content-link a {{ display: inline-block; padding: 0.5rem 1rem; background: #e7f3ff; color: #007bff; text-decoration: none; border-radius: 4px; font-size: 0.9rem; }}
        .content-link a:hover {{ background: #d0e8ff; }}
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            article.story {{ margin: 1rem; }}
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ max-width: 100%; }}
            article.story {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 Daily News Digest</h1>
            <p>Generated {now}</p>
        </header>
        {''.join(articles_html)}
    </div>
</body>
</html>"""
    )
    
    # Write to file
    output_path = pathlib.Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    
    print(f"✓ HTML digest written to {output_file}")
    
    # Count articles
    total = sum(len(articles) for articles in articles_by_source.values())
    print(f"✓ Total articles: {total}")
    for source, articles in articles_by_source.items():
        print(f"  • {source}: {len(articles)}")


if __name__ == "__main__":
    render_html_from_db()
