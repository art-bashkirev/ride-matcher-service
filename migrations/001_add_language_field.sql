-- Migration: Add language field to users table
-- Description: Adds language preference column for i18n support

ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';

-- Update existing users to have the default language
UPDATE users SET language = 'en' WHERE language IS NULL;
