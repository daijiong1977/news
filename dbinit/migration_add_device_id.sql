-- Add device_id column to user_subscriptions
-- Created: 2025-10-26
-- Purpose: Store device_id for offline token generation and user identification

-- Add device_id column (16+ characters, unique identifier)
-- Note: SQLite doesn't support adding UNIQUE constraint via ALTER TABLE
-- So we add column first, then create unique index
ALTER TABLE user_subscriptions ADD COLUMN device_id TEXT;

-- Create unique index for device_id (enforces uniqueness)
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_subscriptions_device_id ON user_subscriptions(device_id);
