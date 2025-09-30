"""
Migration: Add language field to users table

This migration adds a language field to store user's preferred language for i18n support.
"""

# SQL migration for adding language field
ADD_LANGUAGE_FIELD = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
"""

# Rollback SQL
REMOVE_LANGUAGE_FIELD = """
ALTER TABLE users DROP COLUMN IF EXISTS language;
"""

def upgrade(connection):
    """Apply the migration."""
    connection.execute(ADD_LANGUAGE_FIELD)

def downgrade(connection):
    """Rollback the migration."""
    connection.execute(REMOVE_LANGUAGE_FIELD)
