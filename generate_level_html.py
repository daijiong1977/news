#!/usr/bin/env python3
"""
Generate separate HTML email files for each difficulty level.
Creates: email_easy.html, email_mid.html, email_hard.html, email_cn.html
"""

import json
from pathlib import Path
from datetime import datetime

def generate_level_html(payload_file: str, level: str, output_file: str = None):
    """Generate HTML email for a specific difficulty level."""
    
    with open(payload_file) as f:
        payload = json.load(f)
    
    if not output_file:
        output_file = f"email_{level}.html"
    
    server_domain = payload.get('server_domain', 'http://localhost:8000')
    image_base_path = payload.get('image_base_path', '/api/images')
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
            background-color: #f5f5f5;
        }}
        
        .email-container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            color: white;
            padding: 50px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.95;
            margin-bottom: 5px;
        }}
        
        .header .subtitle {{
            font-size: 13px;
            opacity: 0.85;
        }}
        
        .content {{
            padding: 40px 20px;
        }}
        
        .article {{
            margin-bottom: 40px;
            padding: 25px;
            background-color: #fafafa;
            border-radius: 10px;
            border-left: 5px solid {color};
            transition: box-shadow 0.3s ease;
        }}
        
        .article:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .article-header {{
            display: flex;
            gap: 25px;
            margin-bottom: 20px;
        }}
        
        .article-image {{
            flex-shrink: 0;
        }}
        
        .article-image img {{
            width: 180px;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        }}
        
        .article-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .article-id {{
            display: inline-block;
            background-color: {color};
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
            width: fit-content;
        }}
        
        .article-title {{
            font-size: 20px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        
        .article-summary {{
            color: #4b5563;
            font-size: 14px;
            line-height: 1.7;
            text-align: justify;
        }}
        
        .footer {{
            background-color: #f3f4f6;
            padding: 30px 20px;
            text-align: center;
            border-top: 2px solid #e5e7eb;
        }}
        
        .footer h3 {{
            font-size: 16px;
            margin-bottom: 10px;
            color: #1f2937;
        }}
        
        .footer p {{
            margin: 8px 0;
            font-size: 13px;
            color: #6b7280;
        }}
        
        .generated-time {{
            font-size: 12px;
            color: #9ca3af;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #d1d5db;
        }}
        
        .no-image .article-header {{
            flex-direction: column;
        }}
        
        .level-badge {{
            display: inline-block;
            background-color: {color}20;
            color: {color};
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        
        @media (max-width: 768px) {{
            .article-header {{
                flex-direction: column;
            }}
            
            .article-image img {{
                width: 100%;
                height: auto;
                max-width: 300px;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
            
            .content {{
                padding: 20px 15px;
            }}
            
            .article {{
                padding: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{emoji}</h1>
            <p>{title}</p>
            <p class="subtitle">{description}</p>
        </div>
        
        <div class="content">
            <div class="level-badge">{emoji} {title}</div>
"""
    
    # Add articles
    if not articles:
        html += f"""            <div class="article">
                <p style="text-align: center; color: #9ca3af;">No articles available for this level.</p>
            </div>
"""
    else:
        for i, article in enumerate(articles, 1):
            title_text = article.get('title', 'No Title')
            summary = article.get('summary', 'No Summary')
            article_id = article.get('article_id', 'N/A')
            image = article.get('image', {})
            image_name = image.get('image_name', '')
            server_url = image.get('server_url', '')
            
            html += f"""            <div class="article{'no-image' if not image_name else ''}">
                <div class="article-id">Article #{article_id}</div>
"""
            
            if image_name and server_url:
                html += f"""                <div class="article-header">
                    <div class="article-image">
                        <img src="{server_url}" alt="{title_text}" loading="lazy">
                    </div>
                    <div class="article-content">
                        <div class="article-title">{title_text}</div>
                        <div class="article-summary">{summary}</div>
                    </div>
                </div>
"""
            else:
                html += f"""                <div class="article-header">
                    <div class="article-content">
                        <div class="article-title">{title_text}</div>
                        <div class="article-summary">{summary}</div>
                    </div>
                </div>
"""
            
            html += """            </div>
"""
    
    # Footer
    generated_at = payload.get('generated_at', datetime.now().isoformat())
    html += f"""        </div>
        
        <div class="footer">
            <h3>📚 News Digest - {title}</h3>
            <p>This email contains news articles at the {title.lower()} difficulty level.</p>
            <p>Select this level based on your reading preference and language skills.</p>
            <p class="generated-time">Generated: {generated_at}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated: {output_file} ({len(articles)} articles, {len(html)} bytes)")
    return output_file

if __name__ == "__main__":
    payload_file = "payloads/email_combined_payload.json"
    
    # Generate HTML for each level
    levels = ['easy', 'mid', 'hard', 'CN']
    
    print("📧 Generating level-specific HTML files...\n")
    
    for level in levels:
        output_file = f"email_{level}.html"
        generate_level_html(payload_file, level, output_file)
    
    print("\n✅ All HTML files generated successfully!")
    print("\nGenerated files:")
    print("  - email_easy.html (🟢 Beginner-Friendly)")
    print("  - email_mid.html  (🔵 Intermediate)")
    print("  - email_hard.html (🟠 Expert-Level)")
    print("  - email_CN.html   (🔴 Chinese)")
