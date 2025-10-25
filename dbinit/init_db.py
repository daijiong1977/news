#!/usr/bin/env python3
"""Database initializer for articles.db.

Creates a clean database from schema defined in init_schema.md and populates
lookup tables from init_data.json. Supports --force to backup and recreate.

Usage:
    python3 dbinit/init_db.py [--force]

With --force:
    1. Backs up existing articles.db to backups/
    2. Deletes existing articles.db
    3. Creates new database with clean schema
    4. Populates lookup tables from init_data.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT / "articles.db"
BACKUP_DIR = ROOT / "backups"
SCHEMA_PATH = SCRIPT_DIR / "init_schema.md"
DATA_PATH = SCRIPT_DIR / "init_data.json"


def backup_db(db_path: Path, backup_dir: Path) -> Path:
    """Create timestamped backup of database"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = backup_dir / f"articles.db.backup_{ts}.sqlite"
    if db_path.exists():
        shutil.copy(db_path, dst)
    return dst


def extract_create_statements(schema_md: str) -> list[str]:
    """Extract CREATE TABLE statements from markdown code blocks"""
    statements = []
    # Find all markdown code blocks with CREATE TABLE
    pattern = r'```\s*\n(CREATE TABLE.*?)\n```'
    matches = re.findall(pattern, schema_md, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        stmt = match.strip()
        if stmt.lower().startswith('create table'):
            statements.append(stmt)
    
    return statements


def create_schema_from_markdown(conn: sqlite3.Connection, schema_path: Path) -> int:
    """Read CREATE TABLE statements from markdown file and create tables"""
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        return 0
    
    with open(schema_path, 'r') as f:
        schema_md = f.read()
    
    statements = extract_create_statements(schema_md)
    cur = conn.cursor()
    count = 0
    
    for stmt in statements:
        # Use CREATE TABLE IF NOT EXISTS for idempotency
        if 'IF NOT EXISTS' not in stmt:
            stmt = stmt.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS', 1)
        try:
            cur.execute(stmt)
            count += 1
        except sqlite3.Error as e:
            print(f"Warning: Failed to create table: {e}")
    
    conn.commit()
    return count


def load_seed_data(data_path: Path) -> dict:
    """Load seed data from JSON file"""
    if not data_path.exists():
        return {}
    
    with open(data_path, 'r') as f:
        return json.load(f)


def insert_seed_data(conn: sqlite3.Connection, seed_data: dict) -> int:
    """Insert seed data into lookup tables"""
    cur = conn.cursor()
    total_inserted = 0
    
    for table_name, rows in seed_data.items():
        if not isinstance(rows, list):
            continue
        
        for row in rows:
            if not isinstance(row, dict):
                continue
            
            cols = list(row.keys())
            placeholders = ','.join(['?' for _ in cols])
            values = [row[col] for col in cols]
            
            sql = f"INSERT OR REPLACE INTO {table_name} ({','.join(cols)}) VALUES ({placeholders})"
            try:
                cur.execute(sql, values)
                total_inserted += 1
            except sqlite3.Error as e:
                print(f"Warning: Failed to insert into {table_name}: {e}")
    
    conn.commit()
    return total_inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Delete existing DB after backup and recreate schema")
    args = parser.parse_args(argv)

    # Backup existing DB if present
    if DB_PATH.exists():
        dst = backup_db(DB_PATH, BACKUP_DIR)
        print(f"✓ Created DB backup: {dst}")
        if args.force:
            DB_PATH.unlink()
            print(f"✓ Removed existing {DB_PATH.name}")

    # Create new database with schema
    conn = sqlite3.connect(DB_PATH)
    try:
        # Create all tables from markdown schema
        tables_created = create_schema_from_markdown(conn, SCHEMA_PATH)
        print(f"✓ Created {tables_created} tables from schema")
        
        # Load and insert seed data
        seed_data = load_seed_data(DATA_PATH)
        if seed_data:
            rows_inserted = insert_seed_data(conn, seed_data)
            print(f"✓ Inserted {rows_inserted} seed rows")
        
        print("✓ Database initialization complete")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
