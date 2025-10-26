# Ground Rules for This Project

## Core Principles

### 1. Summaries
- **Do NOT generate summaries** unless explicitly asked
- Wait for user confirmation before providing summarized information
- Only provide what was directly requested

### 2. Database Schema Changes
- **Never modify database schema** except when explicitly confirmed
- Schema changes are **isolated tasks** - do not mix with other jobs
- Require explicit confirmation before any schema modifications
- Document schema changes separately with clear reasoning

### 3. Task Execution
- **Do exactly what is asked** - no more, no less
- Do not add "helpful" extras or improvements without being asked
- Follow instructions precisely as stated
- Clarify ambiguous requests before proceeding

### 4. Database File Safety
- **Treat database files with extreme caution**
- Never override or delete DB files without **double confirmation**
- Always create backups before any destructive operations
- Verify backup success before making changes
- Document all DB operations clearly

### 5. Code Synchronization (Local ↔ EC2 Server)
- **Always use git push/pull** for syncing code between local and EC2
- No direct file transfers or manual syncing except with **double confirmation**
- Maintain clean git history with meaningful commit messages
- Test locally before pushing to production server

### 6. Git & Deployment Operations ⚠️ **CRITICAL**
**NEVER DO ANY OF THESE WITHOUT EXPLICIT PERMISSION:**
- ❌ **NO git commits** to local repository
- ❌ **NO git pushes** to GitHub remote
- ❌ **NO deployments to EC2** server
- ❌ **NO scp/ssh operations** to EC2
- ❌ **NO file transfers** to EC2

**ALWAYS:**
- ✅ Ask for explicit permission first
- ✅ Explain what you plan to do
- ✅ Wait for "yes" or "proceed" before executing
- ✅ Test locally ONLY before asking permission
- ✅ Keep all changes local until approved

**Example workflow:**
1. Make changes locally
2. Test changes locally
3. Tell user: "I've tested X locally. Ready to commit/push/deploy. Should I proceed?"
4. **WAIT for user approval**
5. Only execute after explicit "yes"

## Standard Workflow

1. **Receive request** → Clarify if needed
2. **Execute exactly as requested** → No additions
3. **Report results** → No unnecessary summaries
4. **Wait for next instruction** → Do not assume next steps

## Safety Checklist

- [ ] DB file backup created before modifications
- [ ] Schema changes documented separately
- [ ] Git commits have clear messages
- [ ] No file overrides without double confirmation
- [ ] Code synced via git only

## Exceptions

Any deviation from these rules requires **explicit double confirmation** from the user.
