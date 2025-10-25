# Article Analysis Prompt

Analyze the following article and provide JSON output matching this exact structure:

{
  "meta": {
    "article_id": 1
  },
  "article_analysis": {
    "levels": {
      "easy": {
        "title": "Title for elementary (8-10yr)",
        "summary": "200 words for elementary students",
        "keywords": [{"term": "word", "explanation": "simple explanation"}],
        "questions": [{"question": "?", "options": ["A","B","C","D"], "correct_answer": "A"}],
        "background_read": ["Context for elementary students"],
        "Article_Structure": ["WHO: ...", "WHAT: ...", "WHERE: ...", "WHY: ..."],
        "perspectives": [{"perspective": "view1", "description": "desc1"}]
      },
      "middle": {
        "title": "Title for middle (12-14yr)",
        "summary": "300 words for middle school students",
        "keywords": [{"term": "word", "explanation": "moderate explanation"}],
        "questions": [{"question": "?", "options": ["A","B","C","D"], "correct_answer": "A"}],
        "background_read": ["Context for middle students"],
        "Article_Structure": ["100-word analysis covering: Main Points, Purpose, Evidence Evaluation, Author Credibility, Methodology"],
        "perspectives": [{"perspective": "view1", "description": "desc1"}]
      },
      "high": {
        "title": "Title for high (15-18yr)",
        "summary": "400 words for high school students",
        "keywords": [{"term": "word", "explanation": "advanced explanation"}],
        "questions": [{"question": "?", "options": ["A","B","C","D"], "correct_answer": "A"}],
        "background_read": ["Context for high school students"],
        "Article_Structure": ["150-word in-depth analysis covering: Main Points, Purpose, Evidence Evaluation, Author Credibility, Methodology, Critical Assessment"],
        "perspectives": [{"perspective": "view1", "description": "desc1"}]
      },
      "zh": {
        "title": "中文标题",
        "summary": "中文摘要"
      }
    }
  }
}

Requirements:

EASY LEVEL (8-10 years):
- Article_Structure should list WHO, WHAT, WHERE, WHY
- Use simple language, 8 questions, 100-150 word background
- Each structure item should answer the basic question

MIDDLE LEVEL (12-14 years):
- Article_Structure should be a 100-word comprehensive analysis
- Include: Main Points (key arguments), Purpose (why article was written), 
  Evidence Evaluation (assess quality of evidence), Author Credibility (background/expertise), 
  Methodology (how information was gathered)
- 10 questions, 150-250 word background
- Moderate language complexity

HIGH LEVEL (15-18 years):
- Article_Structure should be a 150-word in-depth analysis
- Include: Main Points (detailed arguments), Purpose (broader context), 
  Evidence Evaluation (critical assessment of sources), Author Credibility (expertise/bias), 
  Methodology (research methods), Critical Assessment (strengths/limitations)
- 12 questions, 200-300 word background
- Complex language, academic vocabulary

CHINESE (zh):
- Title: Chinese translation of article title
- Summary: 200-300 word Chinese summary

UNIVERSAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown
- Keywords must have "term" and "explanation" fields
- Questions need "question", "options" (4 choices), "correct_answer"
- All text must be properly closed strings with no unterminated quotes
- No trailing commas
- Article_Structure for easy: array of 4 strings (WHO, WHAT, WHERE, WHY)
- Article_Structure for middle/high: array with 1 element containing full analysis text (100-150 words)
