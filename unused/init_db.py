#!/usr/bin/env python3
"""Initialize articles.db from schema + data fixtures.

Creates lookup tables and inserts seed data from `init_data.json`.

Usage:
  python3 init_db.py [--force] [--db path] [--data path]

Options:
  --force    Backup and remove existing DB before recreating (destructive)
  --db PATH   Path to sqlite DB (default: articles.db)
  --data PATH Path to JSON data file (default: init_data.json)

This script is safe to re-run: it uses CREATE TABLE IF NOT EXISTS and
INSERT OR REPLACE so running twice will not duplicate rows. The --force
option deletes the DB after creating a timestamped backup and recreates
fresh tables and data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "articles.db"
DEFAULT_DATA = ROOT / "init_data.json"
BACKUP_DIR = ROOT / "backups"


def backup_db(db_path: Path) -> Path | None:
    if not db_path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dst = BACKUP_DIR / f"articles.db.backup_{ts}.sqlite"
    shutil.copy(db_path, dst)
    return dst


def create_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.executescript(
        """
        -- Full schema derived from backups/schema_snapshot_20251024.md (cleaned)

        CREATE TABLE IF NOT EXISTS article_analysis (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER NOT NULL,
            analysis_en TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS article_images (
            image_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            image_name TEXT,
            original_url TEXT,
            local_location TEXT,
            new_url TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        );

        CREATE TABLE IF NOT EXISTS article_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER,
            language_id INTEGER,
            title TEXT,
            summary TEXT,
            generated_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
            FOREIGN KEY (language_id) REFERENCES languages(language_id)
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            pub_date TEXT,
            content TEXT,
            crawled_at TEXT,
            deepseek_processed BOOLEAN DEFAULT 0,
            processed_at TEXT,
            category_id INTEGER,
            image_id INTEGER REFERENCES article_images(image_id),
            deepseek_failed INTEGER DEFAULT 0,
            deepseek_last_error TEXT,
            deepseek_in_progress INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS background_read (
            background_read_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER NOT NULL,
            background_text TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            description TEXT,
            prompt_name TEXT DEFAULT 'default',
            created_at TEXT,
            enable BOOLEAN DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS choices (
            choice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            choice_text TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT 0,
            explanation TEXT,
            created_at TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER NOT NULL,
            attitude TEXT CHECK(attitude IN ('positive', 'neutral', 'negative')),
            com_content TEXT NOT NULL,
            who_comment TEXT,
            comment_date TEXT,
            created_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS difficulty_levels (
            difficulty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            difficulty TEXT UNIQUE NOT NULL,
            meaning TEXT,
            grade TEXT
        );

        CREATE TABLE IF NOT EXISTS feeds (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_name TEXT NOT NULL,
            feed_url TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            enable BOOLEAN DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );

        CREATE TABLE IF NOT EXISTS keywords (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER,
            explanation TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            difficulty_id INTEGER,
            question_text TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS user_awards (
            award_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comments_count INTEGER DEFAULT 0,
            questions_answered_count INTEGER DEFAULT 0,
            questions_answered_correct_count INTEGER DEFAULT 0,
            articles_read_count INTEGER DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS user_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, category_id)
        );

        CREATE TABLE IF NOT EXISTS user_difficulty_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            difficulty_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
            UNIQUE(user_id, difficulty_id)
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            email_enabled BOOLEAN DEFAULT 1,
            email_frequency TEXT DEFAULT 'daily',
            subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active', 'paused', 'cancelled')),
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            token TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered BOOLEAN DEFAULT 1,
            registered_date TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS languages (
            language_id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT UNIQUE NOT NULL
        );

        -- optional catalog table (kept for backwards compatibility)
        CREATE TABLE IF NOT EXISTS catalog (
            catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_token TEXT UNIQUE NOT NULL,
            category_id INTEGER,
            enable BOOLEAN DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );

        """
    )
    conn.commit()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def insert_table_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        cols = ",".join(r.keys())
        placeholders = ",".join(["?" for _ in r])
        values = list(r.values())
        sql = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders});"
        cur.execute(sql, values)
        inserted += 1
    return inserted


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Backup and recreate DB")
    p.add_argument("--db", default=str(DEFAULT_DB), help="Path to sqlite DB")
    p.add_argument("--data", default=str(DEFAULT_DATA), help="Path to JSON seed data")
    args = p.parse_args(argv)

    db_path = Path(args.db)
    data_path = Path(args.data)

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return 2

    if db_path.exists():
        bak = backup_db(db_path)
        if bak:
            print(f"Backed up existing DB to: {bak}")
        if args.force:
            db_path.unlink()
            print(f"Removed existing DB: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        create_tables(conn)
        data = load_json(data_path)

        # Insert in an order that satisfies FK constraints
        order = ["categories", "languages", "difficulty_levels", "feeds", "catalog"]
        total = 0
        for table in order:
            rows = data.get(table, [])
            n = insert_table_rows(conn, table, rows)
            total += n
            print(f"Inserted {n} rows into {table}")
        conn.commit()
        print(f"Initialization complete — total inserted rows: {total}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
