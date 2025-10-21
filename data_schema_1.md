# Data Schema v1.0

## articles.db Schema

### Table: categories
```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL,
    description TEXT,
    prompt_name TEXT DEFAULT 'default',
    created_at TEXT
);
```

### Table: articles
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    pub_date TEXT,
    image_url TEXT,
    image_local TEXT,
    content TEXT,
    crawled_at TEXT,
    deepseek_processed BOOLEAN DEFAULT 0,
    processed_at TEXT,
    category_id INTEGER,
    zh_title TEXT
);
```

### Table: difficulty_levels
```sql
CREATE TABLE difficulty_levels (
    difficulty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    difficulty TEXT UNIQUE NOT NULL,
    meaning TEXT,
    grade TEXT
);
```

### Table: languages
```sql
CREATE TABLE languages (
    language_id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT UNIQUE NOT NULL
);
```

### Table: article_summaries
```sql
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
);
```

### Table: keywords
```sql
CREATE TABLE keywords (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    article_id INTEGER NOT NULL,
    difficulty_id INTEGER,
    explanation TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
);
```

### Table: questions
```sql
CREATE TABLE questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    difficulty_id INTEGER,
    question_text TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
);
```

### Table: choices
```sql
CREATE TABLE choices (
    choice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    choice_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT 0,
    explanation TEXT,
    created_at TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);
```

### Table: comments
```sql
CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    attitude TEXT CHECK(attitude IN ('positive', 'neutral', 'negative')),
    com_content TEXT NOT NULL,
    who_comment TEXT,
    comment_date TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

### Table: users
```sql
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
);
```

### Table: user_difficulty_levels
```sql
CREATE TABLE user_difficulty_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    difficulty_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id),
    UNIQUE(user_id, difficulty_id)
);
```

### Table: user_languages
```sql
CREATE TABLE user_languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(user_id, language_id)
);
```

### Table: user_categories
```sql
CREATE TABLE user_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, category_id)
);
```

### Table: user_preferences
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT 1,
    email_frequency TEXT DEFAULT 'daily',
    subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active', 'paused', 'cancelled')),
    updated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Table: comments (Perspectives)
```sql
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
);
```
**Purpose**: Stores perspective feedback from Deepseek at each difficulty level (easy, mid, hard)
- One record per article per difficulty level (3 records per article)
- difficulty_id links to: 1=easy, 2=mid, 3=hard
- com_content stores the perspective text (perspective_1, perspective_2, or synthesis)

### Table: background_read (Background Reading)
```sql
CREATE TABLE background_read (
    background_read_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    difficulty_id INTEGER NOT NULL,
    background_text TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
);
```
**Purpose**: Stores background reading content from Deepseek at each difficulty level
- One record per article per difficulty level (3 records per article)
- difficulty_id links to: 1=easy, 2=mid, 3=hard
- background_text stores the background reading content

### Table: article_analysis (Article Structure and Tone Analysis)
```sql
CREATE TABLE article_analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    difficulty_id INTEGER NOT NULL,
    analysis_en TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id)
);
```
**Purpose**: Stores article structure and tone analysis from Deepseek for mid/hard difficulty levels
- One record per article per difficulty level (2 records per article: mid and hard only)
- difficulty_id links to: 2=mid, 3=hard
- analysis_en: ~100 word analysis of article structure and tone in English
- Includes analysis of what positions/arguments are supported vs objected to

### Table: user_awards
```sql
CREATE TABLE user_awards (
    award_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    comments_count INTEGER DEFAULT 0,
    questions_answered_count INTEGER DEFAULT 0,
    questions_answered_correct_count INTEGER DEFAULT 0,
    articles_read_count INTEGER DEFAULT 0,
    updated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## Notes
- All ID columns are auto-incrementing integers
- Foreign keys enforce referential integrity
- articles.deepseek_processed flag: 0=not processed, 1=processed
- Date columns (pub_date, crawled_at, processed_at, generated_at) use TEXT type storing ISO 8601 format (YYYY-MM-DD HH:MM:SS)
