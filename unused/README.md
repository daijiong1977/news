News project — local backup

This repository contains the Daily Digest / DeepSeek processing code.

Quick start:

1. Create a Python venv and install dependencies (if any).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set your DeepSeek API key in environment:

```bash
export DEEPSEEK_API_KEY="sk-<your-key>"
```

3. Run DeepSeek processor:

```bash
python3 deepseek_processor.py
```

Notes:
- Sensitive files (databases, logs, secrets) are excluded by `.gitignore`.
- This is a local backup. To push to GitHub, create a remote repo and push.
