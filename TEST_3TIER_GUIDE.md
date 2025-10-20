# 🧪 Test DeepSeek 3-Tier Content Generation

## What This Does

Generates 3-tier personalized content for ONE article using DeepSeek API:

1. **Loads Article**: Uses article ID 6 (swimming)
2. **Sends to DeepSeek**: Single batch prompt for all 3 levels
3. **Stores in Database**: Saves all content and questions
4. **Generates 3 HTML Files**:
   - `article_6_elementary.html` - Simplified layout
   - `article_6_middle.html` - Standard layout with arguments
   - `article_6_high.html` - Standard layout with arguments

## Prerequisites

```bash
# 1. Set DeepSeek API key
export DEEPSEEK_API_KEY='your-api-key-here'

# 2. Verify Python is available
python3 --version

# 3. Verify Flask is running (port 5001)
curl http://localhost:5001/health
```

## Run the Test

```bash
cd /Users/jidai/news

# Make script executable
chmod +x test_deepseek_3tier.py

# Run it
python3 test_deepseek_3tier.py
```

## Expected Output

```
======================================================================
🚀 DEEPSEEK 3-TIER CONTENT GENERATION TEST
======================================================================

Step 1: Initializing database...
✅ Database initialized

Step 2: Loading article...
✅ Loaded: [Article Title]

Step 3: Generating DeepSeek prompt...
✅ Prompt created (XXXX characters)

Step 4: Calling DeepSeek API (this may take a minute)...
🔄 Calling DeepSeek API...
✅ DeepSeek response received and parsed

Step 5: Storing content in database...
✅ Content stored in database

Step 6: Retrieving content from database...
✅ Content retrieved

Step 7: Generating HTML files...
✅ article_6_elementary.html created
✅ article_6_middle.html created
✅ article_6_high.html created

======================================================================
✅ SUCCESS! Generated 3 HTML files
======================================================================

📂 View the generated files:
   Elementary: file:///Users/jidai/news/article_6_elementary.html
   Middle:     file:///Users/jidai/news/article_6_middle.html
   High:       file:///Users/jidai/news/article_6_high.html

💾 Data stored in database:
   Location: /Users/jidai/news/subscriptions.db
   Tables: article_summaries, quiz_questions
```

## View the Results

### Option 1: Open in Browser
```bash
# Open each file in your browser
open file:///Users/jidai/news/article_6_elementary.html
open file:///Users/jidai/news/article_6_middle.html
open file:///Users/jidai/news/article_6_high.html
```

### Option 2: Via HTTP Server (if running)
```bash
# If http.server is running on port 8000
http://localhost:8000/article_6_elementary.html
http://localhost:8000/article_6_middle.html
http://localhost:8000/article_6_high.html
```

## Verify Database Storage

```bash
# Check what was stored
sqlite3 /Users/jidai/news/subscriptions.db

# List all summaries
SELECT article_id, difficulty, language, LENGTH(summary) as words FROM article_summaries;

# List all questions
SELECT article_id, difficulty, question_number, question_text FROM quiz_questions LIMIT 10;

# Count by difficulty
SELECT difficulty, COUNT(*) as count FROM article_summaries GROUP BY difficulty;
```

## What You'll See

### Elementary Layout
```
┌─────────────────────────────────┐
│ 📚 Elementary Level (Grades 3-5)│
├─────────────────────────────────┤
│ 📖 What You Should Know         │
│ [100-200 word simple summary]   │
├─────────────────────────────────┤
│ 🎯 Key Topics                   │
│ [Simple keywords]               │
├─────────────────────────────────┤
│ ❓ Let's Check What You Learned │
│ [5 Easy Questions with Answers] │
└─────────────────────────────────┘

EXCLUDES: Background, Arguments, Link
```

### Middle School Layout
```
┌─────────────────────────────────┐
│ 📚 Middle School (Grades 6-8)   │
├─────────────────────────────────┤
│ 📖 Article Summary              │
│ [300-500 word medium summary]   │
├─────────────────────────────────┤
│ 🎯 Key Topics                   │
│ [Standard keywords]             │
├─────────────────────────────────┤
│ 📚 Background Information       │
│ [Context paragraph]             │
├─────────────────────────────────┤
│ 💭 Different Perspectives       │
│ ✅ Supporting Arguments         │
│ ❌ Counter Arguments            │
├─────────────────────────────────┤
│ ❓ Check Your Understanding     │
│ [5 Medium Questions with Answers]│
└─────────────────────────────────┘

INCLUDES: Background, Arguments, Link
```

### High School Layout
```
┌─────────────────────────────────┐
│ 📚 High School (Grades 9-12)    │
├─────────────────────────────────┤
│ 📖 In-Depth Analysis            │
│ [500-700 word detailed summary] │
├─────────────────────────────────┤
│ 🎯 Key Concepts                 │
│ [Detailed keywords]             │
├─────────────────────────────────┤
│ 📚 Historical & Contextual...   │
│ [Deep context paragraph]        │
├─────────────────────────────────┤
│ 🔬 Critical Analysis            │
│ ✅ Supporting Arguments (detailed)
│ ❌ Counter Arguments (detailed) │
├─────────────────────────────────┤
│ ❓ Advanced Comprehension...    │
│ [5 Hard Analysis Questions]     │
└─────────────────────────────────┘

INCLUDES: Background, Arguments, Link
```

## Troubleshooting

### Error: "DEEPSEEK_API_KEY not set"
```bash
export DEEPSEEK_API_KEY='sk-...'
```

### Error: "Article not found"
- Script uses article ID 6
- Verify `articles_data_with_summaries.json` contains article 6
- Check file path: `/Users/jidai/news/articles_data_with_summaries.json`

### Error: "DeepSeek error: 401"
- API key is invalid or incorrect
- Get new key from DeepSeek console

### Error: "Database error"
- Check database path: `/Users/jidai/news/subscriptions.db`
- Ensure write permissions to `/Users/jidai/news/`

### Timeout Error
- DeepSeek might be slow (can take 30-60 seconds)
- Try again after a few minutes

### JSON Parse Error
- DeepSeek response might not be valid JSON
- Check script output for response preview
- Verify API key and prompt structure

## Next Steps

After successful test:

1. **Review the 3 HTML files** - Open in browser, verify content quality
2. **Verify database storage** - Run sqlite3 queries above
3. **Compare layouts** - Check differences between elementary/middle/high
4. **Check content quality** - Does DeepSeek provide good summaries?
5. **Adjust prompts** - If needed, modify prompt in script and rerun

## Script Features

✅ **Single DeepSeek Request**
- One API call generates all 3 levels
- More efficient, consistent responses

✅ **Database Storage**
- Stores summaries (all 3 levels, both languages)
- Stores quiz questions (5 per level)
- Indexed by article_id and difficulty

✅ **HTML Generation**
- Styled HTML with gradient headers
- Different colors per level (purple, pink, cyan)
- Responsive design
- All content inline (no external dependencies)

✅ **Easy Comparison**
- 3 files side-by-side in file explorer
- Identical structure, different content depth
- Same article, 3 different perspectives

## Questions Answered

**Q: How long does it take?**
A: ~1-2 minutes. Most time is waiting for DeepSeek API.

**Q: Can I modify the article?**
A: Yes! Edit line in main(): `article = load_article(6)` → change 6 to any article ID

**Q: Can I re-run on same article?**
A: Script will ADD new entries (duplicates). Clean database first with: `rm subscriptions.db`

**Q: How do I get the API key?**
A: Visit https://platform.deepseek.com and get API key from console

**Q: Can I test without API key?**
A: No, but you can manually create sample content in database for testing

---

**Ready?** Set your API key and run: `python3 test_deepseek_3tier.py`
