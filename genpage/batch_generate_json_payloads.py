#!/usr/bin/env python3
"""
Generate clean JSON payloads from deepseek responses.
Creates payload_<articleid> directories with easy.json, middle.json, high.json
Includes article image URLs from database.
Tracks generation status in database to enable incremental updates.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import argparse


def get_db_connection():
    """Get database connection."""
    db_path = Path('/Users/jidai/news/articles.db')
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_article_image_url(article_id):
    """Get the image URL for an article from the database."""
    try:
        conn = get_db_connection()
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


def get_pending_articles(force=False):
    """Get articles that need payload generation.
    
    Args:
        force: If True, return all articles. If False, only return articles 
               where payload_generated = 0 or NULL.
    
    Returns:
        List of (article_id, respons_file) tuples
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if force:
            # Get all articles with response files
            cursor.execute('''
                SELECT article_id, respons_file 
                FROM response 
                WHERE respons_file IS NOT NULL
                ORDER BY article_id
            ''')
        else:
            # Get only articles that haven't been generated yet
            cursor.execute('''
                SELECT article_id, respons_file 
                FROM response 
                WHERE respons_file IS NOT NULL 
                  AND (payload_generated IS NULL OR payload_generated = 0)
                ORDER BY article_id
            ''')
        
        articles = cursor.fetchall()
        conn.close()
        
        return [(row['article_id'], row['respons_file']) for row in articles]
    except Exception as e:
        print(f"Error fetching articles from database: {e}")
        return []


def mark_payload_generated(article_id, payload_dir):
    """Mark article as having payloads generated in database.
    
    Args:
        article_id: Article ID
        payload_dir: Name of the payload directory (e.g., 'payload_2025102501')
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE response 
            SET payload_generated = 1,
                payload_generated_at = ?,
                payload_directory = ?
            WHERE article_id = ?
        ''', (now, payload_dir, article_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Warning: Could not update database for {article_id}: {e}")


def generate_payload_jsons(force=False):
    """Generate clean JSON payloads for articles at all difficulty levels.
    
    Args:
        force: If True, regenerate all payloads. If False, only generate missing ones.
    """
    
    output_base = Path('/Users/jidai/news/website/article_page')
    
    # Get articles that need payload generation
    articles = get_pending_articles(force=force)
    
    if not articles:
        if force:
            print("No articles with response files found in database")
        else:
            print("No articles need payload generation (all up to date)")
        return
    
    mode = "all articles (forced)" if force else "pending articles only"
    print(f"Generating payloads for {len(articles)} {mode}\n")
    
    success_count = 0
    
    for article_id, response_file_path in articles:
        # Load the deepseek response
        try:
            response_path = Path(response_file_path)
            if not response_path.is_absolute():
                # If relative path stored in DB, make it absolute
                response_path = Path('/Users/jidai/news') / response_path
                
            with open(response_path, 'r', encoding='utf-8') as f:
                response_data = json.load(f)
        except Exception as e:
            print(f"✗ Error loading response for {article_id}: {e}")
            continue
        
        # Create payload directory for this article
        payload_dir_name = f'payload_{article_id}'
        payload_dir = output_base / payload_dir_name
        payload_dir.mkdir(parents=True, exist_ok=True)
        
        # Get article image URL
        image_url = get_article_image_url(article_id)
        
        # Extract levels data
        levels_data = response_data.get('article_analysis', {}).get('levels', {})
        
        # Generate for all 3 levels
        levels_generated = 0
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
                
                levels_generated += 1
            except Exception as e:
                print(f"✗ Error generating {level} for {article_id}: {e}")
        
        if levels_generated == 3:
            # Mark as generated in database
            mark_payload_generated(article_id, payload_dir_name)
            print(f"✓ {article_id} → {payload_dir_name}/")
            success_count += 1
        else:
            print(f"⚠ {article_id} → Partial generation ({levels_generated}/3 levels)")
    
    print(f"\n✓ Complete! Generated {success_count}/{len(articles)} article payloads")
    
    # Show summary
    payload_dirs = sorted(output_base.glob('payload_*'))
    print(f"Total payload directories: {len(payload_dirs)}")
    
    # Show total size
    total_size = 0
    for payload_dir in payload_dirs:
        for json_file in payload_dir.glob('*.json'):
            total_size += json_file.stat().st_size
    
    print(f"Total payload size: {total_size / 1024:.1f} KB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate JSON payloads for articles')
    parser.add_argument('--force', action='store_true', 
                        help='Regenerate all payloads (default: only generate missing ones)')
    
    args = parser.parse_args()
    generate_payload_jsons(force=args.force)
