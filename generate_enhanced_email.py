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
    """Generate enhanced email with modern Tailwind-based layout."""
    
    with open(payload_file) as f:
        payload = json.load(f)
    
    if not output_file:
        output_file = f"email_enhanced_{level}.html"
    
    server_domain = payload.get('server_domain', 'http://localhost:8000')
    levels = payload.get('levels', {})
    articles = levels.get(level, [])
    
    # Level display info
    level_info = {
        'easy': ('🟢 Easy Level', 'Beginner-Friendly Content', '#10b981', 'Engaging News for High Schoolers - Easy Reading Level'),
        'mid': ('🔵 Mid Level', 'Intermediate Content', '#3b82f6', 'Engaging News for High Schoolers - Intermediate Level'),
        'hard': ('🟠 Hard Level', 'Expert-Level Content', '#f59e0b', 'Engaging News for High Schoolers - Advanced Level'),
        'CN': ('🔴 中文版本', 'Chinese Translation', '#ef4444', '高中生新闻 - 中文版')
    }
    
    emoji, title, primary_color, description = level_info.get(level, ('📰', 'News Digest', '#13a4ec', 'News Digest'))
    category_articles = get_category_articles()
    
    html = f"""<!DOCTYPE html>
<html class="light" lang="{'zh' if level == 'CN' else 'en'}">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>{emoji} InsightFeed - {title}</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz@6..72&amp;family=Noto+Sans:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
    <script id="tailwind-config">
      tailwind.config = {{
        darkMode: "class",
        theme: {{
          extend: {{
            colors: {{
              "primary": "{primary_color}",
              "background-light": "#f6f7f8",
              "background-dark": "#101c22",
              "text-light": "#111618",
              "text-dark": "#f0f3f4",
              "text-muted-light": "#617c89",
              "text-muted-dark": "#9cb3bf",
            }},
            fontFamily: {{
              "display": ["Newsreader", "serif"],
              "sans": ["Noto Sans", "sans-serif"],
            }},
            borderRadius: {{"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"}},
          }},
        }},
      }}
    </script>
    <style>
        body {{
            font-family: 'Noto Sans', sans-serif;
        }}
        
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark">
<div class="relative flex min-h-screen w-full flex-col">
<header class="sticky top-0 z-10 w-full bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-sm border-b border-text-light/10 dark:border-text-dark/10">
<div class="mx-auto flex max-w-5xl items-center justify-between whitespace-nowrap px-4 sm:px-6 lg:px-8 py-3">
<a class="flex items-center gap-3 text-text-light dark:text-text-dark" href="#">
<div class="h-6 w-6">
<svg fill="currentColor" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
<g clip-path="url(#clip0_6_330)">
<path clip-rule="evenodd" d="M24 0.757355L47.2426 24L24 47.2426L0.757355 24L24 0.757355ZM21 35.7574V12.2426L9.24264 24L21 35.7574Z" fill-rule="evenodd"></path>
</g>
<defs>
<clipPath id="clip0_6_330"><rect fill="white" height="48" width="48"></rect></clipPath>
</defs>
</svg>
</div>
<h2 class="font-display text-2xl font-bold tracking-tight">InsightFeed {emoji}</h2>
</a>
<nav class="hidden md:flex items-center gap-6">
<a class="text-sm font-medium text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">News</a>
<a class="text-sm font-medium text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">Science</a>
<a class="text-sm font-medium text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">Fun</a>
</nav>
</div>
</header>
<main class="flex-grow">
<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10 md:py-16">
<div class="flex flex-col gap-12 md:gap-16">
"""
    
    # Add featured articles
    if articles:
        for i, article in enumerate(articles[:2]):  # Show max 2 articles side-by-side
            title_text = article.get('title', 'No Title')
            summary = article.get('summary', 'No Summary')
            article_id = article.get('article_id', 'N/A')
            image = article.get('image', {})
            server_url = image.get('server_url', '')
            
            # Determine category based on article content (simplified)
            category = "Technology"  # Default category
            
            html += f"""<div class="w-full @container">
<div class="flex flex-col items-stretch justify-start rounded-xl overflow-hidden bg-white dark:bg-background-dark shadow-sm border border-text-light/10 dark:border-text-dark/10">
{f'<div class="w-full bg-center bg-no-repeat aspect-[16/7] bg-cover" data-alt="{title_text}" style=\'background-image: url("{server_url}");\' ></div>' if server_url else '<div class="w-full bg-center bg-no-repeat aspect-[16/7] bg-cover" style="background: linear-gradient(135deg, var(--tw-colors-primary) 0%, var(--tw-colors-primary) 100%);"></div>'}
<div class="p-6 md:p-8">
<p class="text-sm font-medium text-primary mb-1">{category}</p>
<h3 class="font-display text-2xl md:text-3xl font-bold tracking-tight text-text-light dark:text-text-dark">{title_text}</h3>
<div class="mt-2 flex items-center gap-x-2 text-xs text-text-muted-light dark:text-text-muted-dark">
<span>Article #{article_id}</span>
<span class="h-1 w-1 rounded-full bg-text-muted-light/50 dark:bg-text-muted-dark/50"></span>
<span>{title}</span>
</div>
<p class="text-text-muted-light dark:text-text-muted-dark mt-3 text-base md:text-lg">
{summary}
</p>
<div class="mt-6 flex">
<button class="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-5 bg-primary text-white text-sm font-medium leading-normal transition-transform hover:scale-105">
<span class="truncate">Start Activity</span>
</button>
</div>
</div>
</div>
</div>
"""
    
    html += """</div>
</div>
</main>
<footer class="bg-white dark:bg-background-dark border-t border-text-light/10 dark:border-text-dark/10">
<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10 md:py-16">
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8 text-left">
"""
    
    # Add category sections
    for category, cat_articles in category_articles.items():
        html += f"""<div>
<h4 class="font-display text-lg font-bold text-text-light dark:text-text-dark mb-4">{category}</h4>
<ul class="space-y-3">
"""
        
        for cat_article in cat_articles[:2]:  # Show max 2 articles per category
            html += f"""<li><a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary text-sm transition-colors" href="#">{cat_article['title']}</a></li>
"""
        
        html += """</ul>
</div>
"""
    
    # Footer
    generated_at = payload.get('generated_at', datetime.now().isoformat())
    
    html += f"""</div>
<div class="mt-12 pt-8 border-t border-text-light/10 dark:border-text-dark/10 flex flex-col sm:flex-row items-center justify-between gap-6">
<div class="flex flex-wrap justify-center gap-x-6 gap-y-2">
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary text-sm transition-colors" href="#">About Us</a>
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary text-sm transition-colors" href="#">Privacy Policy</a>
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary text-sm transition-colors" href="#">Contact Us</a>
</div>
<div class="flex justify-center gap-4">
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">
<span class="material-symbols-outlined">alternate_email</span>
</a>
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">
<span class="material-symbols-outlined">camera_alt</span>
</a>
<a class="text-text-muted-light dark:text-text-muted-dark hover:text-primary dark:hover:text-primary transition-colors" href="#">
<span class="material-symbols-outlined">group</span>
</a>
</div>
<p class="text-text-muted-light dark:text-text-muted-dark text-sm order-first sm:order-last">© 2024 InsightFeed. All rights reserved.</p>
</div>
<div class="mt-4 text-center">
<p class="text-text-muted-light dark:text-text-muted-dark text-xs">Generated: {generated_at}</p>
</div>
</div>
</footer>
</div>

</body></html>
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
