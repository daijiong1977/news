# Latest Deepseek Response Structure

## Root Structure

```json
{
  "article_analysis": {
    "zh_title": "string",
    "levels": {
      "easy": { /* see below */ },
      "mid": { /* see below */ },
      "hard": { /* see below */ }
    }
  }
}
```

## Level Structure - Easy

```json
{
  "easy": {
    "title": "string",
    "summary": "string",
    "keywords": [
      {
        "term": "string",
        "explanation": "string"
      }
    ],
    "questions": [
      {
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "correct_answer": "string"
      }
    ],
    "background_reading": "string",
    "perspectives": [
      {
        "perspective": "string",
        "attitude": "positive|negative|neutral"
      }
    ]
  }
}
```

## Level Structure - Mid

```json
{
  "mid": {
    "title": "string",
    "summary": "string",
    "keywords": [
      {
        "term": "string",
        "explanation": "string"
      }
    ],
    "questions": [
      {
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "correct_answer": "string"
      }
    ],
    "background_reading": "string",
    "perspectives": [
      {
        "perspective": "string",
        "attitude": "positive|negative|neutral"
      }
    ]
  }
}
```

## Level Structure - Hard

```json
{
  "hard": {
    "title": "string",
    "title_zh": "string",
    "summary": "string",
    "zh_hard": "string",
    "keywords": [
      {
        "term": "string",
        "explanation": "string"
      }
    ],
    "questions": [
      {
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "correct_answer": "string"
      }
    ],
    "background_reading": "string",
    "analysis": "string",
    "perspectives": [
      {
        "perspective": "string",
        "attitude": "positive|negative|neutral"
      }
    ]
  }
}
```

## Field Specifications

### article_analysis (root level)
- **zh_title**: Chinese title of the article

### Each Level (easy, mid, hard)

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| title | string | English title tailored to difficulty level | Required for all levels |
| title_zh | string | Chinese title | Only in hard level |
| summary | string | Detailed explanation at appropriate complexity level | Required for all levels |
| zh_hard | string | Chinese summary for hard content | Only in hard level |
| keywords | array of objects | Key terms with explanations (10 items) | Required for all levels |
| questions | array of objects | Multiple choice questions with 4 options | 5-12 questions per level |
| background_reading | string | Contextual/background information | Required for all levels |
| perspectives | array of objects | 3 viewpoints with attitudes | Required for all levels |
| analysis | string | Detailed analytical commentary | Only in hard level |

### Keywords Object
```json
{
  "term": "string",           // The key term
  "explanation": "string"      // Simple explanation appropriate to difficulty level
}
```

### Questions Object
```json
{
  "question": "string",           // The question text
  "options": [                     // Exactly 4 answer options
    "string",
    "string",
    "string",
    "string"
  ],
  "correct_answer": "string"      // Must match one of the options exactly
}
```

### Perspectives Object
```json
{
  "perspective": "string",                    // The viewpoint or argument
  "attitude": "positive|negative|neutral"    // One of three values
}
```

## Content Characteristics by Level

### Easy Level
- Simple vocabulary
- Basic concepts
- 5 questions typically
- Beginner-friendly explanations
- No Chinese translations (except zh_title at root)

### Mid Level
- Intermediate vocabulary
- More detailed concepts
- 8-10 questions typically
- Connecting simple to complex ideas
- No Chinese translations

### Hard Level
- Advanced/technical vocabulary
- Complex, nuanced explanations
- 10-12 questions typically
- Includes Chinese translations (title_zh, zh_hard)
- Includes analytical commentary
- Most comprehensive coverage

## Current Statistics (from response_article_1)

- **Easy keywords**: 10 items
- **Easy questions**: 5 questions
- **Mid keywords**: 10 items
- **Mid questions**: 8 questions
- **Hard keywords**: 10 items
- **Hard questions**: 12 questions
- **Perspectives per level**: 3 items (1 positive, 1 negative, 1 neutral)
