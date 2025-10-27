-- User Subscription System Migration
-- Created: 2025-10-26
-- Purpose: Add user subscription and statistics tracking tables

-- Table 1: user_subscriptions
-- Stores email subscribers for newsletter delivery
CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    reading_style TEXT CHECK(reading_style IN ('relax', 'enjoy', 'research', 'chinese')),
    bootstrap_token TEXT,
    bootstrap_failed INTEGER DEFAULT 0,
    subscription_status TEXT DEFAULT 'pending' CHECK(subscription_status IN ('pending', 'active', 'cancelled')),
    verified INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Table 2: user_stats_sync
-- Optional cloud backup of user statistics (user-initiated sync)
CREATE TABLE IF NOT EXISTS user_stats_sync (
    user_id TEXT PRIMARY KEY,
    stats_json TEXT NOT NULL,
    last_sync INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_subscriptions(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_email ON user_subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(subscription_status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_verified ON user_subscriptions(verified);
CREATE INDEX IF NOT EXISTS idx_user_stats_sync_last_sync ON user_stats_sync(last_sync);
