# GitHub-First Development Workflow

This document describes the proper workflow for making changes to the news pipeline system.

## Workflow Summary

```
Local Development → GitHub Push → Server Pull → Run Pipeline
```

## Step-by-Step Process

### 1. Make Changes Locally

Edit files on your Mac/local machine:
```bash
cd /Users/jidai/news
# Edit your files
```

### 2. Test Locally (Optional)

```bash
python3 run_full_pipeline.py --test
```

### 3. Commit to Git Locally

```bash
git add .
git commit -m "feat: description of changes"
```

### 4. Push to GitHub

```bash
git push origin main
```

### 5. Deploy to Server Using Script

```bash
./deploy_to_server.sh
```

This script will:
- Verify all changes are committed
- Push to GitHub
- SSH to server
- Pull latest code from GitHub
- Show sync status

### Alternative: Manual Server Update

If the deployment script fails, manually update:

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 << 'EOF'
cd /var/www/news
# Option A: If SSH keys configured for git
git pull origin main

# Option B: Manual file copy (use SCP for critical files)
scp -i ~/Downloads/web1.pem /Users/jidai/news/run_full_pipeline.py ec2-user@18.223.121.227:/var/www/news/
EOF
```

## Smart Pipeline Features

### Duplicate Detection
- **Crawl Step**: Checks for articles by title before adding
- **Display**: Shows "⊘ Skipped (duplicate)" for duplicates
- **Benefit**: No duplicate articles in database

### Smart Deepseek Processing
- **Only processes** articles that haven't been analyzed yet
- **Checks flag**: `deepseek_processed = 0`
- **Display**: Shows "Already analyzed: N" and "Processing M articles"
- **Benefit**: Saves API calls and time

### Partial Rerun Support
You can rerun the pipeline anytime:
- New articles automatically added (others skipped)
- Only unprocessed articles sent to Deepseek
- HTML pages regenerated for all articles
- Safe to run multiple times

## Example Output

```
STEP 1: CRAWLING RSS SOURCES
Source: PBS NewsHour
  ✓ Added: New article title...
  ⊘ Skipped (duplicate): Existing article...

STEP 2: FETCHING ARTICLE CONTENT
Fetching content for 1 articles...
  ✓ Fetched: New article title...

STEP 3: PROCESSING WITH DEEPSEEK API
Total articles with content: 23
Already analyzed: 22
Processing 1 articles through Deepseek...
  ⊘ Skipped (already analyzed): Article 1...
  ⊘ Skipped (already analyzed): Article 2...
  Processing: New article title...
```

## File Tracking

**Always tracked in Git:**
- `run_full_pipeline.py` - Pipeline code
- `main_articles_interface_v2.html` - Frontend interface
- `*.py` scripts
- `.gitignore`, configs, docs

**Never tracked (in .gitignore):**
- `articles.db` - Database (server-specific)
- `output/` - Generated HTML files
- `logs/` - Pipeline logs
- `.DS_Store` - macOS files

## Best Practices

✅ **DO:**
- Commit all code changes before deploying
- Use the deployment script for consistency
- Make changes on local machine first
- Test locally when possible
- Write descriptive commit messages

❌ **DON'T:**
- Edit files directly on server
- Push database files to GitHub
- Skip testing locally
- Mix uncommitted changes with deployments

## Troubleshooting

### Deployment script fails at git pull
- Server may not have GitHub SSH keys configured
- This is expected - code sync still works partially
- Manual sync required for some files

### Changes not appearing on server
- Check git status: `git status`
- Verify commit was pushed: `git log --oneline`
- Run deployment script: `./deploy_to_server.sh`

### Need to undo changes
```bash
git reset --soft HEAD~1  # Undo last commit, keep changes
git reset --hard HEAD~1  # Undo last commit, discard changes
git revert HEAD           # Create new commit that undoes last
```
