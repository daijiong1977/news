"""
Generate email templates using real payload files (article_12 and article_2).
Uses actual AI-generated summaries at different difficulty levels.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def load_payload_file(article_id):
    """Load the most recent payload file for an article."""
    responses_dir = Path('/Users/jidai/news/responses')
    
    # Find the most recent response file for this article
    pattern = f'response_article_{article_id}_*.json'
    response_files = list(responses_dir.glob(pattern))
    
    if not response_files:
        print(f"No payload found for article {article_id}")
        return None
    
    # Get the most recent one
    latest_file = sorted(response_files)[-1]
    print(f"Loading: {latest_file.name}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {latest_file}: {e}")
        return None

def get_articles_from_db(limit=10):
    """Get articles from database for navigation."""
    conn = sqlite3.connect('/Users/jidai/news/articles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id as article_id,
            title,
            'Technology' as category
        FROM articles
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return articles

def get_content_by_level(payload, level):
    """Extract content from payload based on difficulty level."""
    if not payload or 'article_analysis' not in payload:
        return None
    
    levels = payload['article_analysis'].get('levels', {})
    level_data = levels.get(level, {})
    
    content = {
        'title': level_data.get('title', ''),
        'summary': level_data.get('summary', ''),
        'keywords': level_data.get('keywords', []),
        'questions': level_data.get('questions', [])
    }
    
    # For hard level, also check for Chinese version (zh_hard and title_zh)
    if level == 'hard':
        if 'zh_hard' in level_data:
            content['zh_summary'] = level_data['zh_hard']
        if 'title_zh' in level_data:
            content['zh_title'] = level_data['title_zh']
    
    return content

def generate_email_html(feature1_article_id, feature2_article_id, read_level='mid', subscriber_name='Friend', use_chinese=False):
    """
    Generate email HTML using two real payload files as features.
    If use_chinese=True, uses zh_hard content from hard level.
    """
    
    # Load the two feature payloads
    payload1 = load_payload_file(feature1_article_id)
    payload2 = load_payload_file(feature2_article_id)
    
    if not payload1 or not payload2:
        return "<p>Error: Could not load payload files</p>"
    
    # Get content for the specified level
    feature1_content = get_content_by_level(payload1, read_level)
    feature2_content = get_content_by_level(payload2, read_level)
    
    if not feature1_content or not feature2_content:
        return f"<p>Error: Could not extract {read_level} level content from payloads</p>"
    
    # Use Chinese versions if requested
    if use_chinese:
        # Use Chinese title and summary if available
        if 'zh_title' in feature1_content:
            feature1_content['title'] = feature1_content['zh_title']
        if 'zh_summary' in feature1_content:
            feature1_content['summary'] = feature1_content['zh_summary']
            
        if 'zh_title' in feature2_content:
            feature2_content['title'] = feature2_content['zh_title']
        if 'zh_summary' in feature2_content:
            feature2_content['summary'] = feature2_content['zh_summary']
        
        display_level = 'CN'
    else:
        display_level = read_level.upper()
    
    # Get DB articles for navigation (excluding the two features)
    all_articles = get_articles_from_db(limit=20)
    nav_articles = [a for a in all_articles if a['article_id'] not in [feature1_article_id, feature2_article_id]][:6]
    
    # Extract image URLs from DB
    feature1_db = next((a for a in all_articles if a['article_id'] == feature1_article_id), None)
    feature2_db = next((a for a in all_articles if a['article_id'] == feature2_article_id), None)
    
    image1 = 'https://via.placeholder.com/600x400?text=Article+12'
    image2 = 'https://via.placeholder.com/600x400?text=Article+2'
    category1 = 'Technology'
    category2 = 'Technology'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News for Kids - Daily Digest</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }}
        .email-container {{ 
            max-width: 600px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        /* HEADER */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 5px;
        }}
        .header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .greeting {{
            font-size: 16px;
            margin-top: 15px;
            font-weight: 500;
        }}
        
        /* FEATURE CARD */
        .feature-card {{
            border-bottom: 1px solid #eee;
            padding: 0;
            overflow: hidden;
        }}
        .feature-image {{
            width: 100%;
            height: 300px;
            object-fit: cover;
            display: block;
        }}
        .feature-content {{
            padding: 30px;
        }}
        .feature-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 12px;
            color: #666;
            align-items: center;
            flex-wrap: wrap;
        }}
        .level-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
        }}
        .level-easy {{ background: #d4edda; color: #155724; }}
        .level-mid {{ background: #fff3cd; color: #856404; }}
        .level-hard {{ background: #f8d7da; color: #721c24; }}
        .level-cn {{ background: #cfe2ff; color: #084298; }}
        
        .category {{
            color: #667eea;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 4px;
        }}
        
        .feature-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin: 15px 0;
            line-height: 1.3;
        }}
        .feature-summary {{
            font-size: 14px;
            color: #555;
            line-height: 1.7;
            margin: 15px 0;
        }}
        
        .keywords {{
            margin: 15px 0;
            padding: 12px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .keywords-title {{
            font-size: 12px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        .keyword-item {{
            display: inline-block;
            background: white;
            padding: 4px 10px;
            margin: 4px 4px 4px 0;
            border-radius: 4px;
            font-size: 12px;
            color: #555;
            border: 1px solid #e0e0e0;
        }}
        
        .cta-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        .cta-button {{
            flex: 1;
            display: inline-block;
            padding: 12px 16px;
            text-align: center;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
            transition: all 0.3s;
        }}
        .cta-quiz {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .cta-read {{
            background: #f0f0f0;
            color: #667eea;
            border: 2px solid #667eea;
        }}
        
        /* NAVIGATION */
        .nav-section {{
            padding: 30px;
            background: #f9f9f9;
        }}
        .nav-title {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }}
        .nav-list {{
            list-style: none;
        }}
        .nav-item {{
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .nav-item:last-child {{
            border-bottom: none;
        }}
        .nav-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
        }}
        .nav-link:hover {{
            text-decoration: underline;
        }}
        .nav-category {{
            color: #999;
            font-size: 12px;
            margin-left: 10px;
        }}
        
        /* FOOTER */
        .footer {{
            background: #f5f5f5;
            padding: 20px 30px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #eee;
        }}
        .footer-links {{
            margin-bottom: 15px;
        }}
        .footer-links a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 10px;
        }}
        .footer-links a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <!-- HEADER -->
        <div class="header">
            <h1>📚 News for Kids</h1>
            <p>Your personalized daily news digest</p>
            <p class="greeting">Hello {subscriber_name}! Here's today's top stories in {display_level} level...</p>
        </div>
        
        <!-- FEATURE 1 -->
        <div class="feature-card">
            <img src="{image1}" alt="{feature1_content['title']}" class="feature-image">
            <div class="feature-content">
                <div class="feature-meta">
                    <span class="level-badge level-{read_level if read_level != 'hard' else 'hard'}" style="{'background: #cfe2ff; color: #084298;' if use_chinese else ''}">{display_level}</span>
                    <span class="category">Technology</span>
                </div>
                
                <h2 class="feature-title">{feature1_content['title']}</h2>
                
                <p class="feature-summary">{feature1_content['summary']}</p>
"""
    
    # Add keywords if available
    if feature1_content['keywords']:
        html += """
                <div class="keywords">
                    <div class="keywords-title">📖 Key Words:</div>
"""
        for keyword in feature1_content['keywords'][:5]:  # Show first 5
            term = keyword.get('term', '') if isinstance(keyword, dict) else keyword
            html += f'                    <span class="keyword-item">{term}</span>\n'
        html += """
                </div>
"""
    
    html += f"""
                <div class="cta-buttons">
                    <a href="https://news.6ray.com/articles/{feature1_article_id}/{read_level}.html" class="cta-button cta-quiz">
                        🧠 Test Knowledge
                    </a>
                    <a href="https://news.6ray.com/articles/{feature1_article_id}/{read_level}.html" class="cta-button cta-read">
                        📖 Read Full
                    </a>
                </div>
            </div>
        </div>
        
        <!-- FEATURE 2 -->
        <div class="feature-card">
            <img src="{image2}" alt="{feature2_content['title']}" class="feature-image">
            <div class="feature-content">
                <div class="feature-meta">
                    <span class="level-badge level-{read_level if read_level != 'hard' else 'hard'}" style="{'background: #cfe2ff; color: #084298;' if use_chinese else ''}">{display_level}</span>
                    <span class="category">Technology</span>
                </div>
                
                <h2 class="feature-title">{feature2_content['title']}</h2>
                
                <p class="feature-summary">{feature2_content['summary']}</p>
"""
    
    # Add keywords if available
    if feature2_content['keywords']:
        html += """
                <div class="keywords">
                    <div class="keywords-title">📖 Key Words:</div>
"""
        for keyword in feature2_content['keywords'][:5]:  # Show first 5
            term = keyword.get('term', '') if isinstance(keyword, dict) else keyword
            html += f'                    <span class="keyword-item">{term}</span>\n'
        html += """
                </div>
"""
    
    html += f"""
                <div class="cta-buttons">
                    <a href="https://news.6ray.com/articles/{feature2_article_id}/{read_level}.html" class="cta-button cta-quiz">
                        🧠 Test Knowledge
                    </a>
                    <a href="https://news.6ray.com/articles/{feature2_article_id}/{read_level}.html" class="cta-button cta-read">
                        📖 Read Full
                    </a>
                </div>
            </div>
        </div>
        
        <!-- NAVIGATION -->
        <div class="nav-section">
            <div class="nav-title">📰 More Today's Stories</div>
            <ul class="nav-list">
"""
    
    for article in nav_articles:
        html += f"""
                <li class="nav-item">
                    <a href="https://news.6ray.com/articles/{article['article_id']}/{read_level}.html" class="nav-link">
                        {article['title']}
                    </a>
                    <span class="nav-category">• {article['category']}</span>
                </li>
"""
    
    html += """
            </ul>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            <div class="footer-links">
                <a href="https://news.6ray.com/preferences">Update Preferences</a>
                <a href="https://news.6ray.com/unsubscribe">Unsubscribe</a>
            </div>
            <p>© 2025 News for Kids. All rights reserved.</p>
            <p style="margin-top: 10px; font-size: 11px; color: #999;">
                You're receiving this because you subscribed to our newsletter.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

# Generate previews for all levels using article_12 and article_2
if __name__ == '__main__':
    feature1_id = 12
    feature2_id = 2
    
    print(f"\n{'='*60}")
    print(f"Generating email previews using Article {feature1_id} and Article {feature2_id}")
    print('='*60 + "\n")
    
    for level in ['easy', 'mid', 'hard', 'cn']:
        print(f"Generating: {level.upper()} level")
        
        # For CN level, use 'hard' to access zh_hard content
        read_level = 'hard' if level == 'cn' else level
        
        html = generate_email_html(
            feature1_article_id=feature1_id,
            feature2_article_id=feature2_id,
            read_level=read_level,
            subscriber_name='Friend',
            use_chinese=(level == 'cn')
        )
        
        output_file = f'/Users/jidai/news/email_manager/preview_email_{level}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  ✅ Saved: {output_file}")
        print(f"     View: file://{output_file}\n")
    
    print("✅ All email previews generated!")
    print("\nOpen these files in your browser to preview:")
    print("  • file:///Users/jidai/news/email_manager/preview_email_easy.html")
    print("  • file:///Users/jidai/news/email_manager/preview_email_mid.html")
    print("  • file:///Users/jidai/news/email_manager/preview_email_hard.html")
    print("  • file:///Users/jidai/news/email_manager/preview_email_cn.html")
