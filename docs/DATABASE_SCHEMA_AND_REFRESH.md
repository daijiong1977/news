# Database schema snapshot and refresh instructions

Generated: 2025-10-21

This document captures the current `articles.db` schema (CREATE TABLE
statements), a quick table row-count summary, and safe commands to
refresh and repopulate lookup data (feeds, categories, catalog tokens).

## 1) Schema (CREATE TABLE statements)

Below are the CREATE statements for each non-internal table in the
database as of this snapshot.

---

### article_analysis
```
CREATE TABLE article_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                analysis_en TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
)
```

### article_images
```
CREATE TABLE article_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                image_name TEXT,
                original_url TEXT,
                local_location TEXT,
                new_url TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
)
```

### article_summaries
```
CREATE TABLE article_summaries (
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
```

### articles
```
CREATE TABLE articles (
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
```

### background_read
```
CREATE TABLE background_read (
                background_read_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                background_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
)
```

### catalog
```
CREATE TABLE catalog (
                catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_token TEXT UNIQUE NOT NULL,
                category_id INTEGER,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
)
```

### categories
```
CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                prompt_name TEXT DEFAULT 'default',
                created_at TEXT
)
```

### choices
```
CREATE TABLE choices (
                choice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                choice_text TEXT NOT NULL,
                is_correct BOOLEAN DEFAULT 0,
                explanation TEXT,
                created_at TEXT,
                FOREIGN KEY (question_id) REFERENCES questions(question_id)
)
```

### comments
```
CREATE TABLE comments (
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
```

### deepseek_feedback
```
CREATE TABLE deepseek_feedback (
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
```

### difficulty_levels
```
CREATE TABLE difficulty_levels (
                difficulty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                difficulty TEXT UNIQUE NOT NULL,
                meaning TEXT,
                grade TEXT
)
```

### feeds
```
CREATE TABLE feeds (
                feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_name TEXT NOT NULL,
                feed_url TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                enable BOOLEAN DEFAULT 1,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
)
```

### keywords
```
CREATE TABLE keywords (
                word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER,
                explanation TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
)
```

### languages
```
CREATE TABLE languages (
                language_id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT UNIQUE NOT NULL
)
```

### questions
```
CREATE TABLE questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                difficulty_id INTEGER,
                question_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
)
```

### user_awards
```
CREATE TABLE user_awards (
                award_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comments_count INTEGER DEFAULT 0,
                questions_answered_count INTEGER DEFAULT 0,
                questions_answered_correct_count INTEGER DEFAULT 0,
                articles_read_count INTEGER DEFAULT 0,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

### user_categories
```
CREATE TABLE user_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, category_id)
)
```

### user_difficulty_levels
```
CREATE TABLE user_difficulty_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                difficulty_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
                UNIQUE(user_id, difficulty_id)
)
```

### user_languages
```
CREATE TABLE user_languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                language_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (language_id) REFERENCES languages(language_id),
                UNIQUE(user_id, language_id)
)
```

### user_preferences
```
CREATE TABLE user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                email_enabled BOOLEAN DEFAULT 1,
                email_frequency TEXT DEFAULT 'daily',
                subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active', 'paused', 'cancelled')),
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

### users
```
CREATE TABLE users (
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
```

---

## 2) Table row counts (current snapshot)

```
article_analysis: 0
article_images: 0
article_summaries: 0
articles: 0
background_read: 0
catalog: 6
categories: 6
choices: 0
comments: 0
deepseek_feedback: 0
difficulty_levels: 3
feeds: 13
keywords: 0
languages: 2
questions: 0
user_awards: 0
user_categories: 0
user_difficulty_levels: 0
user_languages: 0
user_preferences: 0
users: 0
```

## 3) Safe refresh and populate instructions

This section provides the exact commands to safely reinitialize the
database and repopulate lookup data (feeds/categories) using the repo's
tools. All steps create local backups under `backups/` first.

1. Reinitialize the database (backups created automatically):

```bash
# creates a timestamped backup under backups/ and recreates schema
python3 init_db.py --force
```

2. Repopulate the `feeds` table from the canonical verified feeds file:

```bash
python3 scripts/repopulate_feeds_from_verified.py
```

3. Verify DB structure and counts (quick):

```bash
sqlite3 -header -csv articles.db "SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
sqlite3 -header -csv articles.db "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;" | xargs -I{} sqlite3 articles.db "SELECT '{}', COUNT(*) FROM {}"
```

Notes and safety reminders
- The `--force` flag in `init_db.py` will delete the existing `articles.db`
  after creating a backup in `backups/`.
- Backups are local-only. See `docs/GROUND_RULES.md` and ensure you do not
  commit `backups/` or `articles.db` to version control.

## 4) Where to find the canonical feed config

- `config/verified_feeds.dm` — authoritative seed used by `init_db.py` and
  `scripts/repopulate_feeds_from_verified.py`.

---

If you'd like, I can add a one-liner script to show the latest backup file
and its size, or implement a cleanup tool to prune backups older than N days.
