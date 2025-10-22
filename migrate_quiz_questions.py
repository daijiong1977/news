#!/usr/bin/env python3
"""Migrate legacy `quiz_questions` rows into normalized `questions` and `choices` tables.

Usage: python3 migrate_quiz_questions.py [--db articles.db] [--preview]

- Creates a DB backup in ./backups with a timestamp before making changes.
- Adds `question_number` column to `questions` table if missing to preserve ordering.
- Reads all rows from `quiz_questions` and inserts corresponding rows into `questions` and `choices`.
- By default runs in preview mode (no writes) unless --apply is passed.

The script is idempotent for applied rows: it will skip migration of a quiz_questions row
if it finds a questions row with the same article_id and question_text.
"""

import sqlite3
import argparse
import pathlib
import shutil
import time
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent
DB_PATH = ROOT / 'articles.db'
BACKUP_DIR = ROOT / 'backups'


def backup_db(db_path: pathlib.Path) -> pathlib.Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'articles.db.backup_{ts}'
    shutil.copy2(db_path, backup_path)
    print(f'Created DB backup: {backup_path}')
    return backup_path


def ensure_question_number_column(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(questions)")
    cols = [r[1] for r in cur.fetchall()]
    if 'question_number' not in cols:
        print('Adding question_number column to questions table...')
        cur.execute('ALTER TABLE questions ADD COLUMN question_number INTEGER')
        conn.commit()
        print('Added question_number column')
    else:
        print('questions.question_number already exists')


def migrate(conn: sqlite3.Connection, apply: bool = False):
    cur = conn.cursor()

    # Check if quiz_questions table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_questions'")
    if not cur.fetchone():
        print('No quiz_questions table found. Nothing to migrate.')
        return

    # Read all legacy quiz rows
    cur.execute('SELECT id, article_id, question_number, question_type, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, created_at FROM quiz_questions ORDER BY article_id, question_number')
    rows = cur.fetchall()
    print(f'Found {len(rows)} rows in quiz_questions')

    migrated = 0
    skipped = 0

    for r in rows:
        (legacy_id, article_id, qnum, qtype, qtext, a, b, c, d, correct, explanation, created_at) = r

        # Check if question already exists (idempotent)
        cur.execute('SELECT question_id FROM questions WHERE article_id = ? AND question_text = ?', (article_id, qtext))
        exists = cur.fetchone()
        if exists:
            skipped += 1
            continue

        print(f"Migrating quiz id={legacy_id} article={article_id} q#={qnum}")

        if apply:
            # Insert question
            cur.execute('INSERT INTO questions (article_id, difficulty_id, question_text, created_at, question_number) VALUES (?, NULL, ?, ?, ?)', (article_id, qtext, created_at, qnum))
            question_id = cur.lastrowid

            # Insert choices
            opts = [(a, 'A'), (b, 'B'), (c, 'C'), (d, 'D')]
            for text, letter in opts:
                if not text:
                    continue
                is_correct = 1 if (correct and correct.strip().upper().startswith(letter)) else 0
                cur.execute('INSERT INTO choices (question_id, choice_text, is_correct, explanation, created_at) VALUES (?, ?, ?, ?, ?)', (question_id, text, is_correct, explanation if is_correct else None, created_at))

            migrated += 1

    if apply:
        conn.commit()

    print(f'Migration summary: total={len(rows)} migrated={migrated} skipped={skipped}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(DB_PATH))
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is preview)')
    args = parser.parse_args()

    db_path = pathlib.Path(args.db)
    if not db_path.exists():
        print(f'ERROR: DB not found at {db_path}')
        return

    if args.apply:
        backup_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = None

    ensure_question_number_column(conn)
    migrate(conn, apply=args.apply)

    conn.close()


if __name__ == '__main__':
    main()
