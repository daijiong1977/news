# Tools Directory - Complete Reference

This directory contains utility scripts for managing the news pipeline.

## 📖 Documentation Guide

**Which document should you read?**

| Goal | Read This |
|------|-----------|
| Want to understand all tools? | **[TOOL_LIST.md](./TOOL_LIST.md)** |
| Check pipeline progress? | **[CHECK_STATUS_README.md](./CHECK_STATUS_README.md)** |
| Reset everything? | **[RESET_ALL_README.md](./RESET_ALL_README.md)** |
| Other tools (datapurge, etc)? | **[OTHER_TOOLS_README.md](./OTHER_TOOLS_README.md)** |

---

## ⚡ Quick Reference

### Check Status
```bash
python3 tools/check_status.py
```
**Docs:** [CHECK_STATUS_README.md](./CHECK_STATUS_README.md)

### Reset Everything
```bash
python3 tools/reset_all.py --force
```
**Docs:** [RESET_ALL_README.md](./RESET_ALL_README.md)

### Full Tool List
```bash
cat tools/TOOL_LIST.md
```

---

## 📁 Available Tools

| Script | Purpose | Docs |
|--------|---------|------|
| `check_status.py` | Monitor pipeline progress | [📄](./CHECK_STATUS_README.md) |
| `reset_all.py` | ⚠️ Complete system reset | [📄](./RESET_ALL_README.md) |
| `datapurge.py` | Remove specific articles | [📄](./OTHER_TOOLS_README.md) |
| `imgcompress.py` | Compress images for web | [📄](./OTHER_TOOLS_README.md) |
| `pagepurge.py` | Clean HTML pages | [📄](./OTHER_TOOLS_README.md) |

---

## 🎯 Choose Your Task

### I want to...

**...monitor the pipeline**
```bash
python3 tools/check_status.py
```
→ Read [CHECK_STATUS_README.md](./CHECK_STATUS_README.md)

**...start completely fresh**
```bash
python3 tools/reset_all.py --force
```
→ Read [RESET_ALL_README.md](./RESET_ALL_README.md) ⚠️

**...remove one article**
```bash
python3 tools/datapurge.py article_ID
```
→ Read [OTHER_TOOLS_README.md](./OTHER_TOOLS_README.md)

**...compress images**
```bash
python3 tools/imgcompress.py
```
→ Read [OTHER_TOOLS_README.md](./OTHER_TOOLS_README.md)

**...clean HTML pages**
```bash
python3 tools/pagepurge.py
```
→ Read [OTHER_TOOLS_README.md](./OTHER_TOOLS_README.md)

---

## 📚 Full Documentation

### Main Index
- **[TOOL_LIST.md](./TOOL_LIST.md)** - Complete tool reference with all details

### Tool-Specific Docs
- **[CHECK_STATUS_README.md](./CHECK_STATUS_README.md)** - 15 sections, examples, troubleshooting
- **[RESET_ALL_README.md](./RESET_ALL_README.md)** - Safety features, workflows, recovery
- **[OTHER_TOOLS_README.md](./OTHER_TOOLS_README.md)** - Datapurge, Image compress, Page purge

### Legacy Docs (Older format)
- **[RESET_SYSTEM_README.md](./RESET_SYSTEM_README.md)** - Original reset documentation

---

## Documentation Format

Each tool README includes:
- 📋 Overview & purpose
- 🎯 Use cases & when to use
- 📝 Requirements & installation
- 💻 Usage with examples
- 📊 Output explanation
- ⚠️ Error handling
- ⏱️ Performance notes
- 🔧 Integration examples
- 🆘 Troubleshooting
- 📚 Related tools

---

## Getting Help

### Find Information About...

**Status & Monitoring**
```bash
cat tools/CHECK_STATUS_README.md
```

**Resetting & Cleanup**
```bash
cat tools/RESET_ALL_README.md
```

**All Tools Overview**
```bash
cat tools/TOOL_LIST.md
```

**Specific Tool Details**
```bash
python3 tools/check_status.py --help
python3 tools/reset_all.py --help
python3 tools/datapurge.py --help
```

---

## 🚀 Common Tasks

### Monitor Pipeline
```bash
# Quick status check
python3 tools/check_status.py

# Watch every 30 seconds
watch -n 30 'python3 tools/check_status.py'
```

### Fresh Start Workflow
```bash
# 1. Reset everything
python3 tools/reset_all.py --force

# 2. Verify reset
python3 tools/check_status.py

# 3. Run new pipeline
cd /var/www/news && ./run_pipeline.sh
```

### Fix Corrupted Article
```bash
# 1. Check status
python3 tools/check_status.py

# 2. Remove problematic article
python3 tools/datapurge.py article_2025102401

# 3. Verify removal
python3 tools/check_status.py

# 4. Re-run pipeline for that article
```

---

## 📈 Status Dashboard

Quick overview of what's happening:

```bash
python3 tools/check_status.py
```

Shows:
- Total articles in database
- How many have been processed
- Response files on disk
- Progress percentage
- Any errors or issues

---

## 🔐 Safety & Backups

### Before Destructive Operations
```bash
# Always backup first
cp /var/www/news/articles.db backups/articles.db.backup

# Then reset
python3 tools/reset_all.py --force
```

### Recovery
```bash
# Restore from backup
cp backups/articles.db.backup /var/www/news/articles.db

# Verify
python3 tools/check_status.py
```

---

## 📖 Document Organization

```
tools/
├── README.md                    ← You are here
├── TOOL_LIST.md                 ← Start here for overview
├── CHECK_STATUS_README.md       ← Status & monitoring
├── RESET_ALL_README.md          ← System reset (⚠️)
├── OTHER_TOOLS_README.md        ← Other utilities
├── RESET_SYSTEM_README.md       ← Legacy docs
│
├── check_status.py              ← Status checker
├── reset_all.py                 ← Complete reset
├── datapurge.py                 ← Article removal
├── imgcompress.py               ← Image optimization
├── pagepurge.py                 ← Page cleanup
└── __init__.py
```

---

## 📞 Support

**For issues:**

1. Check tool README: `cat tools/<TOOL>_README.md`
2. See Troubleshooting section
3. Review error messages carefully
4. Check file permissions: `ls -la /var/www/news/`
5. Verify database: `python3 tools/check_status.py`

---

**Last Updated:** October 25, 2025
**Latest Tools:** check_status, reset_all, datapurge, imgcompress, pagepurge
**Documentation Status:** ✅ Complete & Current
