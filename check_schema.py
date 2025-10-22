#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('articles.db')
c = conn.cursor()

# Get schema of deepseek_feedback
try:
    c.execute("PRAGMA table_info(deepseek_feedback)")
    schema = c.fetchall()
    if not schema:
        print('deepseek_feedback table not found or has no columns (it may be deprecated).')
    else:
        print('deepseek_feedback Table Schema:')
        print('=' * 80)
        for row in schema:
            col_id, name, type_, notnull, default, pk = row
            print(f'  {name:30s} | {type_:10s} | PK:{pk} | NOT NULL:{notnull} | DEFAULT:{default}')
except Exception as e:
    print(f'Error checking schema: {e}')

conn.close()
