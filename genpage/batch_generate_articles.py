#!/usr/bin/env python3
"""
Batch generate article pages for all difficulty levels.
Creates payload_<articleid> directories with easy/mid/high versions.
"""

import json
import os
from pathlib import Path
from datetime import datetime


def generate_article_pages_batch():
    """Generate article pages for all articles at all difficulty levels."""
    
    responses_dir = Path('/Users/jidai/news/website/responses')
    output_base = Path('/Users/jidai/news/website/article_page')
    
    # Get all response files
    response_files = sorted(responses_dir.glob('article_*.json'))
    
    if not response_files:
        print("No response files found in website/responses/")
        return
    
    print(f"Found {len(response_files)} response files")
    
    for response_file in response_files:
        # Extract article ID from filename (e.g., article_2025102501_response.json)
        filename = response_file.stem  # article_2025102501_response
        article_id = filename.replace('article_', '').replace('_response', '')
        
        print(f"\nProcessing article {article_id}...")
        
        # Create payload directory for this article
        payload_dir = output_base / f'payload_{article_id}'
        payload_dir.mkdir(exist_ok=True)
        
        # Generate for all 3 levels
        for level in ['easy', 'middle', 'high']:
            try:
                # Run the generator
                cmd = f"cd /Users/jidai/news && python3 genpage/generate_article_page.py {response_file} {level} en"
                result = os.system(cmd)
                
                if result == 0:
                    # Move generated file to payload directory
                    generated_file = Path(f'/Users/jidai/news/article_{article_id}_response_{level}.html')
                    if generated_file.exists():
                        dest_file = payload_dir / f'article_{level}.html'
                        generated_file.rename(dest_file)
                        print(f"  ✓ Generated {level}: {dest_file.name}")
                else:
                    print(f"  ✗ Failed to generate {level}")
            except Exception as e:
                print(f"  ✗ Error generating {level}: {e}")
    
    print(f"\n✓ Batch generation complete!")
    print(f"Output directory: {output_base}")
    
    # Show summary
    payload_dirs = list(output_base.glob('payload_*'))
    print(f"\nCreated {len(payload_dirs)} payload directories")
    
    # List first few
    for payload_dir in sorted(payload_dirs)[:5]:
        files = sorted(payload_dir.glob('*.html'))
        print(f"  {payload_dir.name}: {len(files)} files")


if __name__ == '__main__':
    generate_article_pages_batch()
