# Quiz Game Development Guide

## Overview

The DeepSeek processor now automatically separates quiz **questions** and **correct answers** into a dedicated database table specifically designed for game development.

## Why Separate Tables?

Previously, questions and answers were stored together in JSON format inside the main feedback table. Now they're in a dedicated `quiz_questions` table with:

- **Separate columns for each option** (option_a, option_b, option_c, option_d)
- **Separate column for correct answer** (correct_answer)
- **Individual IDs** for each question (perfect for game tracking)
- **Question types** stored separately (main_idea, new_word, sat_style)
- **Database indexes** for fast game queries

This makes it **extremely easy** to build quiz games!

---

## Database Schema

```sql
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question_type TEXT,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Column Descriptions

| Column | Type | Purpose |
|--------|------|---------|
| `id` | INTEGER | Unique question ID for game tracking |
| `article_id` | INTEGER | Links to the source article |
| `question_number` | INTEGER | 1-5 (questions per article) |
| `question_type` | TEXT | Type: main_idea, new_word, sat_style |
| `question_text` | TEXT | The question itself |
| `option_a` | TEXT | Option A text |
| `option_b` | TEXT | Option B text |
| `option_c` | TEXT | Option C text |
| `option_d` | TEXT | Option D text |
| `correct_answer` | TEXT | Correct option: A, B, C, or D |
| `explanation` | TEXT | Why this answer is correct |

---

## How Questions Are Stored

When you run the processor:

```bash
python3 deepseek_processor.py --batch-size 5
```

For each article:
1. DeepSeek returns 5 multiple-choice questions
2. Questions are stored in `quiz_questions` table
3. Each option (A, B, C, D) is in its own column
4. Correct answer is in `correct_answer` column
5. Each question gets a unique ID

**Example from database:**

```
id  | article_id | question_number | question_type | question_text            | option_a | option_b | option_c | option_d | correct_answer | explanation
----|------------|-----------------|---------------|--------------------------|----------|----------|----------|----------|----------------|------------------------
42  | 16         | 1               | main_idea     | What is the main topic? | Option 1 | Option 2 | Option 3 | Option 4 | B              | Option 2 correctly...
43  | 16         | 2               | new_word      | Define "innovation"     | ...      | ...      | ...      | ...      | C              | ...
```

---

## Game Development Commands

### 1. Get All Questions for an Article

Perfect for building a quiz around one article:

```bash
python3 deepseek_processor.py --quiz 16
```

Returns all 5 questions as JSON:

```json
[
  {
    "id": 42,
    "question_number": 1,
    "type": "main_idea",
    "question": "What is the main topic?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": "B",
    "explanation": "Option 2 correctly identifies..."
  },
  {
    "id": 43,
    "question_number": 2,
    "type": "new_word",
    "question": "Define 'innovation'",
    "options": [...],
    "correct_answer": "C",
    "explanation": "..."
  }
]
```

### 2. Get a Single Question by ID

Perfect for rendering one question at a time in games:

```bash
python3 deepseek_processor.py --quiz-id 42
```

Returns:

```json
{
  "id": 42,
  "article_id": 16,
  "question_number": 1,
  "type": "main_idea",
  "question": "What is the main topic?",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correct_answer": "B",
  "explanation": "Option 2 correctly identifies..."
}
```

### 3. Get All Quiz Questions (Build Question Bank)

Perfect for creating a large quiz database:

```bash
python3 deepseek_processor.py --all-quiz
```

Returns all questions from all articles as a JSON array.

### 4. Get Questions by Type

Filter questions for difficulty levels:

```bash
# Only "main idea" questions
python3 deepseek_processor.py --quiz-type main_idea

# Only "new word" questions
python3 deepseek_processor.py --quiz-type new_word

# Only "SAT style" questions
python3 deepseek_processor.py --quiz-type sat_style
```

---

## Usage Examples for Games

### Example 1: Simple Quiz Web App

```python
import json
import subprocess

# Get questions for article 16
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz", "16"],
    capture_output=True,
    text=True
)
questions = json.loads(result.stdout)

for q in questions:
    print(f"Question {q['question_number']}: {q['question']}")
    for i, option in enumerate(q['options']):
        print(f"  {chr(65+i)}) {option}")
    
    # Game logic
    user_answer = input("Your answer: ").upper()
    if user_answer == q['correct_answer']:
        print("✓ Correct!")
    else:
        print(f"✗ Wrong. The answer is {q['correct_answer']}")
        print(f"  {q['explanation']}")
```

### Example 2: Quiz Difficulty Levels

```python
import json
import subprocess

# Create different difficulty levels from question types
def get_quiz_game(difficulty):
    if difficulty == "easy":
        qtype = "main_idea"
    elif difficulty == "medium":
        qtype = "new_word"
    else:  # hard
        qtype = "sat_style"
    
    result = subprocess.run(
        ["python3", "deepseek_processor.py", "--quiz-type", qtype],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Build a game menu
easy_questions = get_quiz_game("easy")    # ~20 main_idea questions
medium_questions = get_quiz_game("medium")  # ~20 new_word questions
hard_questions = get_quiz_game("hard")    # ~20 sat_style questions
```

### Example 3: Daily Quiz Challenge

```python
import json
import sqlite3
import random

# Get random question from database
conn = sqlite3.connect('articles.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Random question of the day
cursor.execute("SELECT * FROM quiz_questions ORDER BY RANDOM() LIMIT 1")
q = cursor.fetchone()

print(f"📚 Daily Challenge from Article {q['article_id']}")
print(f"\n{q['question_text']}")
print(f"A) {q['option_a']}")
print(f"B) {q['option_b']}")
print(f"C) {q['option_c']}")
print(f"D) {q['option_d']}")
```

### Example 4: Quiz Statistics

```python
import sqlite3

conn = sqlite3.connect('articles.db')
cursor = conn.cursor()

# Count questions by type
cursor.execute("""
    SELECT question_type, COUNT(*) as count
    FROM quiz_questions
    GROUP BY question_type
""")
print("Questions by type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} questions")

# Count questions per article
cursor.execute("""
    SELECT article_id, COUNT(*) as count
    FROM quiz_questions
    GROUP BY article_id
""")
print("\nQuestions per article:")
for row in cursor.fetchall():
    print(f"  Article {row[0]}: {row[1]} questions")
```

---

## SQL Queries for Game Development

### Get Questions for a Specific Article

```sql
SELECT * FROM quiz_questions 
WHERE article_id = 16 
ORDER BY question_number;
```

### Get All Questions of a Type

```sql
SELECT * FROM quiz_questions 
WHERE question_type = 'sat_style'
ORDER BY article_id, question_number;
```

### Get Random Question

```sql
SELECT * FROM quiz_questions 
ORDER BY RANDOM() 
LIMIT 1;
```

### Get Questions from Multiple Articles

```sql
SELECT * FROM quiz_questions 
WHERE article_id IN (16, 17, 18)
ORDER BY article_id, question_number;
```

### Check Answer (User Study)

```sql
-- Track user answers
CREATE TABLE quiz_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct INTEGER,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES quiz_questions(id)
);

-- Insert user answer
INSERT INTO quiz_answers (question_id, user_answer, is_correct)
VALUES (42, 'B', 1);

-- Get user score
SELECT COUNT(*) as total, 
       SUM(is_correct) as correct
FROM quiz_answers;
```

---

## Integration with Your News Portal

### Display Quiz with Article

```python
# When user views article 16
from db_utils import fetch_article_by_id

article = fetch_article_by_id(16)

# Get associated quiz
result = subprocess.run(
    ["python3", "deepseek_processor.py", "--quiz", "16"],
    capture_output=True,
    text=True
)
questions = json.loads(result.stdout)

# Render in HTML
html = f"""
<article>
    <h1>{article['title']}</h1>
    <p>{article['summary']}</p>
</article>

<section class="quiz">
    <h2>Test Your Knowledge</h2>
    {render_questions(questions)}
</section>
"""
```

---

## Features Available for Your Game

✅ **Separate Questions & Answers** - Easy game logic  
✅ **Individual Question IDs** - Track user responses  
✅ **Question Types** - Create difficulty levels  
✅ **Explanations** - Show why answers are correct  
✅ **Article Links** - Know which article each question is from  
✅ **Database Indexes** - Fast queries for game responsiveness  
✅ **JSON Output** - Easy integration with web/mobile apps  

---

## Quick Start for Game Dev

**Step 1:** Get all questions

```bash
python3 deepseek_processor.py --all-quiz > all_questions.json
```

**Step 2:** Load into your game

```python
import json
with open('all_questions.json') as f:
    questions = json.load(f)
```

**Step 3:** Render questions

```python
for q in questions:
    print(f"{q['question']}")
    for i, opt in enumerate(q['options']):
        print(f"  {chr(65+i)}) {opt}")
```

**Step 4:** Check answers

```python
user_ans = input("Answer: ").upper()
if user_ans == q['correct_answer']:
    print("✓ Correct!")
else:
    print(f"✗ Wrong: {q['explanation']}")
```

---

## Summary

The new `quiz_questions` table gives you:

| Feature | Benefit for Games |
|---------|-------------------|
| Separate columns for options A-D | Easy to randomize or shuffle answers |
| Separate correct_answer column | Simple to check user responses |
| Individual question IDs | Track which questions users answer |
| Question types | Build difficulty-based games |
| Database indexes | Fast queries for real-time games |
| Explanations included | Educational value |
| JSON export | Integration with any platform |

**You're now ready to build your quiz game!** 🎮📚
