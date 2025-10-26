#!/usr/bin/env python3
"""
Generate clean JSON payloads from deepseek responses.
Creates payload_<articleid> directories with easy.json, middle.json, high.json
Includes article image URLs from database.
"""

import json
import sqlite3
from pathlib import Path


def get_article_image_url(article_id):
    """Get the image URL for an article from the database."""
    try:
        db_path = Path('/Users/jidai/news/articles.db')
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT small_location FROM article_images WHERE article_id = ? LIMIT 1',
            (article_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            local_path = row['small_location']
            # Convert /var/www/news/website/article_image/... to /article_image/...
            if '/article_image/' in local_path:
                return '/article_image/' + local_path.split('/article_image/')[-1]
            else:
                return local_path
    except Exception as e:
        print(f"Warning: Could not fetch image for {article_id}: {e}")
    
    return None


def generate_payload_jsons():
    """Generate clean JSON payloads for all articles at all difficulty levels."""
    
    responses_dir = Path('/Users/jidai/news/website/responses')
    output_base = Path('/Users/jidai/news/website/article_page')
    
    # Get all response files
    response_files = sorted(responses_dir.glob('article_*_response.json'))
    
    if not response_files:
        print("No response files found in website/responses/")
        return
    
    print(f"Found {len(response_files)} response files\n")
    
    for response_file in response_files:
        # Extract article ID
        filename = response_file.stem  # article_2025102501_response
        article_id = filename.replace('article_', '').replace('_response', '')
        
        # Load the deepseek response
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                response_data = json.load(f)
        except Exception as e:
            print(f"✗ Error loading {response_file}: {e}")
            continue
        
        # Create payload directory for this article
        payload_dir = output_base / f'payload_{article_id}'
        payload_dir.mkdir(parents=True, exist_ok=True)
        
        # Get article image URL
        image_url = get_article_image_url(article_id)
        
        # Extract levels data
        levels_data = response_data.get('article_analysis', {}).get('levels', {})
        
        # Generate for all 3 levels
        for level in ['easy', 'middle', 'high']:
            try:
                level_info = levels_data.get(level, {})
                
                # Add image URL if available
                if image_url:
                    level_info['image_url'] = image_url
                
                # Write JSON payload with just the level data
                payload_file = payload_dir / f'{level}.json'
                with open(payload_file, 'w', encoding='utf-8') as f:
                    json.dump(level_info, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                print(f"✗ Error generating {level}: {e}")
    
    print(f"✓ Complete!")
    
    # Show summary
    payload_dirs = sorted(output_base.glob('payload_*'))
    print(f"\nCreated {len(payload_dirs)} payload directories")
    
    # Show total size
    total_size = 0
    for payload_dir in payload_dirs:
        for json_file in payload_dir.glob('*.json'):
            total_size += json_file.stat().st_size
    
    print(f"Total payload size: {total_size / 1024:.1f} KB")
    
    # Show examples
    print(f"\nExample structure:")
    first_payload = payload_dirs[0]
    for json_file in sorted(first_payload.glob('*.json')):
        size = json_file.stat().st_size
        print(f"  {first_payload.name}/{json_file.name} ({size} bytes)")


if __name__ == '__main__':
    generate_payload_jsons()
