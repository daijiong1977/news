Local backup ground rules
=========================

This repository contains a live SQLite database (`articles.db`) and
automation that may reinitialize or overwrite it. To avoid accidental
data loss or leaking private data, follow these ground rules:

  operation that overwrites or deletes `articles.db`.
  repositories (e.g., GitHub). Backups are stored under the `backups/`
  directory by scripts in this repository and that directory is excluded
  in `.gitignore`.
  rotate or remove them when no longer needed.

Why
The database may contain scraped content, URLs, or other data you do not
want stored in a public repo. Local backups protect you from accidental
deletes while preventing accidental syncs to remote services.

Quick checklist
1. Before reinitializing the DB, ensure the script prints a message like:

   "Created DB backup: backups/articles_db_backup_YYYYMMDDTHHMMSSZ.db"

2. Confirm `backups/` exists and is listed in `.gitignore`.
3. Do NOT `git add backups/` or commit `articles.db` unless you have an
   explicit, documented reason and have sanitized the DB.

Configuration changes

  settings, prefer editing configuration files (for example files under
  `config/`) or updating configuration tables in the database rather than
  hard-coding values in Python source files. This makes changes auditable,
  reversible, and safer to deploy.

  a configuration value? If yes, add the value to the appropriate
  configuration file or table, and update the code to read from that
  configuration location.

  in the repository docs so future operators know where to change behavior.

Timestamp: 2025-10-21

Local backup ground rules
=========================

This repository contains a live SQLite database (`articles.db`) and
automation that may reinitialize or overwrite it. To avoid accidental
data loss or leaking private data, follow these ground rules:

- Always create a local, timestamped backup before any destructive
  operation that overwrites or deletes `articles.db`.
- Backups are local-only and MUST NOT be committed or pushed to remote
  repositories (e.g., GitHub). Backups are stored under the `backups/`
  directory by scripts in this repository and that directory is excluded
  in `.gitignore`.
- Treat backups as sensitive: keep them on your local machine and
  rotate or remove them when no longer needed.

Why
---
The database may contain scraped content, URLs, or other data you do not
want stored in a public repo. Local backups protect you from accidental
deletes while preventing accidental syncs to remote services.

Quick checklist
---------------
1. Before reinitializing the DB, ensure the script prints a message like:

   "Created DB backup: backups/articles_db_backup_YYYYMMDDTHHMMSSZ.db"

2. Confirm `backups/` exists and is listed in `.gitignore`.
3. Do NOT `git add backups/` or commit `articles.db` unless you have an
   explicit, documented reason and have sanitized the DB.

Timestamp: 2025-10-21
