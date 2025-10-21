# GitHub Actions Deployment Setup

## Overview

The automated deployment workflow (`.github/workflows/deploy.yml`) automatically syncs your code to the EC2 server whenever you push to the `main` branch.

**What it does:**
1. Detects push to `main` branch
2. Connects to EC2 via SSH
3. Pulls latest code from GitHub
4. Updates repository on server

---

## Required GitHub Secrets Setup

You need to configure 4 secrets in your GitHub repository settings. Here's how:

### Step 1: Go to Repository Settings

1. Open https://github.com/daijiong1977/news
2. Click **Settings** (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)

### Step 2: Create `EC2_HOST` Secret

**Value:** Your EC2 public IP address

```
18.223.121.227
```

**How to add:**
1. Click **New repository secret**
2. Name: `EC2_HOST`
3. Secret: `18.223.121.227`
4. Click **Add secret**

### Step 3: Create `EC2_USER` Secret

**Value:** EC2 username

```
ec2-user
```

**How to add:**
1. Click **New repository secret**
2. Name: `EC2_USER`
3. Secret: `ec2-user`
4. Click **Add secret**

### Step 4: Create `EC2_PORT` Secret

**Value:** SSH port (usually 22)

```
22
```

**How to add:**
1. Click **New repository secret**
2. Name: `EC2_PORT`
3. Secret: `22`
4. Click **Add secret**

### Step 5: Create `EC2_SSH_KEY` Secret (Most Important!)

**Value:** Contents of your private SSH key

**How to get your SSH key:**

On your Mac:

```bash
cat ~/Downloads/web1.pem
```

This will display the key contents. It looks like:

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
[many lines of key data]
...
-----END RSA PRIVATE KEY-----
```

**How to add:**
1. Click **New repository secret**
2. Name: `EC2_SSH_KEY`
3. Secret: **Paste the ENTIRE contents of web1.pem** (all lines including BEGIN and END)
4. Click **Add secret**

⚠️ **IMPORTANT:** Make sure to include the entire key, including:
- `-----BEGIN RSA PRIVATE KEY-----`
- All the key data
- `-----END RSA PRIVATE KEY-----`

---

## Verification Checklist

After adding all secrets, verify:

```
✓ EC2_HOST = 18.223.121.227
✓ EC2_USER = ec2-user
✓ EC2_PORT = 22
✓ EC2_SSH_KEY = [full private key content]
```

---

## Testing the Deployment

### Option 1: Trigger Manually via GitHub UI

1. Go to **Actions** tab in your repository
2. Click **Deploy to EC2** workflow
3. Click **Run workflow** → **Run workflow**

### Option 2: Trigger via Git Push

Simply push code to main branch:

```bash
git push origin main
```

The workflow will automatically trigger.

---

## Monitoring Deployment Status

1. Go to **Actions** tab in your repository
2. Click the workflow run
3. Watch the job progress in real-time

**Expected output:**
```
✓ Checkout
✓ Deploy to EC2
  cd /var/www/news
  git fetch origin main
  git reset --hard origin/main
  ✓ Repository updated to latest commit
  ✓ Deploy complete at [timestamp]
```

---

## Troubleshooting

### "All jobs have failed" Error

**Common causes:**

1. **Missing or incorrect secrets**
   - Solution: Verify all 4 secrets are added and have correct values
   - EC2_SSH_KEY must include the full private key (BEGIN and END lines)

2. **SSH key permissions**
   - The key needs 600 permissions
   - Mac default: usually correct
   - If issues: `chmod 600 ~/Downloads/web1.pem`

3. **EC2 not accepting SSH connection**
   - Test manually: `ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227`
   - If fails, EC2 may have security group restrictions

4. **Repository not cloned to /var/www/news**
   - The workflow assumes repo is already at `/var/www/news`
   - If first time, manually clone: 
     ```bash
     ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
     mkdir -p /var/www
     cd /var/www
     git clone https://github.com/daijiong1977/news.git
     ```

5. **Git SSH authentication failing**
   - Make sure repository is PUBLIC (✓ already done)
   - Non-public repos need different setup

### Viewing Detailed Logs

1. Click on the failed workflow run
2. Click **Deploy to EC2** job
3. Expand any step to see full output
4. Look for error messages

### Manual SSH Test

Test SSH connection directly:

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227 "cd /var/www/news && git status"
```

---

## Workflow Details

### File: `.github/workflows/deploy.yml`

Current workflow:
```yaml
on:
  push:
    branches: [ main ]  # Triggers on any push to main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - SSH to EC2 and run:
        * cd /var/www/news
        * git fetch origin main
        * git reset --hard origin/main
```

**This means:**
- ✅ Every `git push origin main` auto-deploys
- ✅ Always syncs to latest code
- ✅ No manual SSH needed after setup
- ✅ Logs available in Actions tab

### Customization

To modify when deployment triggers, edit `.github/workflows/deploy.yml`:

**Deploy on all branches:**
```yaml
on:
  push:
    branches: [ '**' ]
```

**Deploy only on specific branch:**
```yaml
on:
  push:
    branches: [ main, production ]
```

**Deploy on pull request (optional):**
```yaml
on:
  pull_request:
    branches: [ main ]
```

---

## Best Practices

1. **Always test locally first**
   - Run scripts locally before pushing
   - Test with `npm run build` for React

2. **Use meaningful commit messages**
   - Makes it easier to track deployments

3. **Monitor first few deployments**
   - Check Actions tab after each push
   - Verify changes on EC2

4. **Keep SSH key secure**
   - Never commit `web1.pem` to Git
   - GitHub secrets are encrypted
   - Only admins can see secret values

5. **Backup before major changes**
   - SSH into EC2 and backup important files
   - Keep database backups

---

## Automation Flow

```
1. Developer pushes code
   git push origin main
                ↓
2. GitHub detects push to main
   Webhook triggers
                ↓
3. GitHub Actions workflow starts
   ubuntu-latest runner spins up
                ↓
4. Workflow executes SSH action
   Connects to 18.223.121.227 as ec2-user
                ↓
5. Commands run on EC2
   git fetch && git reset
                ↓
6. Server has latest code
   Ready to use immediately
```

---

## Next Steps

1. **Add all 4 secrets to GitHub**
2. **Test with a small commit**
3. **Verify deployment in Actions tab**
4. **Check EC2 server to confirm code updated**

---

## Support

If deployment still fails after setup:

1. Check GitHub Actions logs (detailed error messages)
2. Verify EC2 security group allows SSH (port 22)
3. Confirm SSH key is correct: `ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227`
4. Check repository is PUBLIC

