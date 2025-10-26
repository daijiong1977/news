-- Migration: Add payload tracking fields to response table
-- Date: 2025-10-26
-- Purpose: Track which articles have had their JSON payloads generated
--          to enable incremental updates and avoid unnecessary regeneration

-- Add payload tracking columns
ALTER TABLE response ADD COLUMN payload_generated INTEGER DEFAULT 0;
ALTER TABLE response ADD COLUMN payload_generated_at TEXT;
ALTER TABLE response ADD COLUMN payload_directory TEXT;

-- Notes:
-- payload_generated: 0 = not generated, 1 = generated
-- payload_generated_at: ISO timestamp when payloads were last generated
-- payload_directory: Directory name (e.g., 'payload_2025102501')

-- To apply this migration:
-- sqlite3 articles.db < dbinit/migration_20251026_payload_tracking.sql

-- To verify:
-- sqlite3 articles.db "PRAGMA table_info(response);"

-- To reset payload flags (force regeneration):
-- UPDATE response SET payload_generated = 0, payload_generated_at = NULL, payload_directory = NULL;

-- To mark specific article for regeneration:
-- UPDATE response SET payload_generated = 0 WHERE article_id = '2025102501';
