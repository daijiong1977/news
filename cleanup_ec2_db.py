#!/usr/bin/env python3
"""Clean up EC2 database"""

import sqlite3

conn = sqlite3.connect('articles.db')
c = conn.cursor()

print('🧹 Cleaning up EC2 Database...')
print('=' * 60)

# Clear all processed data
tables_to_clear = [
    'deepseek_feedback',
    'article_summaries',
    'keywords',
    'questions',
    'background_read',
    'comments',
    'choices'
]

for table in tables_to_clear:
    c.execute(f'DELETE FROM {table}')
    print(f'✓ Cleared {table}')

# Reset deepseek_processed flag
c.execute('UPDATE articles SET deepseek_processed = 0')
print(f'✓ Reset deepseek_processed flag for all articles')

conn.commit()

# Show final stats
c.execute('SELECT COUNT(*) FROM articles')
article_count = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM article_images')
image_count = c.fetchone()[0]

print()
print('=' * 60)
print(f'✅ Cleanup complete!')
print(f'   Articles preserved: {article_count}')
print(f'   Images preserved: {image_count}')
print(f'   Processed data cleared')

conn.close()
