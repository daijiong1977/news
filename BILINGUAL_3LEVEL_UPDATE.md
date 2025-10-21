# Bilingual 3-Level Summary Implementation

## Overview
System now generates **6 summaries per article**:
- **easy_en** - Simple English (ages 8-10)
- **easy_zh** - Simple Chinese (8-10岁)
- **mid_en** - Intermediate English (ages 11-13)
- **mid_zh** - Intermediate Chinese (11-13岁)
- **high_en** - Complex English (ages 14+)
- **high_zh** - Complex Chinese (14岁以上)

## Changes Made

### 1. `run_full_pipeline.py`
#### Deepseek Prompt (Lines 451-483)
- **OLD:** Generated only `elementary_en` and `elementary_zh`
- **NEW:** Generates all 6 difficulty/language combinations
- Prompt emphasizes matching complexity levels between EN/ZH translations

#### SQL Query (Lines 806-826)
- **OLD:** Fetched `elementary`, `middle`, `high`, `elementary_en`, `elementary_zh`
- **NEW:** Fetches `summary_easy_en`, `summary_easy_zh`, `summary_mid_en`, `summary_mid_zh`, `summary_high_en`, `summary_high_zh`

#### JSON Generation (Lines 832-862)
- **OLD:** Generated `summary_easy`, `summary_medium`, `summary_hard` (no language)
- **NEW:** Generates language-specific fields:
  ```json
  {
    "summary_easy_en": "...",
    "summary_easy_zh": "...",
    "summary_mid_en": "...",
    "summary_mid_zh": "...",
    "summary_hard_en": "...",
    "summary_hard_zh": "..."
  }
  ```

### 2. `main_articles_interface_v2.html`
#### renderArticles() Function (Lines 186-213)
- **OLD:** Used `difficultyMap` with single field per difficulty
- **NEW:** Uses `difficultyMap` with language-specific fields:
  ```javascript
  const difficultyMap = {
    'easy': { en: 'summary_easy_en', zh: 'summary_easy_zh' },
    'medium': { en: 'summary_mid_en', zh: 'summary_mid_zh' },
    'hard': { en: 'summary_hard_en', zh: 'summary_hard_zh' }
  };
  ```
- Now selects correct field based on **both** `currentDifficulty` and `currentLanguage`

### 3. `article_analysis_v2.html`
#### loadArticle() Function (Lines 616-634)
- **OLD:** Used `summaryFieldMap` then applied language as overlay
- **NEW:** Uses nested language structure like homepage:
  ```javascript
  const summaryFieldMap = {
    'easy': { en: 'summary_easy_en', zh: 'summary_easy_zh' },
    'medium': { en: 'summary_mid_en', zh: 'summary_mid_zh' },
    'hard': { en: 'summary_hard_en', zh: 'summary_hard_zh' }
  };
  const summaryField = difficultyData[currentLanguage === 'zh' ? 'zh' : 'en'];
  ```

#### renderSummaryQuiz() Function (Line 739)
- Now shows both difficulty and language in debug badge

#### renderKeywords() Function (Line 893)
- Simplified fallback logic

## How It Works

### User Interaction Flow
1. User visits homepage
2. **Selects Difficulty:** HIGH/MID/EASY (dropdown)
3. **Selects Language:** EN/CN (buttons)
4. System determines summary field:
   - Difficulty + Language = Specific field
   - Example: MID + CN = `summary_mid_zh`
5. Homepage displays article with correct summary
6. User clicks MORE → Goes to detail page
7. Detail page respects both selections
8. User can change difficulty or language on detail page

### Data Storage
```
Database (articles_summaries table):
- article_id: 1
- difficulty: "easy_en" / "easy_zh" / "mid_en" / "mid_zh" / "high_en" / "high_zh"
- language: "en" or "zh"
- summary: "The actual summary text"

JSON Output (articles_data.json):
{
  "id": 1,
  "title": "...",
  "summary_easy_en": "Simple English...",
  "summary_easy_zh": "简单中文...",
  "summary_mid_en": "Intermediate English...",
  "summary_mid_zh": "中等中文...",
  "summary_hard_en": "Complex English...",
  "summary_hard_zh": "复杂中文..."
}
```

## Testing Checklist

- [ ] Reset deepseek_processed flag: `UPDATE articles SET deepseek_processed = 0`
- [ ] Run pipeline: `python3 run_full_pipeline.py --skip-crawl --skip-fetch`
- [ ] Verify Deepseek output shows "✓ Generated summaries: easy_en, easy_zh, mid_en, mid_zh, high_en, high_zh" for each article
- [ ] Check JSON output has all 6 fields
- [ ] Test homepage: Select different difficulty levels → see different EN content
- [ ] Test homepage: Select CN button → see different ZH content
- [ ] Test homepage: HIGH + EN → MID + EN → EASY + EN → see varying complexity
- [ ] Test homepage: HIGH + CN → MID + CN → EASY + CN → see varying complexity
- [ ] Click MORE on article → verify detail page uses correct summary
- [ ] Change difficulty on detail page → see different content at same language
- [ ] Change language on detail page → see different language at same difficulty

## Database Migration Notes

Old articles with only `elementary` difficulty will NOT have new fields.
Need to reset: `UPDATE articles SET deepseek_processed = 0` to force regeneration with all 6 summaries.

## API Calls

Each article requires ONE Deepseek API call (returns all 6 summaries at once).
- Old system: Could require 1-3 calls per article
- New system: Exactly 1 call per article → More efficient!

## Language Accuracy Notes

For each difficulty level, the EN and ZH versions should be:
- **At the same reading level** (not translations of different difficulty levels)
- **Approximately equal length**
- **Convey the same meaning** (not literal word-for-word translation)
- **Use appropriate vocabulary** for the target difficulty

Example:
```
EASY:
  EN: "A big storm made flooding happen in many places." (8-10 year old words)
  ZH: "一场大风暴导致许多地方发生了洪水。" (8-10岁的词汇)

MID:
  EN: "Severe weather conditions resulted in widespread flooding." (11-13 year old level)
  ZH: "恶劣的天气条件导致了广泛的洪水泛滥。" (11-13岁的水平)

HIGH:
  EN: "Meteorological phenomena precipitated catastrophic inundation across multiple regions." (14+ year old level)
  ZH: "气象现象导致了多个地区的灾难性泛滥。" (14岁以上的水平)
```

## Common Issues & Fixes

### Issue: Detail page shows empty summary
- Check that both difficulty dropdown and language buttons are set
- Verify JSON has the required `summary_X_en` or `summary_X_zh` field
- Check browser console for errors

### Issue: Clicking HIGH then MID shows same content
- Make sure you're looking at the same language
- Verify pipeline ran successfully with new Deepseek prompt
- Check articles_data.json to ensure all fields are populated

### Issue: CN button shows wrong language
- Verify `currentLanguage` is being set correctly
- Check HTML button click handlers
- Verify JSON has `summary_X_zh` fields

## Next Steps

1. Deploy files to server
2. Reset database flag and re-process all articles through Deepseek
3. Verify JSON output on server
4. Test all 9 combinations (3 difficulties × 3 selections)
5. Adjust Deepseek prompt if summaries aren't appropriate for age group
