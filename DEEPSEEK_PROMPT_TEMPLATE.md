# DeepSeek Processing - Prompt Template

## The Prompt That Will Be Sent to DeepSeek

Here's the exact prompt structure that will be used for processing your articles:

---

### SYSTEM PROMPT
```
You are an expert editorial analyst, educator, and content processor. 
Return responses only in valid JSON format.
```

### USER PROMPT
```
You are an expert editorial analyst and educator. Process the following {N} articles 
with comprehensive analysis.

For EACH article, provide a JSON response with the following structure:

{
    "article_id": <integer>,
    
    "summary_en": "<300-500 word comprehensive summary in English>",
    
    "summary_zh": "<300-500 word natural Chinese translation of the summary>",
    
    "key_words": [
        {
            "word": "<important keyword or term>",
            "frequency": <number of occurrences>,
            "explanation": "<50-100 word explanation of this key term in the context of the article>"
        },
        ... (exactly 10 keywords, genuinely important/infrequent, not common words)
    ],
    
    "background_reading": "<200-300 word background on the topic, explaining historical context 
                           or domain knowledge needed to understand the article>",
    
    "multiple_choice_questions": [
        {
            "question": "<question text>",
            "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is the correct answer>",
            "type": "main_idea"  // for question 1
        },
        {
            "question": "<question text>",
            "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is the correct answer>",
            "type": "new_word"   // for question 2
        },
        {
            "question": "<question text>",
            "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
            "correct_answer": "<A/B/C/D>",
            "explanation": "<why this is the correct answer>",
            "type": "sat_style"  // for questions 3-5
        },
        ... (total of 5 questions: 1 main_idea, 1 new_word, 3 sat_style)
    ],
    
    "discussion_both_sides": {
        "perspective_1": {
            "title": "<name of first perspective>",
            "arguments": [
                "<1-2 substantive arguments supporting this perspective>"
            ]
        },
        "perspective_2": {
            "title": "<name of alternative perspective>",
            "arguments": [
                "<1-2 substantive arguments supporting this perspective>"
            ]
        },
        "synthesis": "<200-300 word synthesis discussing the tension between the 
                     two perspectives, exploring how both might be partially correct 
                     and what further information would be needed to resolve the tension>"
    }
}

CRITICAL INSTRUCTIONS:
1. Ensure summaries are exactly 300-500 words
2. Chinese translation should be natural and idiomatic, NOT literal word-for-word
3. Keywords should be genuinely important/infrequent (NOT common words like "the", "is", "and", "or")
4. Background reading should help someone with NO prior knowledge understand the topic
5. Multiple choice questions should be academic level (SAT/AP difficulty)
6. For questions:
   - Question 1 (main_idea): Tests understanding of the article's central point
   - Question 2 (new_word): Tests understanding of important new vocabulary/terminology
   - Questions 3-5 (sat_style): Varying levels - inference, application, synthesis
7. Perspectives should represent genuinely different and reasonable viewpoints on the issue
8. Return ONLY valid JSON - no markdown, no code blocks, no explanatory text
9. If processing multiple articles, return a JSON array
10. Each article is independent - process all N articles completely

ARTICLES TO PROCESS:
[Articles provided in JSON array format with id, title, source, link, snippet, content, date]

Process all {N} articles with the complete analysis as specified above. 
Return ONLY valid JSON output.
```

---

## Example Input Format

The articles will be sent like this:

```json
[
  {
    "id": 16,
    "title": "This powerful drug combo cuts prostate cancer deaths by 40%",
    "source": "Science Daily",
    "link": "https://www.sciencedaily.com/releases/2025/10/251019120507.htm",
    "snippet": "A new drug combo of enzalutamide and hormone therapy...",
    "content": "[Full article text here...]",
    "date": "2025-10-19T12:59:16-04:00"
  },
  {
    "id": 17,
    "title": "Cancer patients who got a COVID vaccine lived much longer",
    "source": "Science Daily",
    "link": "https://www.sciencedaily.com/releases/2025/10/251019120503.htm",
    "snippet": "A groundbreaking study reveals that cancer patients...",
    "content": "[Full article text here...]",
    "date": "2025-10-19T12:43:31-04:00"
  },
  ...
]
```

## Expected Output Format

DeepSeek will return:

```json
[
  {
    "article_id": 16,
    "summary_en": "Detailed 300-500 word summary...",
    "summary_zh": "Detailed 300-500 word Chinese summary...",
    "key_words": [
      {"word": "enzalutamide", "frequency": 6, "explanation": "..."},
      {"word": "biochemically recurrent", "frequency": 4, "explanation": "..."},
      ...
    ],
    "background_reading": "200-300 word background...",
    "multiple_choice_questions": [
      {"question": "...", "options": [...], "correct_answer": "A", "type": "main_idea", "explanation": "..."},
      ...
    ],
    "discussion_both_sides": {
      "perspective_1": {"title": "...", "arguments": [...]},
      "perspective_2": {"title": "...", "arguments": [...]},
      "synthesis": "..."
    }
  },
  {
    "article_id": 17,
    "summary_en": "...",
    ...
  },
  ...
]
```

---

## Processing Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| model | deepseek-chat | DeepSeek's main chat model |
| temperature | 0.7 | Good balance: creative but consistent |
| max_tokens | 8000 | Per response (usually sufficient for batch) |
| batch_size | 5 | Articles per API call (adjustable) |
| rate_limit | 3 seconds | Between batches to avoid API throttling |

---

## What Happens With Your API Key

1. **Request**: Your articles (full content) are sent to DeepSeek's API
2. **Processing**: DeepSeek analyzes each article according to the prompt
3. **Response**: Returns JSON with all 6 analytical components
4. **Storage**: Results stored in local `deepseek_feedback` database table
5. **Files**: Raw responses also saved to `deepseek_batch_N.json` for inspection

All data processing happens server-side at DeepSeek. The API handles your articles securely.

---

## Customization Options

You can modify the prompt by editing these sections in `deepseek_processor.py`:

```python
# Change batch processing size
--batch-size 10  # Instead of default 5

# Change temperature (creativity level)
"temperature": 0.5,  # Lower = more consistent
"temperature": 0.9,  # Higher = more creative

# Change max tokens (response length)
"max_tokens": 10000,  # Allow longer responses

# Change rate limiting
time.sleep(5)  # Wait 5 seconds between batches instead of 3
```

---

## Quality Expectations

Based on this prompt structure, DeepSeek should deliver:

✅ **Summaries**: Comprehensive, well-organized, capturing key points
✅ **Translations**: Natural Chinese that reads as native Chinese text
✅ **Keywords**: Genuinely important terms with meaningful explanations
✅ **Background**: Context that helps unfamiliar readers understand
✅ **Questions**: Well-designed, varying difficulty, good distractors
✅ **Discussion**: Thoughtful examination of multiple perspectives

---

## Cost Consideration

Each batch (5 articles) typically requires:
- ~45-50 KB of input text
- ~8000 tokens of output
- Approximate cost: $0.01-0.02 per batch (depends on DeepSeek pricing)

20 articles (4 batches): ~$0.04-0.08 total
All 20 articles processed: One-time investment

---

## Timeline

- **Per Batch**: 2-5 seconds processing time
- **Per Batch with Rate Limiting**: 5-8 seconds
- **20 Articles (4 batches)**: ~30-40 seconds total

---

## Next Steps After Processing

1. **View Results**: `python3 deepseek_processor.py --query 16`
2. **Export to JSON**: Pipe output to file for integration
3. **Create Display Pages**: HTML templates for summaries/discussions
4. **Build Quiz Interface**: Use questions in interactive tool
5. **Integrate into Digest**: Add to email or web portal
