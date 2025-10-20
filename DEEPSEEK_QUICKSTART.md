# DeepSeek Article Processor - Quick Start

## 🚀 Quick Setup (5 minutes)

### 1. Install Required Package
```bash
pip install requests
```

### 2. Initialize Database
```bash
python3 deepseek_processor.py --init
```

Output:
```
✓ Added deepseek_processed column to articles table
✓ DeepSeek tables initialized
```

### 3. Process Your First Batch
```bash
python3 deepseek_processor.py --batch-size 5
```

What happens:
- Fetches 5 unprocessed articles with full content
- Sends them to DeepSeek API in one batch
- Saves response to `deepseek_batch_1.json`
- Stores results in database
- Marks articles as processed

Output:
```
======================================================================
BATCH 1: Processing 5 articles
======================================================================
  - Article 16: This powerful drug combo cuts prostate cancer deaths...
  - Article 17: Cancer patients who got a COVID vaccine lived much...
  - Article 18: Einstein's overlooked idea could explain how...
  - Article 19: Astronomers discover a gigantic bridge of gas...
  - Article 20: A clue to ancient life? What scientists found...

📤 Sending batch 1 to DeepSeek API...
   Payload size: 45.2 KB

✓ Received response from DeepSeek (batch 1)
✓ Response saved to deepseek_batch_1.json
✓ Stored feedback for 5/5 articles
⏳ Waiting 3 seconds before next batch...
```

### 4. Retrieve Results
```bash
python3 deepseek_processor.py --query 16
```

Returns complete JSON with:
- 300-500 word English summary
- 300-500 word Chinese summary
- 10 key words with explanations
- 200-300 word background reading
- 5 multiple choice questions
- Discussion with both perspectives

## 📊 What DeepSeek Generates (Per Article)

### 1. **Summary** (English) - 300-500 words
Main points and key findings captured comprehensively

### 2. **Summary** (Chinese) - 300-500 words
Natural, idiomatic Chinese translation (not literal)

### 3. **Key Words** - Top 10 Important Terms
```json
{
  "word": "enzalutamide",
  "frequency": 6,
  "explanation": "An androgen receptor inhibitor drug that blocks..."
}
```

### 4. **Background Reading** - 200-300 words
Historical context and domain knowledge needed

### 5. **Multiple Choice Questions** - 5 Questions
- 1x Main Idea (tests core understanding)
- 1x New Word (tests vocabulary)
- 3x SAT-style (various comprehension levels)

Each with options A-D, correct answer, and explanation

### 6. **Discussion - Both Sides** - 2 Perspectives
- Perspective 1: Arguments for/supporting
- Perspective 2: Alternative arguments
- Synthesis: 200-word discussion bridging both

## 🔄 Batch Processing Examples

```bash
# Process all articles, 5 at a time
python3 deepseek_processor.py

# Process only 2 batches (10 articles)
python3 deepseek_processor.py --max-batches 2

# Process batch of 10 articles
python3 deepseek_processor.py --batch-size 10

# Process just 3 articles at a time
python3 deepseek_processor.py --batch-size 3
```

## 📁 Output Files

### Database Updates
```
articles table:
- deepseek_processed = 1 (for processed articles)

deepseek_feedback table:
- article_id (links to original article)
- summary_en (English summary)
- summary_zh (Chinese summary)
- key_words (JSON array)
- background_reading (context)
- multiple_choice_questions (JSON array)
- discussion_both_sides (JSON object)
- created_at, updated_at (timestamps)
```

### Response Files
- `deepseek_batch_1.json` - Raw API response for batch 1
- `deepseek_batch_2.json` - Raw API response for batch 2
- etc.

Useful for inspection before storing in database

## 🔍 Query Examples

```bash
# Get feedback for article 16
python3 deepseek_processor.py --query 16

# Export to file
python3 deepseek_processor.py --query 16 > article_16_analysis.json

# Use in a script
python3 << 'EOF'
from deepseek_processor import query_feedback
import json

feedback = query_feedback(16)
print(f"Summary: {feedback['summary_en'][:100]}...")
print(f"Keywords: {[kw['word'] for kw in feedback['key_words']]}")
print(f"Questions: {len(feedback['multiple_choice_questions'])} questions")
EOF
```

## 💾 Database Schema

### articles table (existing, updated)
```sql
ALTER TABLE articles ADD COLUMN deepseek_processed INTEGER DEFAULT 0;
```

### deepseek_feedback table (new)
```sql
CREATE TABLE deepseek_feedback (
    id INTEGER PRIMARY KEY,
    article_id INTEGER UNIQUE,
    summary_en TEXT,
    summary_zh TEXT,
    key_words TEXT (JSON),
    background_reading TEXT,
    multiple_choice_questions TEXT (JSON),
    discussion_both_sides TEXT (JSON),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

## ⚙️ Configuration

Edit `deepseek_processor.py` to modify:

```python
DEEPSEEK_API_KEY = "sk-0ad0e8ca48544dd79ef790d17672eed2"  # Your API key
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
```

## ⏱️ Rate Limiting

Built-in 3-second delay between batches (configurable in code)

```python
# In the script:
time.sleep(3)  # Change to desired seconds
```

## 📈 Progress Tracking

Check which articles have been processed:

```bash
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1;"
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| API Key Error | Check DEEPSEEK_API_KEY in deepseek_processor.py |
| JSON Parse Error | Check `deepseek_batch_N.json` for format issues |
| Database Error | Run `python3 deepseek_processor.py --init` again |
| Timeout | Reduce batch_size or increase timeout in requests |
| No articles found | Check that articles table has unprocessed articles |

## 🚀 Next Steps

1. **Display in Web Portal**
   - Create HTML pages showing summaries
   - Add Chinese version toggle
   - Show key words with tooltips

2. **Quiz System**
   - Use multiple choice questions for interactive quiz
   - Track user answers
   - Show explanations on wrong answers

3. **Email Integration**
   - Send summaries in email digests
   - Include 1-2 discussion points
   - Link to full analysis

4. **Mobile App**
   - Show summaries while commuting
   - Practice with questions
   - Read Chinese translations

5. **Analytics**
   - Track which articles get most engagement
   - Analyze common keywords across topics
   - Monitor discussion trends

## 📞 Support

For detailed documentation: `DEEPSEEK_SETUP.md`

For API documentation: https://api-docs.deepseek.com
