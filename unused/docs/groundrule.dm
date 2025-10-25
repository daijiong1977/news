Ground rule: configuration vs code changes
=========================================

When changing operational settings, thresholds, feed lists, or other
behavioral flags, follow this rule:

- Always prefer changing configuration files or configuration tables instead
  of hard-coding values in source code.

Guidelines
---------

- Store numeric thresholds, timeouts, and per-feed settings in `config/`
  JSON/YAML files (for example `config/thresholds.json`) or in a
  configuration table in `articles.db` so they can be edited without a
  code deploy.

- Keep canonical lists (feeds, categories) in `config/` files (`config/feeds.json`,
  `config/verified_feeds.dm`) and use scripts to apply them to the DB.

- If a change requires a code update, first add a configurable key with a
  sensible default; update the code to read the key. That allows operators
  to change behavior immediately and roll back without a new deploy.

- Document each configuration key near the configuration file and in the
  repository docs so future operators know where to edit behavior.

Additional ground rules
=======================

Please follow these operational rules in addition to the configuration
guidance above:

1. No automatic summaries: do not generate or publish article summaries
  unless explicitly requested. Summaries are only produced on-demand.

2. Sync via GitHub: whenever possible, synchronize code changes to the
  production server through GitHub (or the project's canonical SCM). Do
  not manually patch the server without first pushing and PR-ing changes
  through the repository.

3. Backup before DB replace/clean: before replacing, cleaning, or
  restoring `articles.db`, create a timestamped local backup and confirm
  with the operator. Do not perform a destructive DB operation without
  an explicit confirmation step.

4. Confirm schema changes: always ask stakeholders before changing the
  database schema. Schema changes require explicit approval because they
  can break downstream systems.

5. Periodic code and milestone DB backups: create code backups (e.g., a
  branch or archive) every 10–20 minutes while actively developing, and
  create a local DB backup at meaningful milestones (for example before
  large imports, schema changes, or releases).

Timestamp: 2025-10-21
