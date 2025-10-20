# 🚀 EC2 QUICK START - Database Rebuild & Article Processing

## Prerequisites

✅ SSH key added to GitHub (from previous step)  
✅ EC2 server running at 18.223.121.227  
✅ Code in `/var/www/news`

---

## Step 1: Pull Latest Code (First Time Only)

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

cd /var/www/news
git pull origin main
```

This will get:
- `ec2_setup_db.sh` - Database rebuild script
- `process_all_articles.sh` - Automated processing script
- All updated processing code

---

## Step 2: Rebuild Database & Collect Articles

On your EC2 server, run:

```bash
cd /var/www/news
bash ec2_setup_db.sh
```

**What it does:**
1. ✅ Backs up existing database (just in case)
2. ✅ Removes old database
3. ✅ Creates fresh schema (19 tables)
4. ✅ Collects articles from RSS feeds
5. ✅ Shows summary of collected articles

**Example output:**
```
📊 Total articles collected: 4

  [1] Article Title 1... (Cat: 1) ⏳ Ready
  [2] Article Title 2... (Cat: 4) ⏳ Ready
  [3] Article Title 3... (Cat: 5) ⏳ Ready
  [4] Article Title 4... (Cat: 6) ⏳ Ready
```

---

## Step 3: Process All Articles with Deepseek API

On EC2, set your API key and run:

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key_here

cd /var/www/news
bash process_all_articles.sh
```

**What it does:**
1. ✅ Gets first unprocessed article
2. ✅ Calls Deepseek API with category-specific prompt
3. ✅ Saves response to file
4. ✅ Inserts all data into database
5. ✅ Repeats for each article
6. ✅ Shows final statistics

**Processing time:** ~30-60 seconds per article (depending on API speed)

**Example output:**
```
Processing article 1 of 4...

[Step 1] Generating API response...
✓ Response: 28KB

[Step 2] Inserting into database...
✓ Inserted 199 records

Article 1 processed successfully
```

---

## Step 4: Verify Results

After processing completes, check the database:

```bash
cd /var/www/news
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('articles.db')
c = conn.cursor()

# Check articles
c.execute('SELECT COUNT(*) FROM articles WHERE deepseek_processed=1')
print(f"✅ Processed articles: {c.fetchone()[0]}")

# Check data
tables = ['article_summaries', 'keywords', 'questions', 'choices', 'comments', 'background_read', 'article_analysis']
for table in tables:
    c.execute(f'SELECT COUNT(*) FROM {table}')
    count = c.fetchone()[0]
    print(f"   {table}: {count} rows")

conn.close()
EOF
```

---

## Expected Results (After 4 Articles)

```
✅ Processed articles: 4

Data counts:
   article_summaries: ~16 rows (4 per article: 3 EN + 1 ZH)
   keywords: ~120 rows (30 per article)
   questions: ~120 rows (30 per article)
   choices: ~480 rows (120 per article)
   comments: ~36 rows (9 per article)
   background_read: ~12 rows (3 per article)
   article_analysis: ~8 rows (2 per article)

Total: ~796 records from 4 articles
```

---

## Manual Processing (If Needed)

If you want to process articles one by one for verification:

```bash
export DEEPSEEK_API_KEY=your_key

# Generate response
python3 process_one_article.py

# Verify response file
ls -lh response_article_*.json

# Insert into database
python3 insert_from_response.py response_article_*.json
```

---

## One-Liner (Complete Setup)

To do everything in one command:

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'SETUP'
export DEEPSEEK_API_KEY=your_api_key_here
cd /var/www/news
git pull origin main
bash ec2_setup_db.sh
bash process_all_articles.sh
SETUP
```

---

## Troubleshooting

### Git pull fails
- Make sure SSH key is added to GitHub (settings/keys)
- Test: `ssh -T git@github.com`

### API timeouts
- Check network: `ping google.com`
- API key valid: `echo $DEEPSEEK_API_KEY`
- Try processing again (might be temporary)

### Database locked
- Kill any stuck processes: `pkill -f process_one_article.py`
- Try again

### Missing files
- Run: `git pull origin main` to get latest

---

## Files on EC2

Located at `/var/www/news`:
- `articles.db` - SQLite database (created by ec2_setup_db.sh)
- `init_db.py` - Database schema initialization
- `data_collector.py` - RSS article collection
- `process_one_article.py` - Deepseek API processing
- `insert_from_response.py` - Database insertion
- `prompts_compact.md` - Category-specific prompts
- `config.json` - RSS feed configuration
- `ec2_setup_db.sh` - Setup script
- `process_all_articles.sh` - Processing script

---

**Ready?** Let's go! 🚀

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
cd /var/www/news
bash ec2_setup_db.sh
```
