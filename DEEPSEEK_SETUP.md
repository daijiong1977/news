# DeepSeek Article Processing System

## Overview
This system uses the DeepSeek API to process your news articles with advanced analysis including summaries, translations, key terms, background reading, study questions, and discussion of multiple perspectives.

## Setup

### 1. Install Required Package
```bash
pip install requests
```

### 2. Initialize Database Tables
```bash
python3 deepseek_processor.py --init
```

This will:
- Add `deepseek_processed` column to the `articles` table to track which articles have been analyzed
- Create a new `deepseek_feedback` table to store the DeepSeek analysis

## Features

### For Each Article, DeepSeek Will Generate:

#### 1. **Summary (English)** - 300-500 words
- Comprehensive summary of the article
- Captures main points and key findings

#### 2. **Summary (Chinese)** - 300-500 words
- Natural, idiomatic Chinese translation of the English summary
- Not a literal translation, but maintains meaning

#### 3. **Key Words** - Top 10 Important Terms
- Identifies genuinely important/infrequent keywords (not common words)
- For each keyword:
  - Frequency count
  - 50-100 word explanation in context

#### 4. **Background Reading** - 200-300 words
- Historical context or domain knowledge
- Helps readers understand the topic without prior expertise
- Foundation for understanding the article

#### 5. **Multiple Choice Questions** - 5 Questions
- **1 Main Idea Question**: Tests understanding of article's core point
- **1 New Word Question**: Tests vocabulary/terminology from the article
- **3 SAT-Style Questions**: Various comprehension and inference questions
- Each question includes explanation of correct answer

#### 6. **Discussion - Both Sides** - 500-700 words total
- **Perspective 1**: Arguments supporting one viewpoint (1-2 arguments)
- **Perspective 2**: Alternative viewpoint with 1-2 supporting arguments
- **Synthesis**: 200-word discussion of the tension between perspectives

## Usage

### Option 1: Process Articles in Batches (Recommended)
```bash
# Process all unprocessed articles, 5 at a time
python3 deepseek_processor.py --batch-size 5

# Process only 2 batches (10 articles)
python3 deepseek_processor.py --batch-size 5 --max-batches 2
```

### Option 2: Query Existing Feedback
```bash
# Get all feedback for article ID 1
python3 deepseek_processor.py --query 1
```

## Output

### Response Files
- Each batch response is saved as `deepseek_batch_N.json` for inspection
- Contains raw API response before database storage

### Database Storage
- All feedback stored in `deepseek_feedback` table
- Linked to original articles via `article_id`
- Articles marked with `deepseek_processed = 1` after successful processing

## Data Structure

### Articles Table Update
```
deepseek_processed INTEGER (0 = not processed, 1 = processed)
```

### DeepSeek Feedback Table
```
{
  article_id: INTEGER,
  summary_en: TEXT,
  summary_zh: TEXT,
  key_words: JSON (array of keyword objects),
  background_reading: TEXT,
  multiple_choice_questions: JSON (array of question objects),
  discussion_both_sides: JSON (object with perspectives),
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP
}
```

## Example Query Output

```json
{
  "article_id": 1,
  "summary_en": "300-500 word English summary...",
  "summary_zh": "300-500 word Chinese summary...",
  "key_words": [
    {
      "word": "enzalutamide",
      "frequency": 5,
      "explanation": "An androgen receptor inhibitor drug used in prostate cancer treatment..."
    },
    ...
  ],
  "background_reading": "200-300 word background on the topic...",
  "multiple_choice_questions": [
    {
      "question": "What was the main finding of this study?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "...",
      "type": "main_idea"
    },
    ...
  ],
  "discussion_both_sides": {
    "perspective_1": {
      "title": "Support for the research",
      "arguments": ["...", "..."]
    },
    "perspective_2": {
      "title": "Concerns about the findings",
      "arguments": ["...", "..."]
    },
    "synthesis": "..."
  }
}
```

## Processing Workflow

1. **Initialize**: Run `--init` to create tables
2. **Batch Process**: Run main command to process articles
3. **Monitor**: Check `deepseek_batch_N.json` files for raw responses
4. **Query**: Use `--query` to retrieve processed data
5. **Display**: Integrate results into your digest/portal

## Tips

- Process in batches of 5-10 articles (API cost/rate limiting considerations)
- Check response files before relying on database data
- Chinese summaries should be natural, not mechanical translations
- Key words should exclude common English words (the, is, and, etc.)
- Multiple choice questions should vary in difficulty level

## Rate Limiting

- Built-in 3-second delay between batches to avoid API rate limits
- Adjust if needed based on your DeepSeek API tier

## Troubleshooting

**API Key Error**: Verify `DEEPSEEK_API_KEY` in the script
**JSON Parse Error**: Check `deepseek_batch_N.json` for response format issues
**Database Errors**: Run `--init` again to ensure tables exist
**Timeout**: Increase timeout in requests or reduce batch size

## Next Steps

After processing articles:
1. Create a view or endpoint to display the feedback
2. Integrate into your HTML digest or web portal
3. Use summaries for email previews
4. Create a quiz/study tool using the multiple choice questions
5. Display discussion points for deeper engagement
