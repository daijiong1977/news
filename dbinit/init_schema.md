# Schema snapshot — articles.db

Generated: 2025-10-24 21:00:00 UTC

This file contains the CREATE TABLE statements for `articles.db` (18 tables).

---

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

### difficulty_levels
```
CREATE TABLE difficulty_levels (
                difficulty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                difficulty TEXT UNIQUE NOT NULL,
                meaning TEXT,
                grade TEXT
            )
```

### apikey
```
CREATE TABLE apikey (
                key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                value TEXT
            )
```

### articles
```
CREATE TABLE articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                pub_date TEXT,
                content TEXT,
                crawled_at TEXT,
                deepseek_processed BOOLEAN DEFAULT 0,
                deepseek_failed INTEGER DEFAULT 0,
                deepseek_last_error TEXT,
                deepseek_in_progress INTEGER DEFAULT 0,
                processed_at TEXT,
                category_id INTEGER,
                zh_title TEXT,
                image_id INTEGER REFERENCES article_images(image_id)
            )
```

### article_images
```
CREATE TABLE article_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                image_name TEXT,
                original_url TEXT,
                local_location TEXT,
                small_location TEXT,
                new_url TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
```

### article_summaries
```
CREATE TABLE article_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                difficulty_id INTEGER,
                summary TEXT,
                generated_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
```

### keywords
```
CREATE TABLE keywords (
                word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                article_id TEXT NOT NULL,
                difficulty_id INTEGER,
                explanation TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
```

### questions
```
CREATE TABLE questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                difficulty_id INTEGER,
                question_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
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
                article_id TEXT NOT NULL,
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

### background_read
```
CREATE TABLE background_read (
                background_read_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                difficulty_id INTEGER NOT NULL,
                background_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
            )
```

### article_analysis
```
CREATE TABLE article_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                difficulty_id INTEGER NOT NULL,
                analysis_en TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id),
                FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
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

### response
```
CREATE TABLE response (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                respons_file TEXT,
                payload_generated INTEGER DEFAULT 0,
                payload_generated_at TEXT,
                payload_directory TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
```

**Migration Notes (2025-10-26):**
- Added `payload_generated` - Flag to track if JSON payloads have been generated (0=not generated, 1=generated)
- Added `payload_generated_at` - Timestamp when payloads were last generated
- Added `payload_directory` - Path to the payload directory (e.g., 'payload_2025102501')

````

### user_subscriptions
```
CREATE TABLE user_subscriptions (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                reading_style TEXT CHECK(reading_style IN ('relax', 'enjoy', 'research', 'chinese')),
                bootstrap_token TEXT,
                bootstrap_failed INTEGER DEFAULT 0,
                subscription_status TEXT DEFAULT 'pending' CHECK(subscription_status IN ('pending', 'active', 'cancelled')),
                verified INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
```

**Purpose:** Email newsletter subscription management with emailapi bootstrap integration

**Migration Notes (2025-10-26):**
- New table for user subscription system
- `reading_style` matches frontend dropdown options (relax/enjoy/research/chinese)
- `bootstrap_token` stores API key from emailapi.6ray.com/client/bootstrap
- `bootstrap_failed` flags when emailapi is unavailable (fallback to local token)
- `verified` tracks email verification status (0=pending, 1=verified)

### user_stats_sync
```
CREATE TABLE user_stats_sync (
                user_id TEXT PRIMARY KEY,
                stats_json TEXT NOT NULL,
                last_sync INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user_subscriptions(user_id)
            )
```

**Purpose:** Optional cloud backup of user activity statistics (localStorage primary, DB secondary)

**Migration Notes (2025-10-26):**
- New table for user-initiated stats synchronization
- `stats_json` stores complete activity data as JSON (words completed, quiz scores, etc.)
- `last_sync` tracks when user last manually synced their data
- Data stored in browser localStorage primarily, this table is backup only
- Minimal server load: sync only when user clicks "Sync" button
