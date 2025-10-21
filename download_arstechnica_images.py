#!/usr/bin/env python3
import requests
import sqlite3
from pathlib import Path

IMAGES_DIR = Path('/var/www/news/article_images')
IMAGES_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect('/var/www/news/articles.db')
c = conn.cursor()

# Direct og:image URLs (from manual inspection)
images = {
    22: 'https://cdn.arstechnica.net/wp-content/uploads/2025/09/deadends4-1152x648.jpg',
    23: 'https://cdn.arstechnica.net/wp-content/uploads/2025/10/KSC-20250917-PH-FMX01_0037orig-768x1152.jpg',
    24: 'https://cdn.arstechnica.net/wp-content/uploads/2025/10/lead2-768x576.jpg'
}

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

print('Downloading ArsTechnica images...')
print('=' * 60)

for aid, img_url in images.items():
    print(f'\nArticle {aid}: {img_url[:60]}')
    try:
        response = requests.get(img_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        filename = f'article_{aid}.jpg'
        filepath = IMAGES_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        c.execute('''
            INSERT INTO article_images (article_id, image_name, original_url, local_location)
            VALUES (?, ?, ?, ?)
        ''', (aid, filename, img_url, str(filepath)))
        
        conn.commit()
        print(f'  ✓ Downloaded {len(response.content)} bytes')
        
    except Exception as e:
        print(f'  ✗ Error: {str(e)[:50]}')

conn.close()
print('\n' + '=' * 60)
print('✅ Complete')
