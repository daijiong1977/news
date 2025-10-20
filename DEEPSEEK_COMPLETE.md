# DeepSeek Article Processing System - Complete Guide

## 📋 What You're Getting

A complete system to enhance your news articles with AI-powered analysis using DeepSeek API:

### 6 Analytical Components per Article

1. **English Summary** (300-500 words)
   - Comprehensive overview of article main points
   - Professional summary style

2. **Chinese Summary** (300-500 words)
   - Natural, idiomatic Chinese translation
   - For international/Chinese-speaking audience

3. **Key Words** (Top 10 Terms)
   - Genuinely important/infrequent terms (not common words)
   - For each: frequency count + 50-100 word explanation
   - Builds vocabulary and understanding

4. **Background Reading** (200-300 words)
   - Historical context and domain knowledge
   - Helps readers unfamiliar with topic understand
   - Provides foundation for comprehension

5. **Multiple Choice Questions** (5 Questions)
   - 1x Main Idea (tests core understanding)
   - 1x New Word (tests vocabulary/terminology)
   - 3x SAT-style (varying difficulty levels)
   - Each with options A-D, correct answer, explanation
   - Ready for quiz/study tools

6. **Discussion - Both Sides** (500-700 words)
   - Perspective 1: Arguments supporting one view
   - Perspective 2: Alternative arguments
   - Synthesis: 200-word bridge discussing tension
   - Shows nuance and complexity

---

## 🚀 Getting Started

### Step 1: Install Dependencies
```bash
pip install requests
```

### Step 2: Initialize Database
```bash
python3 deepseek_processor.py --init
```

This creates:
- `deepseek_processed` column in articles table (tracks completion)
- `deepseek_feedback` table (stores all 6 components)

### Step 3: Start Processing
```bash
python3 deepseek_processor.py --batch-size 5
```

This will:
- Fetch 5 unprocessed articles with full content
- Send to DeepSeek API in one batch
- Parse response and store in database
- Mark articles as processed
- Save raw response to `deepseek_batch_1.json` for inspection
- Wait 3 seconds before next batch

### Step 4: Retrieve Results
```bash
python3 deepseek_processor.py --query 16
```

Returns complete JSON with all 6 analytical components

---

## 📊 Database Structure

### Before Processing
```
articles table:
- id, title, source, link, content_file, image_file, snippet
- NEW: deepseek_processed (0 = not processed, 1 = processed)
```

### After Processing
```
deepseek_feedback table:
- article_id (links to original article)
- summary_en (300-500 word English summary)
- summary_zh (300-500 word Chinese summary)
- key_words (JSON: [{word, frequency, explanation}, ...])
- background_reading (200-300 word context)
- multiple_choice_questions (JSON: 5 questions with options/answers)
- discussion_both_sides (JSON: perspective_1, perspective_2, synthesis)
- created_at, updated_at (timestamps)
```

---

## 💻 The Prompt Strategy

The prompt sent to DeepSeek is specifically designed to generate:

1. **High-quality summaries** through detailed instructions for length and style
2. **Natural Chinese** by emphasizing idiomatic translation, not literal
3. **Meaningful keywords** by excluding common words and emphasizing importance
4. **Contextual background** by specifying domain knowledge for beginners
5. **Academic questions** through SAT/AP-level difficulty specifications
6. **Balanced perspectives** by requesting substantive arguments for both sides

See `DEEPSEEK_PROMPT_TEMPLATE.md` for exact prompt text.

---

## 📁 Files Provided

### Python Scripts
- **deepseek_processor.py** (330 lines)
  - Main processing engine
  - Handles API communication
  - Database storage
  - Batch management

### Documentation
- **DEEPSEEK_QUICKSTART.md** - Quick start guide (5 minute setup)
- **DEEPSEEK_SETUP.md** - Detailed setup and troubleshooting
- **DEEPSEEK_PROMPT_TEMPLATE.md** - Exact prompt structure
- **DEEPSEEK_COMPLETE.md** - This file

---

## 🔄 Processing Workflow

```
1. Initialize Database
   python3 deepseek_processor.py --init
   
2. Get Unprocessed Articles
   Query articles WHERE deepseek_processed = 0
   Limit to batch_size (default: 5)
   
3. Read Full Content
   Load article content from content_file
   Prepare JSON batch with id, title, content, etc.
   
4. Create Prompt
   Embed articles in comprehensive prompt
   Specify all 6 analytical requirements
   
5. Send to DeepSeek API
   POST request with Bearer token authentication
   Wait for response
   
6. Parse Response
   Extract JSON array from response
   Validate structure
   
7. Store in Database
   Insert into deepseek_feedback table
   Update articles.deepseek_processed = 1
   
8. Save Response File
   Save to deepseek_batch_N.json for inspection
   
9. Rate Limiting
   Wait 3 seconds before next batch
   
10. Repeat
    Loop until all articles processed
```

---

## 📈 Usage Examples

### Process All Articles in Batches of 5
```bash
python3 deepseek_processor.py --batch-size 5
```

### Process Only 2 Batches (10 articles)
```bash
python3 deepseek_processor.py --batch-size 5 --max-batches 2
```

### Process with Larger Batches
```bash
python3 deepseek_processor.py --batch-size 10
```

### Get Feedback for Single Article
```bash
python3 deepseek_processor.py --query 16
```

### Export to JSON File
```bash
python3 deepseek_processor.py --query 16 > article_16_feedback.json
```

### Import in Python Script
```python
from deepseek_processor import query_feedback
import json

feedback = query_feedback(16)
print(f"Summary: {feedback['summary_en']}")
print(f"Keywords: {[kw['word'] for kw in feedback['key_words']]}")
print(f"Questions: {len(feedback['multiple_choice_questions'])}")
```

---

## ✅ Quality Checklist

After processing, verify:

- [ ] Each article has both English and Chinese summaries (300-500 words)
- [ ] Keywords exclude common words and focus on domain-specific terms
- [ ] Background reading provides enough context for newcomers
- [ ] Multiple choice questions have good difficulty variation
- [ ] Discussion perspectives are substantive and balanced
- [ ] All JSON is valid and parseable
- [ ] Database table has matching record count with processed articles

---

## 🔍 Monitoring & Tracking

### Check Processing Status
```bash
# How many articles processed so far?
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1;"

# How many remaining?
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0;"

# Which articles were processed?
sqlite3 articles.db "SELECT id, title FROM articles WHERE deepseek_processed = 1 ORDER BY id;"
```

### Inspect Raw Responses
```bash
# Check first batch response
cat deepseek_batch_1.json | python3 -m json.tool | head -50

# Validate JSON format
python3 -m json.tool < deepseek_batch_1.json > /dev/null && echo "Valid JSON"
```

### Database Queries
```bash
# Get all feedback for article 16
sqlite3 articles.db "SELECT * FROM deepseek_feedback WHERE article_id = 16;"

# Count feedback records
sqlite3 articles.db "SELECT COUNT(*) FROM deepseek_feedback;"

# Check for processing errors
sqlite3 articles.db "SELECT a.id FROM articles a LEFT JOIN deepseek_feedback df ON a.id = df.article_id WHERE a.deepseek_processed = 1 AND df.article_id IS NULL;"
```

---

## 🛠️ Configuration & Customization

### API Settings (in deepseek_processor.py)
```python
DEEPSEEK_API_KEY = "sk-0ad0e8ca48544dd79ef790d17672eed2"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
```

### Model Parameters
```python
payload = {
    "model": "deepseek-chat",           # Model to use
    "temperature": 0.7,                 # Creativity: 0-1 (0.7 recommended)
    "max_tokens": 8000,                 # Max response length
}
```

### Rate Limiting (in process_articles_in_batches)
```python
time.sleep(3)  # Change to desired seconds between batches
```

### Batch Size
```bash
python3 deepseek_processor.py --batch-size 10  # Change from default 5
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Verify DEEPSEEK_API_KEY in script |
| "No articles found" | Run `--init` first, check articles table |
| "JSON decode error" | Check `deepseek_batch_N.json`, might be API error |
| "Table already exists" | Error is expected if running `--init` multiple times |
| "Timeout error" | Try smaller batch_size or increase timeout |
| "SSL certificate error" | Update certificates: `pip install --upgrade certifi` |

---

## 📊 Output Examples

### Query Single Article
```bash
$ python3 deepseek_processor.py --query 16

{
  "article_id": 16,
  "summary_en": "Men whose prostate cancer returns after surgery or radiation therapy...",
  "summary_zh": "前列腺癌患者术后或放疗后复发面临有限的治疗选择...",
  "key_words": [
    {
      "word": "enzalutamide",
      "frequency": 6,
      "explanation": "An androgen receptor inhibitor drug that blocks the effects of male hormones..."
    },
    ...
  ],
  "background_reading": "Prostate cancer remains one of the most common cancers in men...",
  "multiple_choice_questions": [
    {
      "question": "What is the main finding of the study?",
      "options": ["...", "...", "...", "..."],
      "correct_answer": "A",
      "explanation": "The study showed a 40.3% reduction in mortality risk...",
      "type": "main_idea"
    },
    ...
  ],
  "discussion_both_sides": {
    "perspective_1": {
      "title": "Support for Aggressive Early Treatment",
      "arguments": ["The 40.3% mortality reduction is substantial...", "..."]
    },
    "perspective_2": {
      "title": "Concerns About Over-treatment",
      "arguments": ["Not all biochemical recurrence becomes metastatic...", "..."]
    },
    "synthesis": "This study presents compelling evidence..."
  }
}
```

---

## 🚀 Integration Ideas

### 1. Email Digest
- Include English or Chinese summary
- Add 1-2 discussion points for deeper engagement

### 2. Web Portal
- Display all components per article
- Interactive question quiz
- Toggle between English/Chinese
- Highlight key words with tooltips

### 3. Mobile App
- Summaries for quick reading
- Questions for study/quiz mode
- Chinese version for language learning

### 4. Study Platform
- Full article content + summary
- Questions with instant feedback
- Explanation on wrong answers
- Progress tracking

### 5. Internal Documentation
- Summarize industry/research articles
- Generate training materials
- Create knowledge base

---

## 📞 Support & Resources

- **API Documentation**: https://api-docs.deepseek.com
- **Status**: Check `deepseek_batch_N.json` for raw API responses
- **Database**: `articles.db` with `deepseek_feedback` table

---

## ✨ Key Features

✅ **Batch Processing**: Handle multiple articles efficiently
✅ **Database Integration**: Automatic storage and tracking
✅ **Bilingual**: English + Chinese analysis
✅ **Educational**: Questions and background for learning
✅ **Balanced**: Multiple perspectives on complex issues
✅ **Traceable**: Know which articles have been processed
✅ **Recoverable**: Raw responses saved for inspection
✅ **Scalable**: Process hundreds of articles over time
✅ **Flexible**: Query individual results or batch export
✅ **Well-documented**: Complete setup and usage guides

---

## 🎯 Next Steps

1. **Install**: `pip install requests`
2. **Initialize**: `python3 deepseek_processor.py --init`
3. **Process**: `python3 deepseek_processor.py --batch-size 5`
4. **Monitor**: Check `deepseek_batch_1.json` for results
5. **Query**: `python3 deepseek_processor.py --query 16` to see full analysis
6. **Integrate**: Build UI/email templates to display results
7. **Scale**: Process all remaining articles in batches

---

## 📝 Version Info

- **Created**: October 2025
- **Status**: Production Ready
- **Python**: 3.8+
- **Dependencies**: `requests` library
- **Database**: SQLite3

---

Enjoy your AI-enhanced article analysis! 🎉
