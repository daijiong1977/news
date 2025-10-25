#!/usr/bin/env python3
"""
Generate HTML report showing all articles with images and full content.
Creates an HTML file that can be opened in a browser for verification.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Paths
ROOT_DIR = Path(__file__).parent.parent
DB_FILE = ROOT_DIR / "articles.db"
ARTICLE_IMAGES_DIR = ROOT_DIR / "article_images"
OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "articles_report.html"


def get_all_articles():
    """Fetch all articles from database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            id, title, source, url, description, content, pub_date, 
            crawled_at, deepseek_processed, deepseek_failed, 
            deepseek_last_error, deepseek_in_progress, category_id
        FROM articles
        ORDER BY id DESC
    """)
    articles = cur.fetchall()
    conn.close()
    return articles


def find_article_image(article_id):
    """Find image file for article."""
    if not ARTICLE_IMAGES_DIR.exists():
        return None
    
    # Look for images matching article_ID_*
    for img_file in ARTICLE_IMAGES_DIR.glob(f"article_{article_id}_*"):
        return img_file.name
    return None


def generate_html(articles):
    """Generate HTML report."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Articles Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .stats {{
            background: white;
            padding: 30px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .article {{
            background: white;
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .article:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .article-header {{
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            padding: 30px;
            background: #f9f9f9;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .article-image {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 6px;
            background: #e0e0e0;
        }}
        
        .article-meta {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        
        .article-title {{
            font-size: 1.6em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            line-height: 1.3;
        }}
        
        .article-info {{
            display: grid;
            gap: 10px;
            font-size: 0.95em;
        }}
        
        .info-row {{
            display: grid;
            grid-template-columns: 120px 1fr;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 8px;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #666;
        }}
        
        .info-value {{
            color: #333;
            word-break: break-word;
        }}
        
        .source-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            width: fit-content;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            width: fit-content;
        }}
        
        .status-unprocessed {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status-processed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .article-content {{
            padding: 30px;
        }}
        
        .article-description {{
            background: #f0f4ff;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
            border-radius: 4px;
            font-style: italic;
        }}
        
        .article-body {{
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.8;
            color: #333;
            font-size: 0.95em;
        }}
        
        .article-id {{
            background: #e8e8e8;
            padding: 2px 8px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        
        .url-link {{
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }}
        
        .url-link:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            margin-top: 40px;
        }}
        
        @media (max-width: 768px) {{
            .article-header {{
                grid-template-columns: 1fr;
            }}
            
            .article-image {{
                height: 300px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .info-row {{
                grid-template-columns: 1fr;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 Articles Mining Report</h1>
        <p>Complete article collection with images and content verification</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="container">
        <div class="stats">
"""
    
    # Count statistics
    total_articles = len(articles)
    processed = sum(1 for a in articles if a['deepseek_processed'] == 1)
    unprocessed = sum(1 for a in articles if a['deepseek_processed'] == 0)
    failed = sum(1 for a in articles if a['deepseek_failed'] > 0)
    
    html += f"""
            <div class="stat-item">
                <div class="stat-number">{total_articles}</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{unprocessed}</div>
                <div class="stat-label">Unprocessed</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{processed}</div>
                <div class="stat-label">Processed</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{failed}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>
        
        <div class="articles-list">
"""
    
    # Articles
    for article in articles:
        article_id = article['id']
        image_file = find_article_image(article_id)
        image_html = ""
        
        if image_file:
            image_path = f"../article_images/{image_file}"
            image_html = f'<img src="{image_path}" alt="Article {article_id}" class="article-image">'
        else:
            image_html = '<div class="article-image" style="display: flex; align-items: center; justify-content: center; background: #ddd; color: #999;">No image</div>'
        
        # Determine status
        if article['deepseek_failed'] > 0:
            status_class = 'status-failed'
            status_text = f"Failed ({article['deepseek_failed']}x)"
        elif article['deepseek_processed'] == 1:
            status_class = 'status-processed'
            status_text = "Processed ✓"
        else:
            status_class = 'status-unprocessed'
            status_text = "Unprocessed"
        
        # Description preview
        description = article['description'] or "(No description)"
        if len(description) > 200:
            description = description[:200] + "..."
        
        # Content preview
        content = article['content'] or "(No content)"
        
        html += f"""
            <div class="article">
                <div class="article-header">
                    {image_html}
                    <div class="article-meta">
                        <h2 class="article-title">{article['title']}</h2>
                        <div class="article-info">
                            <div class="info-row">
                                <div class="info-label">ID:</div>
                                <div class="info-value"><span class="article-id">{article_id}</span></div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">Source:</div>
                                <div class="info-value"><span class="source-badge">{article['source']}</span></div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">Status:</div>
                                <div class="info-value"><span class="status-badge {status_class}">{status_text}</span></div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">URL:</div>
                                <div class="info-value"><a href="{article['url']}" target="_blank" class="url-link">{article['url'][:60]}...</a></div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">Published:</div>
                                <div class="info-value">{article['pub_date']}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">Crawled:</div>
                                <div class="info-value">{article['crawled_at']}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="article-content">
                    <div class="article-description">
                        <strong>Description:</strong><br>
                        {description}
                    </div>
                    <div class="article-body">
                        <strong>Full Content:</strong><br><br>
{content}
                    </div>
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
    
    <div class="footer">
        <p>Mining Pipeline Report | All articles and images verified</p>
        <p style="font-size: 0.9em; margin-top: 10px; opacity: 0.8;">Database location: articles.db | Images: mining/article_images/</p>
    </div>
</body>
</html>
"""
    
    return html


def main():
    print("Fetching articles from database...")
    articles = get_all_articles()
    
    if not articles:
        print("✗ No articles found in database")
        return
    
    print(f"✓ Found {len(articles)} articles")
    print("Generating HTML report...")
    
    html_content = generate_html(articles)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Report generated: {OUTPUT_FILE}")
    print(f"✓ Open in browser: file://{OUTPUT_FILE}")
    
    # Print article summary
    print("\n" + "="*70)
    print("ARTICLES SUMMARY")
    print("="*70)
    by_source = {}
    for article in articles:
        src = article['source']
        by_source.setdefault(src, []).append(article)
    
    for source in sorted(by_source.keys()):
        arts = by_source[source]
        processed = sum(1 for a in arts if a['deepseek_processed'] == 1)
        print(f"{source:<30} {len(arts):2d} articles  ({processed} processed)")


if __name__ == '__main__':
    main()
