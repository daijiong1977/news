# EC2 GitHub SSH Setup - October 20, 2025

## Summary

SSH key pair has been generated on your EC2 server for GitHub authentication.

**Key Details:**
- **Type:** ED25519 (modern, secure)
- **Location:** `/home/ec2-user/.ssh/id_ed25519`
- **Server:** ec2-user@18.223.121.227 (`/var/www/news`)

---

## EC2 Public Key (Add to GitHub)

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOS42Pnjp0jLITSUT0zdT5fwTyhfbNzChanEUtpX6iuX ec2-user@news-pipeline
```

### Steps to Add to GitHub:

1. Go to **GitHub Settings** → **SSH and GPG keys** → https://github.com/settings/keys
2. Click **New SSH key**
3. **Title:** `EC2 News Pipeline - 18.223.121.227`
4. **Key type:** Authentication Key
5. **Key:** Paste the entire `ssh-ed25519 AAAAC3N...` line from above
6. Click **Add SSH key**

---

## Test Git Pull on EC2

After adding the SSH key to GitHub, run this on EC2:

```bash
cd /var/www/news
git pull origin main
```

---

## What's Next

Once SSH key is added to GitHub:

1. **Pull latest files:**
   ```bash
   ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
   cd /var/www/news
   git pull origin main
   ```

2. **Copy the new processing scripts** (if git pull alone isn't enough):
   ```bash
   scp -i ~/Downloads/web1.pem /Users/jidai/news/data_collector.py ec2-user@18.223.121.227:/var/www/news/
   scp -i ~/Downloads/web1.pem /Users/jidai/news/process_one_article.py ec2-user@18.223.121.227:/var/www/news/
   scp -i ~/Downloads/web1.pem /Users/jidai/news/insert_from_response.py ec2-user@18.223.121.227:/var/www/news/
   scp -i ~/Downloads/web1.pem /Users/jidai/news/prompts_compact.md ec2-user@18.223.121.227:/var/www/news/
   ```

3. **Check database status:**
   ```bash
   cd /var/www/news
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('articles.db')
   c = conn.cursor()
   c.execute('SELECT COUNT(*) FROM articles')
   total = c.fetchone()[0]
   c.execute('SELECT SUM(CASE WHEN deepseek_processed=1 THEN 1 ELSE 0 END) FROM articles')
   processed = c.fetchone()[0] or 0
   print(f'Articles: {total} total, {processed} processed')
   conn.close()
   "
   ```

4. **Collect articles:**
   ```bash
   cd /var/www/news
   export DEEPSEEK_API_KEY=your_api_key_here
   python3 data_collector.py
   ```

5. **Process articles:**
   ```bash
   python3 process_one_article.py
   python3 insert_from_response.py response_article_*.json
   ```

---

## Git Configuration on EC2

Already configured:
- **Email:** ec2-user@6ray.com
- **Name:** EC2 News Pipeline
- **GitHub:** Added to known_hosts

---

## Files Status on EC2

**Location:** `/var/www/news`

**Files Present:**
- ✅ `init_db.py` (exists)
- ❌ `data_collector.py` (needs to be updated)
- ❌ `process_one_article.py` (needs to be updated)
- ❌ `insert_from_response.py` (needs to be added)
- ❌ `prompts_compact.md` (needs to be added)
- ✅ `config.json` (likely exists)
- ✅ `articles.db` (database already initialized)

**After git pull, all files will be updated.**

---

**Setup Date:** October 20, 2025  
**Status:** ✅ SSH key generated, ready for GitHub authentication
