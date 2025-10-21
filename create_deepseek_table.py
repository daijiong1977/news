#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('articles.db')
c = conn.cursor()

print('Creating deepseek_feedback table on EC2...')
print('=' * 60)

c.execute("""
    CREATE TABLE IF NOT EXISTS deepseek_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        summary_en TEXT,
        summary_zh TEXT,
        key_words TEXT,
        background_reading TEXT,
        multiple_choice_questions TEXT,
        discussion_both_sides TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles(id)
    )
""")

conn.commit()

# Verify the table was created
c.execute("PRAGMA table_info(deepseek_feedback)")
schema = c.fetchall()

if schema:
    print('✅ deepseek_feedback table created successfully!')
    print('\nTable Schema:')
    for col_id, name, type_, notnull, default, pk in schema:
        print(f'  {name:30s} | {type_:10s} | PK:{pk}')
else:
    print('❌ Failed to create deepseek_feedback table')

conn.close()
