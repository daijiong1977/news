# Documentation Index - News Pipeline

**Updated**: October 25, 2025

## Document Guide

This index helps you find the right documentation for your needs.

## 📖 Main Documents (Read These First)

### README.md
**Purpose**: Get started and quick reference  
**Length**: ~10KB  
**Read if you want to**: Understand what the project does, run the pipeline, get quick commands  
**Key sections**:
- What this project does
- Quick start commands
- File locations
- Common operations
- Troubleshooting

**Start here if you're**: New to the project, need quick commands, want overview

---

### PIPELINE.md
**Purpose**: Complete documentation of pipeline phases  
**Length**: ~11KB  
**Read if you want to**: Understand each phase in detail, see how logging works, understand data flow  
**Key sections**:
- Pipeline architecture (4 phases)
- Detailed phase explanations
- Logging system documentation
- Database schema changes
- Data flow diagram
- Performance notes

**Start here if you're**: Running the pipeline, debugging issues, understanding the architecture

---

### GROUNDRULE.md
**Purpose**: System architecture and ground truth (READ-ONLY)  
**Length**: ~11KB  
**Read if you want to**: Understand core constraints, database rules, recent fixes, version control  
**Key sections**:
- Core architecture and tech stack
- Database constraints (NON-NEGOTIABLE)
- Pipeline flow (immutable sequence)
- Phase details with current state
- Recent fixes with verification
- Configuration details

**Start here if you're**: Maintaining the system, need to understand core design, reviewing fixes

---

### LATEST_CHANGES.md
**Purpose**: Recent improvements and what's new  
**Length**: ~11KB  
**Read if you want to**: See what changed recently, understand fixes, plan upgrades  
**Key sections**:
- Summary of improvements
- Major fixes (with before/after)
- New features added
- Configuration updates
- Testing & validation
- Migration guide
- Performance improvements

**Start here if you're**: Upgrading from old version, curious about recent fixes, planning maintenance

---

## 📚 Legacy Documents (Deprecated)

These documents are superseded by the ones above. Keep for reference only.

### PIPELINE_LATEST.md
**Superseded by**: PIPELINE.md + README.md  
**Status**: Legacy  
**Keep because**: Historical reference

### PIPELINE_LOGGING.md
**Superseded by**: PIPELINE.md (Logging System section)  
**Status**: Legacy  
**Keep because**: Historical reference

### PIPELINE.md (old version)
**Superseded by**: PIPELINE.md (new version)  
**Status**: Legacy  
**Keep because**: Historical reference

---

## 🎯 Which Document Do I Need?

### By Role

**Project Manager / Non-Technical**
1. Read: README.md → "Overview" section
2. Then: README.md → "Quick Start"
3. Check: "Project Status" section at bottom

**Daily User / Pipeline Operator**
1. Start: README.md → "Quick Start"
2. For details: PIPELINE.md → "Phase Details"
3. Issues: README.md → "Troubleshooting"

**Developer / Maintainer**
1. Review: GROUNDRULE.md → Everything (understand constraints)
2. Details: PIPELINE.md → All sections
3. Recent work: LATEST_CHANGES.md → "Implementation Details"
4. Debugging: Check logs in `/log/` directory

**System Administrator**
1. Architecture: GROUNDRULE.md → "Core Architecture"
2. Database: GROUNDRULE.md → "Database Rules"
3. Operations: README.md → "Common Operations"
4. Troubleshooting: README.md → "Troubleshooting"

---

### By Task

**"I want to run the pipeline"**
→ README.md → Quick Start

**"I want to understand what each phase does"**
→ PIPELINE.md → Phase Details (sections for each phase)

**"The pipeline is failing, what do I do?"**
→ README.md → Troubleshooting → Then check log files

**"What changed recently?"**
→ LATEST_CHANGES.md → Major Fixes (section)

**"I need to know the database schema"**
→ GROUNDRULE.md → Database Layer Constraints

**"How do logs work?"**
→ PIPELINE.md → Logging System (section)

**"What are the system constraints?"**
→ GROUNDRULE.md → Pipeline Flow (IMMUTABLE)

**"I need to migrate from old system"**
→ LATEST_CHANGES.md → Migration Guide

**"What are known limitations?"**
→ LATEST_CHANGES.md → Known Issues & Limitations

**"How long does the pipeline take?"**
→ README.md → Performance → Or → PIPELINE.md → Performance Notes

---

## 📋 Document Checklist

### Documents Currently Available

✅ README.md - Getting started + quick reference  
✅ PIPELINE.md - Complete phase documentation  
✅ GROUNDRULE.md - Architecture & rules (READ-ONLY)  
✅ LATEST_CHANGES.md - Recent improvements  
✅ This file: Documentation Index  

### Legacy Documents (Keep but don't update)

✅ PIPELINE_LATEST.md - Superseded  
✅ PIPELINE_LOGGING.md - Superseded  

---

## 🔄 Document Update Strategy

### Update Frequency

**README.md**: Update when user-facing changes made  
**PIPELINE.md**: Update when phase logic changes  
**GROUNDRULE.md**: **READ-ONLY** - Do not update  
**LATEST_CHANGES.md**: Create new version when major work done  
**This Index**: Update when documents added/removed  

### Version Control

All documents tracked in git branch: `restore/data_load_succ_1`

---

## 📞 Support

### If you can't find what you need:

1. Check README.md → Check for section headings
2. Use Ctrl+F to search within documents
3. Check GROUNDRULE.md → "Important Commands" section
4. Check logs in `/log/` directory for execution details

### If you find errors:

1. Document inconsistency: Update this index
2. Technical error: Check GROUNDRULE.md → "Recent Fixes"
3. Procedure error: Update README.md or PIPELINE.md

---

## 🎓 Quick Navigation

### Find Phase Documentation
- **Phase 1 (Mining)**: PIPELINE.md → PHASE 1: MINING
- **Phase 2 (Images)**: PIPELINE.md → PHASE 2: IMAGE HANDLING
- **Phase 3 (Deepseek)**: PIPELINE.md → PHASE 3: DEEPSEEK PROCESSING
- **Phase 4 (Verify)**: PIPELINE.md → PHASE 4: VERIFICATION

### Find Troubleshooting
- **General**: README.md → Troubleshooting
- **Logging**: PIPELINE.md → Logging System
- **Database**: GROUNDRULE.md → Database Rules
- **Recent issues**: LATEST_CHANGES.md → Known Issues

### Find Configuration
- **API Keys**: GROUNDRULE.md → API Key Storage Rule
- **RSS Feeds**: GROUNDRULE.md → Configuration
- **Database schema**: GROUNDRULE.md → Database Layer Constraints
- **Default parameters**: GROUNDRULE.md → Default Parameters

### Find Commands
- **Quick commands**: README.md → Commands Reference
- **All commands**: README.md → Commands Reference (all sections)
- **Troubleshooting commands**: README.md → Troubleshooting Commands
- **Important commands**: GROUNDRULE.md → Important Commands

---

## 📊 Document Statistics

| Document | Size | Status | Last Updated |
|----------|------|--------|--------------|
| README.md | 10KB | Active | Oct 25, 2025 |
| PIPELINE.md | 11KB | Active | Oct 25, 2025 |
| GROUNDRULE.md | 11KB | READ-ONLY | Oct 25, 2025 |
| LATEST_CHANGES.md | 11KB | Active | Oct 25, 2025 |
| This Index | 3KB | Active | Oct 25, 2025 |

**Total**: ~46KB of active documentation

---

## ✅ Final Checklist

- ✅ README.md - Main entry point for all users
- ✅ PIPELINE.md - Complete technical documentation
- ✅ GROUNDRULE.md - System design (READ-ONLY, final)
- ✅ LATEST_CHANGES.md - Recent work and improvements
- ✅ This Index - Navigate all documents
- ✅ All documents updated for Oct 25, 2025
- ✅ No obsolete information remaining
- ✅ All fixes documented and verified

**Status**: ✅ Documentation Complete and Current

---

**Use this index whenever you need to find specific information about the News Pipeline system.**

