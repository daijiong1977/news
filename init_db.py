#!/usr/bin/env python3
"""
Initialize articles.db with all required tables and populate lookup tables.
This script creates a clean, normalized database schema ready for production.
"""

import sqlite3
import pathlib
import sys
from datetime import datetime

DB_FILE = pathlib.Path("articles.db")


def init_database():
    """Create all required tables in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("INITIALIZING ARTICLES DATABASE")
    print("=" * 70)
    
    try:
        # 1. Categories table
        print("\n[1/11] Creating categories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                prompt_name TEXT DEFAULT 'default',
                created_at TEXT
            )
        """)
        print("✓ Categories table created")
        
        # 2. Feeds table
        print("[2/13] Creating feeds table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_name TEXT NOT NULL,
                feed_url TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)
        print("✓ Feeds table created")
        
        # 3. Difficulty levels table
        print("[3/13] Creating difficulty_levels table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS difficulty_levels (
                difficulty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                difficulty TEXT UNIQUE NOT NULL,
                meaning TEXT,
                grade TEXT
            )
        """)
        print("✓ Difficulty levels table created")
        
        # 4. Languages table
        print("[4/13] Creating languages table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                language_id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT UNIQUE NOT NULL
            )
        """)
        print("✓ Languages table created")
        
        # 4. Articles table
        print("[4/13] Creating articles table...")
        cursor.execute("""
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
                zh_title TEXT,
                image_id INTEGER REFERENCES article_images(image_id)
            )
        """)
        print("✓ Articles table created")
        
        # 5. Article images table
        print("[5/13] Creating article_images table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                image_name TEXT,
                original_url TEXT,
                local_location TEXT,
                new_url TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        print("✓ Article images table created")
        
        # 6. Article summaries table
        print("[6/13] Creating article_summaries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER,
                language_id INTEGER,
                summary TEXT,
                generated_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
                FOREIGN KEY (language_id) REFERENCES languages(language_id)
            )
        """)
        print("✓ Article summaries table created")
        
        # 7. Keywords table
        print("[7/13] Creating keywords table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER,
                explanation TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
        """)
        print("✓ Keywords table created")
        
        # 8. Questions table
        print("[8/13] Creating questions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER,
                question_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
        """)
        print("✓ Questions table created")
        
        # 9. Choices table
        print("[9/13] Creating choices table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS choices (
                choice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                choice_text TEXT NOT NULL,
                is_correct BOOLEAN DEFAULT 0,
                explanation TEXT,
                created_at TEXT,
                FOREIGN KEY (question_id) REFERENCES questions(question_id)
            )
        """)
        print("✓ Choices table created")
        
        # 10. Comments table (for perspectives)
        print("[10/13] Creating comments table...")
        cursor.execute("""
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
            )
        """)
        print("✓ Comments table created")
        
        # 11. Background reading table
        print("[11/13] Creating background_read table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS background_read (
                background_read_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                background_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
        """)
        print("✓ Background read table created")
        
        # 12. Article analysis table (structure and tone analysis for mid/hard)
        print("[12/13] Creating article_analysis table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                analysis_en TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
        """)
        print("✓ Article analysis table created")
        
        # 13. Users and related tables
        print("[13/13] Creating users and preference tables...")
        cursor.execute("""
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
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_difficulty_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
                UNIQUE(user_id, difficulty_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                language_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (language_id) REFERENCES languages(language_id),
                UNIQUE(user_id, language_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, category_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                email_enabled BOOLEAN DEFAULT 1,
                email_frequency TEXT DEFAULT 'daily',
                subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active', 'paused', 'cancelled')),
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_awards (
                award_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comments_count INTEGER DEFAULT 0,
                questions_answered_count INTEGER DEFAULT 0,
                questions_answered_correct_count INTEGER DEFAULT 0,
                articles_read_count INTEGER DEFAULT 0,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        print("✓ Users and preference tables created")
        
        conn.commit()
        print("\n✓ All tables created successfully!")
        
    except sqlite3.Error as e:
        print(f"\n✗ Error creating tables: {e}")
        conn.close()
        return False
    
    return conn, cursor


def populate_lookup_tables(conn, cursor):
    """Populate difficulty_levels, languages, and categories tables."""
    
    print("\n" + "=" * 70)
    print("POPULATING LOOKUP TABLES")
    print("=" * 70)
    
    try:
        # Populate difficulty levels
        print("\n[1/3] Populating difficulty_levels table...")
        difficulty_data = [
            ('easy', 'Beginner level - suitable for grades 3-5', '3-5'),
            ('mid', 'Intermediate level - suitable for grades 6-8', '6-8'),
            ('hard', 'Advanced level - suitable for grades 9-12', '9-12')
        ]
        
        for difficulty, meaning, grade in difficulty_data:
            try:
                cursor.execute("""
                    INSERT INTO difficulty_levels (difficulty, meaning, grade)
                    VALUES (?, ?, ?)
                """, (difficulty, meaning, grade))
                print(f"  ✓ Added difficulty level: {difficulty}")
            except sqlite3.IntegrityError:
                print(f"  → Difficulty level '{difficulty}' already exists")
        
        # Populate languages
        print("\n[2/3] Populating languages table...")
        language_data = [
            ('en', ),
            ('zh', )
        ]
        
        for lang, in language_data:
            try:
                cursor.execute("""
                    INSERT INTO languages (language)
                    VALUES (?)
                """, (lang,))
                print(f"  ✓ Added language: {lang}")
            except sqlite3.IntegrityError:
                print(f"  → Language '{lang}' already exists")
        
        # Populate categories
        print("\n[3/3] Populating categories table...")
        category_data = [
            ('US News', 'United States news and current events', 'default'),
            ('Swimming', 'Swimming sports and competitions', 'sports'),
            ('PBS', 'Public Broadcasting Service content', 'default'),
            ('Technology', 'Technology news and innovation', 'tech'),
            ('Science', 'Science research and discoveries', 'science'),
            ('Politics', 'Political news and analysis', 'politics'),
            ('Business', 'Business and economics', 'business'),
            ('Health', 'Health and medical news', 'health')
        ]
        
        now = datetime.now().isoformat()
        for category_name, description, prompt_name in category_data:
            try:
                cursor.execute("""
                    INSERT INTO categories (category_name, description, prompt_name, created_at)
                    VALUES (?, ?, ?, ?)
                """, (category_name, description, prompt_name, now))
                print(f"  ✓ Added category: {category_name} (prompt: {prompt_name})")
            except sqlite3.IntegrityError:
                print(f"  → Category '{category_name}' already exists")
        
        # Populate feeds table
        print("\n[4/4] Populating feeds table...")
        feeds_data = [
            ('US News', 'https://feeds.nytimes.com/services/xml/rss/nyt/US.xml', 'US News'),
            ('Swimming', 'https://www.swimmingworldmagazine.com/feed/', 'Swimming'),
            ('Technology', 'https://feeds.arstechnica.com/arstechnica/index', 'Technology'),
            ('Science', 'https://feeds.arstechnica.com/arstechnica/science', 'Science'),
            ('Politics', 'https://feeds.nytimes.com/services/xml/rss/nyt/Politics.xml', 'Politics'),
            ('PBS', 'https://www.pbs.org/newshour/feeds/rss/headlines', 'PBS')
        ]
        
        for feed_name, feed_url, category_name in feeds_data:
            try:
                # Get category_id for this feed
                cursor.execute("""
                    SELECT category_id FROM categories WHERE category_name = ?
                """, (category_name,))
                result = cursor.fetchone()
                if result:
                    category_id = result[0]
                    cursor.execute("""
                        INSERT INTO feeds (feed_name, feed_url, category_id, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (feed_name, feed_url, category_id, now))
                    print(f"  ✓ Added feed: {feed_name} -> {category_name}")
                else:
                    print(f"  ✗ Category '{category_name}' not found for feed '{feed_name}'")
            except sqlite3.IntegrityError as e:
                print(f"  → Feed '{feed_name}' already exists: {e}")
        
        conn.commit()
        print("\n✓ All lookup tables populated successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Error populating lookup tables: {e}")
        return False


def verify_database():
    """Verify database structure and accessibility."""
    
    print("\n" + "=" * 70)
    print("VERIFYING DATABASE")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if database file exists and is readable
        if not DB_FILE.exists():
            print(f"✗ Database file not found: {DB_FILE}")
            return False
        
        print(f"\n✓ Database file found: {DB_FILE}")
        print(f"  File size: {DB_FILE.stat().st_size / 1024:.1f} KB")
        
        # Get list of all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"\n✓ Database contains {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} rows")
        
        # Verify key tables exist
        required_tables = [
            'categories', 'difficulty_levels', 'languages', 'articles',
            'article_summaries', 'keywords', 'questions', 'choices',
            'comments', 'users'
        ]
        
        existing_tables = [t[0] for t in tables]
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n✗ Missing required tables: {missing_tables}")
            return False
        
        print(f"\n✓ All required tables exist")
        
        # Verify foreign key constraints
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"✓ Foreign key constraints: {'Enabled' if fk_status == 1 else 'Disabled'}")
        
        # Test write permission
        try:
            cursor.execute("""
                INSERT INTO categories (category_name, description, created_at)
                VALUES ('__test__', 'Test', ?)
            """, (datetime.now().isoformat(),))
            cursor.execute("DELETE FROM categories WHERE category_name = '__test__'")
            conn.commit()
            print("✓ Database is writable")
        except Exception as e:
            print(f"✗ Database write test failed: {e}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def main():
    """Main initialization routine."""
    
    # Check if database already exists
    if DB_FILE.exists():
        print(f"Found existing database: {DB_FILE}")
        response = input("Do you want to reinitialize? (yes/no): ").lower().strip()
        if response != 'yes':
            print("Initialization cancelled.")
            verify_database()
            return
        else:
            DB_FILE.unlink()
            print("Existing database deleted.")
    
    # Initialize database
    result = init_database()
    if not result:
        print("\n✗ Database initialization failed")
        sys.exit(1)
    
    conn, cursor = result
    
    # Populate lookup tables
    if not populate_lookup_tables(conn, cursor):
        print("\n✗ Failed to populate lookup tables")
        conn.close()
        sys.exit(1)
    
    conn.close()
    
    # Verify database
    if not verify_database():
        print("\n✗ Database verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ DATABASE INITIALIZATION COMPLETE")
    print("=" * 70)
    print("\nDatabase is ready for production deployment!")
    print(f"Database location: {DB_FILE.absolute()}")


if __name__ == "__main__":
    main()
