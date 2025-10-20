# 🎓 Enhanced Subscription & Content System

## Overview

This system provides personalized learning experiences with 3 difficulty levels:
- **Elementary** (Grades 3-5): Simple summaries (100-200 words), easy questions
- **Middle** (Grades 6-8): Standard summaries (300-500 words), medium questions  
- **High School** (Grades 9-12): Advanced summaries (500-700 words), analysis-focused questions

## New Database Schema

### categories table
```sql
- id: Primary key
- name: Category name (World, Science, Tech, Sports, Life, Economy, etc.)
- website: Website keyword for filtering
- description: Category description
- color: Brand color (hex)
- emoji: Category emoji
```

### articles_enhanced table
```sql
- id: Primary key
- original_article_id: Link to original articles table
- title: Article title
- date: Publication date
- source: News source
- image_file: Image path
- category_id: Foreign key to categories
- original_content: Full article text
```

### article_summaries table
```sql
- id: Primary key
- article_id: Foreign key to articles_enhanced
- difficulty: 'easy' | 'medium' | 'hard'
- language: 'en' | 'zh'
- summary: The summary text
- keywords: JSON array of keywords
- background: Background reading
- pro_arguments: For hard level only
- con_arguments: For hard level only
```

### quiz_questions table
```sql
- id: Primary key
- article_id: Foreign key
- difficulty: 'easy' | 'medium' | 'hard'
- question_number: 1-5
- question_text: The question
- options: JSON array of answer options
- correct_answer: Index of correct answer (0-3)
- explanation: Why this is correct
```

### subscriptions_enhanced table
```sql
- id: Primary key
- email: User email (unique)
- name: Full name
- age_group: 'elementary' | 'middle' | 'high'
- difficulty_level: 'easy' | 'medium' | 'hard'
- interests: JSON array of category IDs
- frequency: 'daily' | 'weekly'
- status: 'active' | 'inactive'
- created_at: Subscription date
- last_sent: Last digest timestamp
- confirmed: Email verification status
```

## New Subscription Form Fields

1. **Email** - User email (required)
2. **Name** - Full name (required)
3. **Reading Level** - Choose difficulty:
   - Elementary (Grades 3-5)
   - Middle School (Grades 6-8)
   - High School (Grades 9-12)
4. **Interests** - Multiple select from:
   - 🌍 World
   - 🔬 Science
   - 💻 Technology
   - 🏊 Sports
   - 🎨 Life
   - 💰 Economy
   - (More can be added)
5. **Frequency** - Daily or Weekly

## DeepSeek Integration

### Generate Summaries (3 Levels in One Batch)

**Endpoint**: `POST /generate-deepseek-summaries`

**Input**:
```json
{
  "article_id": 6,
  "title": "Article Title",
  "content": "Full article content..."
}
```

**Returns**: A prompt template with instructions for all 3 difficulty levels

**DeepSeek Prompt Structure**:
- Single batch request with 3 levels
- Returns JSON with `elementary`, `middle`, `high` keys
- Each contains: summary_en, summary_zh, keywords, questions

**Example Response Format**:
```json
{
  "elementary": {
    "summary_en": "...",
    "summary_zh": "...",
    "keywords": [...],
    "questions": [
      {
        "question": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": 0,
        "explanation": "..."
      }
    ]
  },
  "middle": { ... },
  "high": { ... }
}
```

### Store Summaries

**Endpoint**: `POST /store-summaries`

**Input**:
```json
{
  "article_id": 6,
  "summaries": { ... } // Response from DeepSeek
}
```

**Output**: Stores all 3 levels + languages in database

## API Endpoints

### /categories (GET)
Get all available content categories
```bash
curl http://localhost:5001/categories
```

### /subscribe-enhanced (POST)
Enhanced subscription with all details
```bash
curl -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "age_group": "middle",
    "interests": [1, 3, 5],
    "frequency": "daily"
  }'
```

### /generate-deepseek-summaries (POST)
Generate prompt for DeepSeek batch processing
```bash
curl -X POST http://localhost:5001/generate-deepseek-summaries \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 6,
    "title": "Article Title",
    "content": "Full article content..."
  }'
```

### /store-summaries (POST)
Store DeepSeek generated summaries to database
```bash
curl -X POST http://localhost:5001/store-summaries \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 6,
    "summaries": { ... }
  }'
```

## Content Flow

```
1. USER SUBSCRIBES
   ↓
   Fills form with:
   - Email, Name
   - Reading Level (determines difficulty)
   - Interests (topics to follow)
   - Frequency (daily/weekly)
   ↓
   Stored in subscriptions_enhanced

2. CONTENT GENERATION
   ↓
   For each article:
   - Send to DeepSeek with 3-level prompt
   - Get back summaries + questions for all levels
   - Store in article_summaries + quiz_questions

3. EMAIL DIGEST
   ↓
   For each subscriber:
   - Query articles by interests (category_id)
   - Fetch summaries at their difficulty level
   - Fetch arguments & original links (if not Elementary)
   - Send via Email API with appropriate layout

4. PERSONALIZED HTML LAYOUT
   ↓
   EASY (Elementary) - SIMPLIFIED:
   - Simple summary (100-200 words)
   - Easy questions (5)
   - NO: background, arguments, original article
   
   MEDIUM (Middle School) - STANDARD:
   - Medium summary (300-500 words)
   - Medium questions (5)
   - Background reading
   - Supporting & Counter arguments
   - Link to original article
   
   HARD (High School) - STANDARD:
   - Detailed summary (500-700 words)
   - Hard questions (5) - analysis-focused
   - Background reading
   - Supporting & Counter arguments
   - Link to original article
```

## HTML Generation Strategy

### Easy Level (Elementary) - SIMPLIFIED LAYOUT
```html
<div class="article">
  <h3>Title</h3>
  <p class="summary">100-200 word simple summary</p>
  <div class="keywords">Key Topics: ...</div>
  <div class="quiz">5 Easy Questions</div>
  
  <!-- NO: Background, Arguments, Original Article Link -->
</div>
```

### Medium Level (Middle School) - STANDARD LAYOUT
```html
<!-- SAME LAYOUT AS HIGH SCHOOL AND CURRENT main_articles_interface_v2.html -->

<div class="article">
  <h3>Title</h3>
  <p class="summary">300-500 word medium summary</p>
  <div class="keywords">Key Topics: ...</div>
  <div class="background">Background Reading</div>
  <div class="discussion">
    <div class="pro">Supporting Arguments</div>
    <div class="con">Counterarguments</div>
  </div>
  <div class="quiz">5 Medium Questions</div>
  <a href="...">Read Full Article</a>
</div>
```

### Hard Level (High School) - STANDARD LAYOUT (SAME AS MIDDLE)
```html
<!-- SAME LAYOUT AS MIDDLE SCHOOL -->

<div class="article">
  <h3>Title</h3>
  <p class="summary">500-700 word detailed summary</p>
  <div class="keywords">Key Topics: ...</div>
  <div class="background">Background Reading</div>
  <div class="discussion">
    <div class="pro">Supporting Arguments</div>
    <div class="con">Counterarguments</div>
  </div>
  <div class="quiz">5 Hard Questions (analysis-focused)</div>
  <a href="...">Read Full Article</a>
</div>
```

## Layout Summary

| Level | Layout | Content Difficulty | Background | Arguments | Original Link |
|-------|--------|-------------------|------------|-----------|----------------|
| **Elementary** | **SIMPLIFIED** | Easy (100-200w) | ❌ NO | ❌ NO | ❌ NO |
| **Middle School** | **STANDARD** | Medium (300-500w) | ✅ YES | ✅ YES | ✅ YES |
| **High School** | **STANDARD** | Hard (500-700w) | ✅ YES | ✅ YES | ✅ YES |

## Setup Steps

### 1. Start Enhanced Service
```bash
python3 /Users/jidai/news/subscription_service_enhanced.py
```

### 2. Test Categories Endpoint
```bash
curl http://localhost:5001/categories
```

### 3. Test Subscription
```bash
curl -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "age_group": "middle",
    "interests": [1, 2],
    "frequency": "daily"
  }'
```

### 4. Check Database
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT email, name, age_group, difficulty_level FROM subscriptions_enhanced;"
```

### 5. View Categories
```bash
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT * FROM categories;"
```

## Migration from Old System

To migrate from old `subscriptions` table to new `subscriptions_enhanced`:

```sql
INSERT INTO subscriptions_enhanced (email, frequency, status, age_group, difficulty_level, interests)
SELECT email, frequency, status, 'middle', 'medium', '[]'
FROM subscriptions
WHERE status = 'active';
```

## Future Enhancements

- [ ] Email verification (double opt-in)
- [ ] Unsubscribe functionality
- [ ] Digest preview before send
- [ ] User preferences dashboard
- [ ] Analytics & engagement tracking
- [ ] A/B testing for subject lines
- [ ] Personalized topic recommendations
- [ ] Reading time estimates
- [ ] Progress tracking
- [ ] Achievement badges

## Troubleshooting

**Error: "Please select at least one interest"**
- Ensure categories are loading: Check `/categories` endpoint
- Verify database has categories: `SELECT COUNT(*) FROM categories;`

**Form not showing all fields**
- Check browser console for JavaScript errors
- Ensure subscription service is running on port 5001
- Clear browser cache

**Categories not loading**
- Check if subscription service is running
- Verify database initialized: `SELECT COUNT(*) FROM categories;`
- Check network requests in browser DevTools
