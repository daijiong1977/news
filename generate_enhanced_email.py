#!/usr/bin/env python3
"""
Generate enhanced email template with:
- Side-by-side articles with dynamic width
- Better header and footer
- Category sections below (News, Science, Sports) with 2-3 articles each
"""

import json
from pathlib import Path
from datetime import datetime

def get_category_articles():
    """Get sample articles from different categories for the footer section."""
    return {
        'News': [
            {'title': 'Global Climate Summit Reaches Historic Agreement', 'id': 15},
            {'title': 'New International Trade Deal Announced', 'id': 16},
            {'title': 'Election Results Surprise Political Analysts', 'id': 17}
        ],
        'Science': [
            {'title': 'Scientists Discover New Species in Amazon Rainforest', 'id': 18},
            {'title': 'Breakthrough in Cancer Research Shows Promise', 'id': 19},
            {'title': 'NASA Detects Potential Signs of Water on Distant Moon', 'id': 20}
        ],
        'Sports': [
            {'title': 'Championship Team Celebrates Historic Victory', 'id': 21},
            {'title': 'Young Athlete Breaks World Record', 'id': 22},
            {'title': 'International Tournament Draws Record Viewership', 'id': 23}
        ]
    }

def generate_enhanced_email(payload_file: str, level: str, output_file: str = None):
    """Generate enhanced email with side-by-side articles and category sections."""
    
    with open(payload_file) as f:
        payload = json.load(f)
    
    if not output_file:
        output_file = f"email_enhanced_{level}.html"
    
    server_domain = payload.get('server_domain', 'http://localhost:8000')
    levels = payload.get('levels', {})
    articles = levels.get(level, [])
    
    # Level display info
    level_info = {
        'easy': ('🟢 Easy Level', 'Beginner-Friendly Content', '#10b981', 'For beginners and those learning the topic'),
        'mid': ('🔵 Mid Level', 'Intermediate Content', '#3b82f6', 'For readers with moderate knowledge'),
        'hard': ('🟠 Hard Level', 'Expert-Level Content', '#f59e0b', 'For experts and deep analysis'),
        'CN': ('🔴 中文版本', 'Chinese Translation', '#ef4444', '中文版本的完整内容翻译')
    }
    
    emoji, title, color, description = level_info.get(level, ('📰', 'News Digest', '#667eea', 'News Digest'))
    category_articles = get_category_articles()
    
    html = f"""<!DOCTYPE html>
<html lang="{'zh' if level == 'CN' else 'en'}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{emoji} News Digest - {title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
            padding: 20px 0;
        }}
        
        .email-wrapper {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        }}
        
        /* HEADER */
        .header {{
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            border-bottom: 5px solid {color};
        }}
        
        .header h1 {{
            font-size: 42px;
            margin-bottom: 15px;
            font-weight: 800;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header .level-name {{
            font-size: 28px;
            margin-bottom: 10px;
            opacity: 0.98;
            font-weight: 600;
        }}
        
        .header .description {{
            font-size: 14px;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        /* FEATURED ARTICLES SECTION */
        .featured-section {{
            padding: 50px 40px;
            background: linear-gradient(to bottom, #ffffff 0%, #f9f9f9 100%);
            border-bottom: 3px solid #f0f0f0;
        }}
        
        .section-title {{
            font-size: 24px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid {color};
            display: inline-block;
        }}
        
        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 20px;
        }}
        
        .article {{
            background-color: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border-top: 4px solid {color};
            display: flex;
            flex-direction: column;
            height: auto;
        }}
        
        .article:hover {{
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .article-image {{
            width: 100%;
            height: auto;
            max-height: 250px;
            object-fit: cover;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .article-content {{
            padding: 25px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .article-id {{
            display: inline-block;
            background-color: {color}15;
            color: {color};
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}
        
        .article-title {{
            font-size: 18px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        
        .article-summary {{
            font-size: 13px;
            color: #5a6b7c;
            line-height: 1.7;
            text-align: justify;
            word-wrap: break-word;
            overflow-wrap: break-word;
            flex-grow: 1;
        }}
        
        /* CATEGORY SECTIONS */
        .category-sections {{
            padding: 50px 40px;
            background-color: #ffffff;
        }}
        
        .category-section {{
            margin-bottom: 35px;
        }}
        
        .category-section:last-child {{
            margin-bottom: 0;
        }}
        
        .category-header {{
            font-size: 16px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 15px;
            display: inline-block;
            padding-bottom: 8px;
            border-bottom: 2px solid {color};
        }}
        
        .category-header span {{
            background-color: {color}15;
            color: {color};
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
            display: inline-block;
        }}
        
        .article-list {{
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .article-list li {{
            display: inline-block;
            background-color: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            transition: all 0.2s;
        }}
        
        .article-list li:hover {{
            background-color: {color}10;
            border-color: {color};
        }}
        
        .article-list li a {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}
        
        .article-list li a:hover {{
            color: {color};
        }}
        
        /* FOOTER */
        .footer {{
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            border-top: 5px solid {color};
        }}
        
        .footer h3 {{
            font-size: 18px;
            margin-bottom: 15px;
            font-weight: 700;
        }}
        
        .footer p {{
            margin: 10px 0;
            font-size: 13px;
            opacity: 0.9;
            line-height: 1.6;
        }}
        
        .footer-links {{
            margin: 25px 0;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        
        .footer-links a {{
            color: #60a5fa;
            text-decoration: none;
            margin: 0 15px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        .footer-links a:hover {{
            color: white;
            text-decoration: underline;
        }}
        
        .generated-time {{
            font-size: 11px;
            color: #9ca3af;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        /* RESPONSIVE */
        @media (max-width: 1200px) {{
            .articles-grid {{
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            }}
        }}
        
        @media (max-width: 768px) {{
            .articles-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .header {{
                padding: 40px 20px;
            }}
            
            .header h1 {{
                font-size: 32px;
            }}
            
            .featured-section,
            .category-sections {{
                padding: 30px 20px;
            }}
            
            .article-image {{
                height: auto;
                max-height: 200px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- HEADER -->
        <div class="header">
            <h1>{emoji}</h1>
            <div class="level-name">{title}</div>
            <div class="description">{description}</div>
        </div>
        
        <!-- FEATURED ARTICLES -->
        <div class="featured-section">
            <div class="section-title">Featured Articles</div>
            <div class="articles-grid">
"""
    
    # Add featured articles
    if articles:
        for i, article in enumerate(articles[:2]):  # Show max 2 articles side-by-side
            title_text = article.get('title', 'No Title')
            summary = article.get('summary', 'No Summary')
            article_id = article.get('article_id', 'N/A')
            image = article.get('image', {})
            server_url = image.get('server_url', '')
            
            # Use full summary - no truncation
            
            html += f"""                <div class="article">
                    {f'<img src="{server_url}" alt="{title_text}" class="article-image" loading="lazy">' if server_url else '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 200px;"></div>'}
                    <div class="article-content">
                        <div class="article-id">Article #{article_id}</div>
                        <div class="article-title">{title_text}</div>
                        <div class="article-summary">{summary}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
        </div>
        
        <!-- CATEGORY SECTIONS -->
        <div class="category-sections">
"""
    
    # Add category sections
    for category, cat_articles in category_articles.items():
        category_emoji = {'News': '📰', 'Science': '🔬', 'Sports': '⚽'}.get(category, '📌')
        
        html += f"""            <div class="category-section">
                <div class="category-header"><span>{category_emoji} {category}</span></div>
                <ul class="article-list">
"""
        
        for cat_article in cat_articles[:3]:  # Show max 3 articles per category
            html += f"""                    <li><a href="#">{cat_article['title']}</a></li>
"""
        
        html += """                </ul>
            </div>
"""
    
    # Footer
    generated_at = payload.get('generated_at', datetime.now().isoformat())
    
    html += f"""        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            <h3>📚 News Digest</h3>
            <p>Your daily source of educational news content tailored to your reading level.</p>
            <p>Stay informed, stay curious, keep learning!</p>
            
            <div class="footer-links">
                <a href="#">Preferences</a>
                <a href="#">Archive</a>
                <a href="#">Unsubscribe</a>
                <a href="#">Contact</a>
            </div>
            
            <p class="generated-time">Generated: {generated_at}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Enhanced email generated: {output_file} ({len(html)} bytes)")
    return output_file

if __name__ == "__main__":
    payload_file = "payloads/email_combined_payload.json"
    
    # Generate enhanced HTML for each level
    levels = ['easy', 'mid', 'hard', 'CN']
    
    print("📧 Generating enhanced email layouts...\n")
    
    for level in levels:
        output_file = f"email_enhanced_{level}.html"
        generate_enhanced_email(payload_file, level, output_file)
    
    print("\n✅ All enhanced email layouts generated successfully!")
    print("\nGenerated files:")
    print("  - email_enhanced_easy.html")
    print("  - email_enhanced_mid.html")
    print("  - email_enhanced_hard.html")
    print("  - email_enhanced_CN.html")
