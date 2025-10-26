# News Oh, Ye! - Complete System Documentation

**Automated News Processing and Website Generation**

*Dedicated to Helen, Daisy & Mattie*

**Status**: ✅ Production Ready  
**Last Updated**: October 26, 2025  
**Repository**: https://github.com/daijiong1977/news  
**Production Site**: https://news.6ray.com

---

## Production Server Access

```bash
# SSH to production server
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

# Website directory
cd /var/www/news

# Pull latest code
git pull origin en_gen_suc_2

# Deploy updated HTML files
cp webback/index.html website/
cp webback/archive.html website/main/
cp webback/article.html website/article_page/
```

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [Complete Workflow](#complete-workflow)
4. [One-Time Setup (HTML Generation)](#one-time-setup-html-generation)
5. [Daily Pipeline (Automated)](#daily-pipeline-automated)
6. [Directory Structure](#directory-structure)
7. [Deployment](#deployment)

---

## Quick Start

### Daily Pipeline (Automated)
```bash
# Run complete pipeline with payload generation
python3 pipeline.py --full --articles-per-seed 3

# This will execute:
# 1. Mining (collect articles)
# 2. Image optimization
# 3. AI processing (Deepseek)
# 4. Payload generation (article + main page)
# 5. Verification
```

### One-Time HTML Generation
```bash
# Generate article page template (run once)
python3 genpage/batch_generate_articles.py

# Generate main page template (run once)  
python3 genweb/enhance_generate.py
```

---

## System Overview

**What This System Does:**

1. ✅ **Collects** articles from 6 RSS feeds (BBC, PBS, Science Daily, TechRadar)
2. ✅ **Optimizes** images (web: 1920×1440, mobile: 1024×768 WebP <60KB)
3. ✅ **Analyzes** with Deepseek AI (easy/middle/high + Chinese)
4. ✅ **Generates** interactive article pages with quizzes and games
5. ✅ **Publishes** responsive main page with dynamic loading

---

## Complete Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                ONE-TIME SETUP (Manual)                        │
│  Run when deploying or updating HTML templates               │
├──────────────────────────────────────────────────────────────┤
│  Step 4: Generate HTML Templates                             │
│    • Article page: python3 genpage/batch_generate_articles.py│
│    • Main page: python3 genweb/enhance_generate.py           │
│  Output: article.html, index.html                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│            DAILY AUTOMATED PIPELINE                           │
│  Run via cron or manual: python3 pipeline.py --full          │
├──────────────────────────────────────────────────────────────┤
│  Step 1: MINING                                               │
│    Script: mining/run_mining_cycle.py                         │
│    • Fetch articles from RSS feeds                            │
│    • Download images                                          │
│    • Store in database                                        │
│    Output: 18 articles + images                               │
├──────────────────────────────────────────────────────────────┤
│  Step 2: IMAGE HANDLING                                       │
│    Script: tools/imgcompress.py                               │
│    • Optimize for web (1920×1440)                             │
│    • Create mobile WebP (1024×768, <60KB)                     │
│    Output: Optimized images                                   │
├──────────────────────────────────────────────────────────────┤
│  Step 3: AI PROCESSING                                        │
│    Scripts: deepseek/process_one_article.py                   │
│             deepseek/insert_from_response.py                  │
│    • Analyze at 3 levels (easy/middle/high)                   │
│    • Generate Chinese translation                             │
│    • Create keywords, quizzes, perspectives                   │
│    • Insert responses into database                           │
│    Output: JSON responses + DB updates                        │
├──────────────────────────────────────────────────────────────┤
│  Step 5: GENERATE PAYLOADS (NEW - TO BE ADDED)               │
│    Scripts: genpage/batch_generate_json_payloads.py           │
│             genweb/enhance_generate.py                        │
│    • Create article page JSON payloads                        │
│    • Update main page JSON payloads                           │
│    Output: Updated JSON for dynamic loading                   │
└──────────────────────────────────────────────────────────────┘
```

---

## One-Time Setup (HTML Generation)

These scripts generate the **HTML templates**. Run once during deployment or when updating designs.

### Step 4a: Generate Article Page Template

```bash
python3 genpage/batch_generate_articles.py
```

**Creates:** `website/article_page/article.html`

**Features:**
- Interactive keyword highlighting with tooltips
- Keyword matching game (5 words, stars/percentage)
- Randomized quiz with A/B/C/D answers
- Background analysis (one sentence per paragraph)
- Article structure:
  - Easy: WHO/WHAT/WHERE/WHEN/WHY/HOW table
  - Middle/High: Paragraph format
- Green highlights for: Main Points, Purpose, Methodology, Evidence, established

**When to run:**
- Initial deployment
- Updating article page design
- Adding new features

### Step 4b: Generate Main Page Template

```bash
python3 genweb/enhance_generate.py
```

**Creates:** `website/main/index.html` + initial payloads

**Features:**
- Article cards with clickable images
- "Activities →" links (disabled for CN mode)
- Difficulty selector: Relax/Enjoy/Research
- Language toggle: EN/CN
- Dynamic payload loading
- Footer: "Dedicated to Helen, Daisy & Mattie"

**When to run:**
- Initial deployment
- Updating main page design
- Major layout changes

---

## Daily Pipeline (Automated)

This runs **automatically** via cron or manually for updates.

### Full Pipeline Command

```bash
# Recommended daily run
python3 pipeline.py --full --articles-per-seed 3

# With options
python3 pipeline.py --full -v                    # Verbose
python3 pipeline.py --full --dry-run             # Preview
```

### Phase Details

#### Phase 1: Mining
- **Script:** `mining/run_mining_cycle.py`
- **Output:** 18 articles (3 per source) + images
- **Sources:** BBC (3), PBS (3), Science Daily (3), TechRadar (3), etc.
- **Log:** `log/phase_mining_YYYYMMDD_HHMMSS.log`

#### Phase 2: Image Handling
- **Script:** `tools/imgcompress.py`
- **Output:** Optimized web + mobile images
- **Mobile format:** 1024×768 WebP <60KB
- **Log:** `log/phase_image_handling_YYYYMMDD_HHMMSS.log`

#### Phase 3: AI Processing
- **Scripts:** 
  - `deepseek/process_one_article.py` (API calls)
  - `deepseek/insert_from_response.py` (DB insertion)
- **Output:** JSON responses in `website/responses/`
- **Generates:**
  - Easy/Middle/High difficulty levels
  - Chinese translation
  - Keywords (10-15 per article)
  - Quiz questions (5-10 per article)
  - Perspectives and structure analysis
- **Log:** `log/phase_deepseek_YYYYMMDD_HHMMSS.log`

#### Phase 5: Generate Payloads (TO BE ADDED TO PIPELINE)

**YOU ARE CORRECT - This should be added to pipeline.py!**

##### 5a. Article Page Payloads

```bash
python3 genpage/batch_generate_json_payloads.py
```

**Creates:** `website/article_page/payload_ARTICLEID/`
- `easy.json` - Easy difficulty content
- `middle.json` - Middle difficulty content  
- `high.json` - High difficulty content

**Contains:**
- Article title, summary, full text
- Keywords with explanations
- Quiz questions with randomized options
- Background analysis
- Article structure
- Perspectives

**When to run:**
- After Phase 3 (Deepseek processing)
- **Should be integrated into daily pipeline**

##### 5b. Main Page Payloads

```bash
python3 genweb/enhance_generate.py
```

**Creates:** `website/main/payloads_YYYYMMDD_HHMMSS/`
- `articles_news_easy.json`
- `articles_news_middle.json`
- `articles_news_high.json`
- `articles_news_cn.json`
- (Same for science and fun categories)

**Contains:**
- Latest 3 articles per source
- Article cards data (id, title, summary, image, source, time)
- Balanced source representation

**Updates:** `website/main/index.html` to point to new payload directory

**When to run:**
- After Phase 5a (article payloads)
- **Should be integrated into daily pipeline**

---

## Why Separate HTML Generation and Payload Generation?

### HTML Templates (Step 4 - One-time, Manual)
- `genpage/batch_generate_articles.py` → Creates `article.html`
- `genweb/enhance_generate.py` → Creates `index.html` template

**Run manually when:**
- Deploying the site
- Updating design/layout
- Adding new interactive features

**These are TEMPLATES** - the structure doesn't change daily.

### JSON Payloads (Step 5 - Daily, Automated)
- `genpage/batch_generate_json_payloads.py` → Updates article JSON
- `genweb/enhance_generate.py` → Updates main page JSON

**Run automatically when:**
- New articles are processed
- Content needs refreshing
- Daily updates

**These are DATA** - the content changes daily.

---

## Directory Structure

```
/Users/jidai/news/
├── pipeline.py                          # Main orchestrator
├── articles.db                          # SQLite database
│
├── mining/                              # Phase 1
│   └── run_mining_cycle.py
│
├── tools/                               # Phase 2
│   └── imgcompress.py
│
├── deepseek/                            # Phase 3
│   ├── process_one_article.py
│   └── insert_from_response.py
│
├── genpage/                             # Article pages
│   ├── batch_generate_articles.py      # HTML template (once)
│   ├── batch_generate_json_payloads.py # JSON payloads (daily)
│   └── article.html                    # Backup
│
├── genweb/                              # Main page
│   ├── enhance_generate.py             # HTML + payloads
│   └── main_template.html              # Base template
│
├── website/                             # Published files
│   ├── article_image/                  # Images
│   ├── responses/                      # AI responses
│   │
│   ├── article_page/                   # Article pages
│   │   ├── article.html                # Template
│   │   └── payload_YYYYMMDDNN/         # Per-article JSON
│   │       ├── easy.json
│   │       ├── middle.json
│   │       └── high.json
│   │
│   └── main/                           # Main page
│       ├── index.html                  # Main template
│       └── payloads_YYYYMMDD_HHMMSS/   # Timestamped data
│           ├── articles_news_*.json
│           ├── articles_science_*.json
│           └── articles_fun_*.json
│
└── log/                                 # Pipeline logs
    ├── phase_mining_*.log
    ├── phase_image_handling_*.log
    ├── phase_deepseek_*.log
    └── pipeline_results_*.json
```

---

## Deployment

### Daily Automated Updates (Cron)

```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * cd /Users/jidai/news && python3 pipeline.py --full --articles-per-seed 3 >> /Users/jidai/news/log/cron.log 2>&1
```

### Production Server

```bash
# Deploy to server
cd /Users/jidai/news/deploy
./deploy_news.sh

# Configure Nginx
sudo cp nginx-news.6ray.com-ssl.conf /etc/nginx/sites-available/
sudo systemctl reload nginx
```

---

## Monitoring

```bash
# View latest pipeline results
tail -100 log/pipeline_results_*.json | jq .

# Check specific phase
tail -50 log/phase_deepseek_*.log

# Count processed articles
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1;"

# Verify payloads exist
ls -la website/article_page/payload_*/
ls -la website/main/payloads_*/
```

---

## Summary: Your Understanding is Correct!

**You are RIGHT:**

1. ✅ **HTML generation (Step 4)** - Run **ONCE** manually when deploying
2. ✅ **Payload generation (Step 5)** - Should be **ADDED TO PIPELINE** for daily automation

**Recommended pipeline.py update:**
1. Mining
2. Image handling
3. AI processing (Deepseek)
4. **Generate article payloads** ← ADD THIS
5. **Update main page payloads** ← ADD THIS
6. Verification

**This way:**
- HTML templates stay stable
- JSON data updates daily automatically
- No manual intervention needed!

---

## Credits

**Developer:** Jidai  
**Dedicated to:** Helen, Daisy & Mattie  
**AI Partner:** Deepseek v3  
**Repository:** github.com/daijiong1977/news

---

*Last updated: October 26, 2025*
