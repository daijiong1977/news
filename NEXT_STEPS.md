# 🚀 NEXT STEPS - EC2 Git Setup

## ⚡ Action Required: Add SSH Key to GitHub

### EC2 SSH Public Key (Generated)
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOS42Pnjp0jLITSUT0zdT5fwTyhfbNzChanEUtpX6iuX ec2-user@news-pipeline
```

### Add to GitHub (Takes 1 minute):

1. Visit: https://github.com/settings/keys
2. Click "New SSH key"
3. Title: `EC2 News Pipeline`
4. Key type: Authentication Key
5. Paste the entire key above
6. Click "Add SSH key"

---

## After Adding SSH Key to GitHub:

Then SSH to your EC2 and run:

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

cd /var/www/news
git pull origin main
```

This will update all files with:
- ✅ Updated `data_collector.py`
- ✅ Updated `process_one_article.py` (with category-specific prompts)
- ✅ New `insert_from_response.py` (with Chinese title fallback)
- ✅ New `prompts_compact.md` (all 5 category prompts)
- ✅ Deployment documentation

---

## Then You Can Start Processing:

```bash
# 1. Collect articles
export DEEPSEEK_API_KEY=your_key
python3 data_collector.py

# 2. Process articles one by one
python3 process_one_article.py

# 3. Insert into database (after verification)
python3 insert_from_response.py response_article_*.json
```

---

**Status:** Ready for EC2 deployment ✅  
**What's needed:** Add SSH key to GitHub (one-time setup)
