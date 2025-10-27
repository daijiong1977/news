#!/usr/bin/env python3
"""
User System Migration Script
Created: 2025-10-26
Purpose: Migrate database to add user_subscriptions and user_stats_sync tables
"""

import sqlite3
import sys
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'articles.db'
MIGRATION_SQL = PROJECT_ROOT / 'dbinit' / 'migration_user_system.sql'


def run_migration(db_path: Path, migration_sql_path: Path, dry_run: bool = False) -> bool:
    """
    Run database migration
    
    Args:
        db_path: Path to articles.db
        migration_sql_path: Path to migration SQL file
        dry_run: If True, only show what would be done
        
    Returns:
        True if successful, False otherwise
    """
    if not db_path.exists():
        print(f"❌ Error: Database not found at {db_path}")
        return False
    
    if not migration_sql_path.exists():
        print(f"❌ Error: Migration SQL not found at {migration_sql_path}")
        return False
    
    # Read migration SQL
    with open(migration_sql_path, 'r') as f:
        migration_sql = f.read()
    
    if dry_run:
        print("🔍 DRY RUN - Would execute the following SQL:")
        print("=" * 70)
        print(migration_sql)
        print("=" * 70)
        return True
    
    # Execute migration
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute migration SQL
        cursor.executescript(migration_sql)
        conn.commit()
        
        print("✅ Migration executed successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('user_subscriptions', 'user_stats_sync')
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print("\n📊 Verification:")
        if len(tables) == 2:
            print("✅ user_subscriptions table created")
            print("✅ user_stats_sync table created")
            
            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_user_%'
                ORDER BY name
            """)
            indexes = cursor.fetchall()
            print(f"✅ {len(indexes)} indexes created:")
            for idx in indexes:
                print(f"   - {idx[0]}")
            
            # Show table schemas
            print("\n📋 Table Schemas:")
            for table in ['user_subscriptions', 'user_stats_sync']:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"\n{table}:")
                for col in columns:
                    print(f"   {col[1]} ({col[2]})")
            
            return True
        else:
            print(f"❌ Error: Expected 2 tables, found {len(tables)}")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    """Main entry point"""
    print("=" * 70)
    print("User System Migration")
    print("=" * 70)
    
    # Check command line arguments
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if dry_run:
        print("\n🔍 Running in DRY RUN mode (no changes will be made)\n")
    
    # Run migration
    success = run_migration(DB_PATH, MIGRATION_SQL, dry_run=dry_run)
    
    if success:
        if not dry_run:
            print("\n✅ Migration completed successfully!")
            print(f"\n📝 Database: {DB_PATH}")
            print("\n🔄 Next steps:")
            print("   1. Verify tables with: sqlite3 articles.db '.tables'")
            print("   2. Update backend API endpoints")
            print("   3. Test registration flow")
        sys.exit(0)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
