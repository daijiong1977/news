# 📐 Layout Personalization Strategy - CLARIFIED

## The Key Insight

**Layout & Content Personalization:**

- **Elementary** → Simplified layout (NO background, NO arguments, NO original link)
- **Middle School** → Standard layout (same as High School)
- **High School** → Standard layout (same as Middle School)

Content difficulty differs, but Middle and High School layouts are identical.

---

## Visual Comparison

### Elementary Student Views This:
```
┌─────────────────────────────────────┐
│ Article Title                       │
├─────────────────────────────────────┤
│ [Simple 100-200 word summary]       │
├─────────────────────────────────────┤
│ Key Topics: word1, word2, word3     │
├─────────────────────────────────────┤
│ 5 Easy Questions with Answers       │
│ ✓ Question 1: [answer explanation] │
│ ✓ Question 2: [answer explanation] │
│ ...                                 │
└─────────────────────────────────────┘
```

### Middle School Student Views This:
```
┌─────────────────────────────────────┐
│ Article Title                       │
├─────────────────────────────────────┤
│ [Medium 300-500 word summary]       │
├─────────────────────────────────────┤
│ Key Topics: word1, word2, ...       │
├─────────────────────────────────────┤
│ BACKGROUND READING                  │
│ [Historical context paragraph]      │
├─────────────────────────────────────┤
│ DISCUSSION                          │
│ PRO: [supporting arguments]         │
│ CON: [opposing arguments]           │
├─────────────────────────────────────┤
│ 5 Medium Questions with Answers     │
│ ✓ Question 1: [detailed answer]     │
│ ...                                 │
├─────────────────────────────────────┤
│ [Link: Read Full Original Article]  │
└─────────────────────────────────────┘
```

### High School Student Views This:
```
┌─────────────────────────────────────┐
│ Article Title                       │
├─────────────────────────────────────┤
│ [Detailed 500-700 word summary]     │
├─────────────────────────────────────┤
│ Key Topics: word1, word2, ...       │
├─────────────────────────────────────┤
│ BACKGROUND READING                  │
│ [Deep historical context]           │
├─────────────────────────────────────┤
│ DISCUSSION & ANALYSIS               │
│ PRO: [detailed supporting args]     │
│ CON: [detailed opposing args]       │
├─────────────────────────────────────┤
│ 5 Hard Questions (Analysis-focused) │
│ ✓ Question 1: [complex answer]      │
│ ...                                 │
├─────────────────────────────────────┤
│ [Link: Read Full Original Article]  │
└─────────────────────────────────────┘
```

---

## Content vs Layout

| Aspect | Elementary | Middle School | High School |
|--------|------------|---------------|-------------|
| **Layout Structure** | Simplified | Standard | Standard |
| **Summary Length** | 100-200 words | 300-500 words | 500-700 words |
| **Keywords** | ✅ YES | ✅ YES | ✅ YES |
| **Background Reading** | ❌ NO | ✅ YES | ✅ YES |
| **Pro Arguments** | ❌ NO | ✅ YES | ✅ YES |
| **Con Arguments** | ❌ NO | ✅ YES | ✅ YES |
| **Original Article Link** | ❌ NO | ✅ YES | ✅ YES |
| **Quiz Difficulty** | Easy (Recall) | Medium (Comprehension) | Hard (Analysis) |
| **Question Complexity** | Simple | Standard | Advanced |

---

## DeepSeek Generation - Still Single Request

Despite different layouts, DeepSeek generates all 3 levels in **ONE request**:

```json
Request: "Generate 3 levels of content for this article"

Response: {
  "elementary": {
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [...],
    "questions": [...]
    // NO: background, arguments
  },
  
  "middle": {
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [...],
    "background": "...",
    "pro_arguments": "...",
    "con_arguments": "...",
    "questions": [...]
  },
  
  "high": {
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [...],
    "background": "...",
    "pro_arguments": "...",
    "con_arguments": "...",
    "questions": [...]
  }
}
```

---

## Implementation Steps

### Step 1: Store Content Variants
```sql
-- All 3 levels stored in DB
INSERT INTO article_summaries (article_id, difficulty, summary, background, pro_arguments, con_arguments)
VALUES 
  (6, 'easy', '...', NULL, NULL, NULL),
  (6, 'medium', '...', '...', '...', '...'),
  (6, 'hard', '...', '...', '...', '...');
```

### Step 2: Generate HTML Based on Difficulty
```javascript
// When generating HTML email:
if (difficulty === 'elementary') {
  // Simple template: title, summary, keywords, questions ONLY
  htmlEmail = generateElementaryTemplate(article);
} else {
  // Standard template: all sections + arguments + link
  htmlEmail = generateStandardTemplate(article);
}
```

### Step 3: Send Personalized Email
```python
for subscriber in subscribers:
    difficulty = subscriber.difficulty_level  # 'easy', 'medium', 'hard'
    
    if difficulty == 'easy':
        html_email = generate_elementary_email(articles, difficulty)
    else:  # middle or high
        html_email = generate_standard_email(articles, difficulty)
    
    send_email(subscriber.email, html_email)
```

---

## File Organization

```
/ (root)
├─ main_articles_interface_v2.html
│  └─ Used for MIDDLE and HIGH SCHOOL subscribers
│     (displays the standard layout)
│
├─ email_scheduler.py
│  ├─ Query subscriber.difficulty_level
│  ├─ If 'easy' → generate_elementary_email()
│  ├─ If 'medium' or 'hard' → generate_standard_email()
│  └─ Send appropriate layout
│
└─ Templates (NEW - to create):
   ├─ email_template_elementary.html (simplified)
   ├─ email_template_standard.html (middle & high)
   └─ article_analysis_elementary.html (if needed for browser viewing)
```

---

## Summary

### Current System (Before)
✅ One HTML layout for all
✅ All articles show the same format

### New System (After)
✅ **Elementary**: Simplified HTML layout (no background, no arguments, no link)
✅ **Middle School**: Standard HTML layout (WITH background, WITH arguments, WITH link)
✅ **High School**: Standard HTML layout (SAME as Middle School)
✅ **All 3 generate in 1 DeepSeek request**
✅ **Middle & High layouts are identical - only content difficulty differs**
✅ **Elementary is the only simplified layout**

---

## What Changes in Code

### In `email_scheduler.py`:
```python
# OLD (today)
html = generate_digest(articles)
send_email(subscriber.email, html)

# NEW (after)
if subscriber.difficulty_level == 'easy':
    # Elementary: simplified layout (NO args, NO original link)
    html = generate_digest_elementary(articles)
else:
    # Middle/High: standard layout (WITH args, WITH original link)
    html = generate_digest_standard(articles)

send_email(subscriber.email, html)
```

### In Database:
```sql
-- Same for all levels
article_summaries (summary, keywords)

-- Only for middle/high
article_summaries (background, pro_arguments, con_arguments)
```

---

## Next Action

✅ **Framework understood**  
✅ **DeepSeek prompt design finalized**  
✅ **Database schema ready**  
✅ **HTML layouts documented**  

**Ready to:** Start generating 3-tier content with DeepSeek! 🚀
