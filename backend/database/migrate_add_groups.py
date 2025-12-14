"""Migration script to add groups support to quotes."""
import sqlite3
import os
from pathlib import Path

# Database path
DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///osc_finops.db")
if DATABASE_PATH.startswith("sqlite:///"):
    db_file = DATABASE_PATH.replace("sqlite:///", "")
else:
    db_file = "osc_finops.db"


def migrate():
    """Add groups table and group_id column to quote_items."""
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check if quote_groups table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='quote_groups'
        """)
        if cursor.fetchone():
            print("quote_groups table already exists. Skipping table creation.")
        else:
            # Create quote_groups table
            cursor.execute("""
                CREATE TABLE quote_groups (
                    group_id TEXT PRIMARY KEY,
                    quote_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id) ON DELETE CASCADE,
                    CHECK (LENGTH(name) > 0)
                )
            """)
            print("Created quote_groups table.")
        
        # Check if group_id column already exists in quote_items
        cursor.execute("PRAGMA table_info(quote_items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'group_id' in columns:
            print("group_id column already exists in quote_items. Skipping column addition.")
        else:
            # Add group_id column to quote_items
            cursor.execute("""
                ALTER TABLE quote_items 
                ADD COLUMN group_id TEXT
            """)
            
            # Create index on group_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_quote_items_group_id 
                ON quote_items(group_id)
            """)
            
            # Add foreign key constraint (SQLite doesn't support ALTER TABLE ADD CONSTRAINT,
            # so we'll create a new table and copy data)
            print("Added group_id column to quote_items.")
            print("Note: Foreign key constraint will be enforced by SQLAlchemy.")
        
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Running migration: Add groups support to quotes...")
    migrate()
    print("Migration finished.")

