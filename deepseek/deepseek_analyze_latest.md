# Deepseek Article Analysis Pipeline

## Overview

This is an automated pipeline for analyzing news articles using the Deepseek API. It processes articles through three difficulty levels (easy, middle, high) and generates Chinese translations. The system includes automatic batch processing, database integration, and file organization.

## Architecture

```
news/
├── deepseek/
│   ├── process_one_article.py      # API processor (batch or single mode)
│   ├── insert_from_response.py     # Database integration + file organization
│   ├── prompts.md                  # Detailed prompt template for Deepseek
│   ├── response_template.json      # Expected output structure
│   ├── view_response.py            # HTML viewer for responses
│   └── responses/                  # Temporary JSON storage
├── website/
│   ├── article_page/               # (reserved for article pages)
│   ├── article_image/              # (reserved for article images)
│   └── article_response/           # Final response file destination
├── articles.db                     # SQLite database
└── [other project files]
```

## Key Components

### 1. `process_one_article.py` - API Processor

**Purpose**: Fetches articles from database, calls Deepseek API, generates analysis responses

**Features**:
- Fetches API key from database (no environment variables)
- Reads-only from articles table
- Calls Deepseek API with optimized prompt
- Validates response structure
- Saves JSON to `deepseek/responses/`
- **Batch mode**: Automatically finds and processes all unprocessed articles
- **Single mode**: Processes specific article by ID

**Usage**:

```bash
# Batch mode - process all unprocessed articles
python3 process_one_article.py

# Single mode - process specific article
python3 process_one_article.py 6
```

**Dynamic Paths**:
- All paths are computed relative to the script location
- Works on any server with same directory structure
- No hardcoded user paths

**Processing Steps**:
1. Get API key from database (articles.db, apikey table)
2. Fetch article content from database (read-only)
3. Load prompt template from `prompts.md`
4. Load response template for validation
5. Build user prompt combining instructions + article
6. Call Deepseek API with temperature=0.7, max_tokens=6000
7. Validate response structure matches template
8. Save JSON to `deepseek/responses/article_{id}_response.json`
9. Print completion summary (file size only)

**Batch Processing Logic**:
- Queries database for articles where `deepseek_processed=0` AND `deepseek_failed<3`
- Processes sequentially with progress indicator `[1/N]`, `[2/N]`, etc.
- Continues through all unprocessed articles

### 2. `insert_from_response.py` - Database Integration & File Organization

**Purpose**: Updates database after API processing, moves response files to final location

**Features**:
- Validates response JSON structure
- Inserts record into `response` table
- Updates `articles` table with processing status
- Automatically moves response files to `website/article_response/`
- Handles errors gracefully with status tracking

**Usage**:

```bash
# Success path - process and move file
python3 insert_from_response.py 2 deepseek/responses/article_2_response.json

# Error path (optional)
python3 insert_from_response.py 4 '' --error 'API timeout'
```

**On Success**:
- Validates JSON structure (meta.article_id, article_analysis.levels)
- Inserts into `response` table: article_id, respons_file
- Updates `articles` table:
  - `deepseek_processed = 1`
  - `processed_at = NOW()`
  - `deepseek_failed = 0`
  - `deepseek_last_error = NULL`
- Moves file: `deepseek/responses/article_{id}_response.json` → `website/article_response/article_{id}_response.json`
- Handles duplicate filenames with timestamp suffix

**On Error**:
- Updates `articles` table only:
  - `deepseek_processed = 0`
  - `deepseek_failed += 1`
  - `deepseek_last_error = error_message`
- No response table insert
- No file movement

### 3. `prompts.md` - Prompt Template

**Content**: Detailed instructions for Deepseek API, specifying output structure and requirements for each difficulty level

**Key Sections**:

**Easy Level** (8 questions):
- Article_Structure: 4 items (WHO, WHAT, WHERE, WHY)
- Background reading: 100-150 words
- 8 comprehension questions

**Middle Level** (10 questions):
- Article_Structure: 1 item, 100-word comprehensive analysis
  - Includes: Main Points, Purpose, Evidence Evaluation, Author Credibility, Methodology
- Background reading: 150-250 words
- 10 analysis questions

**High Level** (12 questions):
- Article_Structure: 1 item, 150-word in-depth analysis
  - Includes: Main Points, Purpose, Evidence Evaluation, Author Credibility, Methodology, Critical Assessment
- Background reading: 200-300 words
- 12 critical questions

**Chinese Level**:
- Title translation
- 200-300 word summary in Chinese

### 4. `response_template.json` - Output Structure

**Purpose**: Reference template showing expected Deepseek response structure

**Structure**:
```json
{
  "meta": {
    "article_id": 1
  },
  "article_analysis": {
    "levels": {
      "easy": {
        "title": "...",
        "summary": "...",
        "keywords": ["..."],
        "questions": ["..."],
        "background_read": ["..."],
        "Article_Structure": ["WHO", "WHAT", "WHERE", "WHY"],
        "perspectives": ["..."]
      },
      "middle": { /* same structure */ },
      "high": { /* same structure */ },
      "zh": {
        "title": "...",
        "summary": "..."
      }
    }
  }
}
```

## Database Schema

**Key Tables**:

### response
```sql
CREATE TABLE response (
  response_id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL,
  respons_file TEXT,
  FOREIGN KEY (article_id) REFERENCES articles(id)
)
```

### articles (updated columns)
```sql
deepseek_processed BOOLEAN DEFAULT 0      -- 1 = successfully processed
deepseek_failed INTEGER DEFAULT 0         -- failure count
deepseek_last_error TEXT                  -- error message if failed
processed_at TEXT                         -- timestamp of processing
```

## Workflow

### Standard Processing Workflow

```
1. Run batch processor
   python3 process_one_article.py

2. For each unprocessed article:
   - Fetch API key from database
   - Retrieve article content
   - Build Deepseek prompt
   - Call API
   - Validate response
   - Save to deepseek/responses/article_{id}_response.json

3. After each successful API response:
   python3 insert_from_response.py {id} deepseek/responses/article_{id}_response.json

4. Database integration:
   - Insert response record
   - Update articles table
   - Move file to website/article_response/

Final Result:
- Response files in: /website/article_response/
- Database records in: response table
- Processing status in: articles table
```

### Error Handling

**Article with API Error**:
1. API returns error or invalid JSON
2. File saved to `deepseek/responses/` but not moved
3. Run: `python3 insert_from_response.py {id} '' --error 'API error details'`
4. Database updated with error status
5. Can retry later (deepseek_failed < 3)

**Article with Bad Content**:
1. Missing or incomplete article content
2. Skip processing
3. Manually update database as needed

## API Configuration

**Endpoint**: `https://api.deepseek.com/chat/completions`

**Model**: `deepseek-chat`

**Parameters**:
- `temperature`: 0.7 (balanced creativity/consistency)
- `max_tokens`: 6000 (sufficient for all 4 levels + structure)
- `response_format`: `json_object` (forces JSON output)

**API Key Location**: Database table `apikey` where `name='DeepSeek'`

## File Organization

**Temporary Storage** (`deepseek/responses/`):
- Active during processing
- Files deleted after successful database integration
- If error: stays until manually resolved or retry succeeds

**Final Storage** (`website/article_response/`):
- After successful database update
- Format: `article_{id}_response.json`
- Never deleted by pipeline
- Ready for frontend/website use

## Running the Pipeline

### Option 1: Batch Process All Unprocessed Articles

```bash
cd /Users/jidai/news
source .venv/bin/activate

# Process all unprocessed articles
python3 deepseek/process_one_article.py

# Check status
sqlite3 articles.db "SELECT id, title, deepseek_processed, processed_at FROM articles LIMIT 10;"
```

### Option 2: Process Specific Article

```bash
# Single article API processing
python3 deepseek/process_one_article.py 6

# Then database integration
python3 deepseek/insert_from_response.py 6 deepseek/responses/article_6_response.json
```

### Option 3: Manual Recovery

```bash
# Check processing status
sqlite3 articles.db "SELECT id, deepseek_processed, deepseek_failed, deepseek_last_error FROM articles WHERE deepseek_processed=0 LIMIT 5;"

# Retry failed article
python3 deepseek/process_one_article.py 10
python3 deepseek/insert_from_response.py 10 deepseek/responses/article_10_response.json

# View HTML response
python3 deepseek/view_response.py 2
# Open: deepseek/deepseek_response_viewer_article_2.html
```

## Monitoring & Validation

**Check Processing Status**:
```sql
-- Articles processed
SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;

-- Articles with errors
SELECT id, title, deepseek_failed, deepseek_last_error 
FROM articles WHERE deepseek_processed=0 LIMIT 5;

-- Response files stored
SELECT response_id, article_id, respons_file FROM response LIMIT 10;
```

**Verify File Organization**:
```bash
# Temporary files
ls -lh deepseek/responses/ | wc -l

# Final files
ls -lh website/article_response/ | wc -l

# Both should match
```

**Validate Response Structure**:
```bash
python3 deepseek/view_response.py 2
# Verify HTML output shows all 4 levels (easy/middle/high/Chinese)
```

## Deployment to Server

### Prerequisites
- Python 3.8+
- SQLite3
- `requests` library installed
- Deepseek API key in database

### Setup Steps

1. **Clone repository**:
   ```bash
   git clone <repo_url>
   cd news
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install requests
   ```

3. **Setup database**:
   ```bash
   # Database should be present as articles.db
   # Ensure apikey table has DeepSeek entry
   sqlite3 articles.db
   > SELECT * FROM apikey;
   ```

4. **Create required directories**:
   ```bash
   mkdir -p website/article_response
   mkdir -p deepseek/responses
   ```

5. **Run pipeline**:
   ```bash
   python3 deepseek/process_one_article.py
   ```

### Server Path Compatibility

All paths are **dynamically computed** from script location:
- Works in `/home/user/news/deepseek/`
- Works in `/var/www/news/deepseek/`
- Works in `/opt/news/deepseek/`
- No hardcoded paths to modify

## Troubleshooting

### API Key Not Found
```
ERROR: DeepSeek API key not found in database
```
**Solution**: 
```sql
INSERT INTO apikey (name, value) VALUES ('DeepSeek', 'your-api-key-here');
```

### Article Not Found
```
ERROR: Article X not found
```
**Solution**: Check if article exists and has content
```sql
SELECT id, title, content FROM articles WHERE id=X;
```

### File Move Failed
```
ERROR: Could not move response file
```
**Solution**: Ensure `website/article_response/` directory exists
```bash
mkdir -p website/article_response
chmod 755 website/article_response
```

### JSON Validation Error
```
WARNING: Response missing level: middle
```
**Solution**: Check API response format in `deepseek/responses/article_X_response.json`

## Performance Notes

- **API Call Duration**: 10-30 seconds per article
- **Batch Processing 10 articles**: ~3-5 minutes
- **Database Operations**: <1 second per article
- **File Move**: <100ms per file

## Future Enhancements

- [ ] Extract keywords, questions, comments to populate related tables
- [ ] Cron job for automated daily processing
- [ ] API rate limiting with queue management
- [ ] Progress dashboard/monitoring
- [ ] Email notifications on batch completion
- [ ] Automated retry logic with backoff
