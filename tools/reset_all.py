#!/usr/bin/env python3
"""
Complete Purge Tool - Reset article data while preserving configuration

This tool provides ONE-COMMAND purging of article-related data:
- Database: All articles and related processing data (preserves config tables)
- Website files: All article pages, images, responses
- Deepseek responses: All processing results
- Mining responses: All collected data

PRESERVED (never deleted):
- apikey, feeds, categories, difficulty_levels
- users, user_difficulty_levels, user_categories, user_preferences, user_awards
- All configuration and setup data

Use cases:
1. Fresh start: python3 reset_all.py --force
2. Preview: python3 reset_all.py (shows what will be deleted)
3. Selective purge: See options below

Options:
  --db-only       Delete article data only (preserve website files)
  --files-only    Delete website files only (preserve database)
  --deepseek-only Delete deepseek responses only
  --mining-only   Delete mining responses only
  --force         Actually delete (default is dry-run preview)
  -v, --verbose   Show detailed information
  --keep-db       Keep database, delete everything else

Default (no options): Full purge with dry-run preview
"""

import sqlite3
import argparse
import sys
from pathlib import Path
import shutil
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
DB_PATH = SCRIPT_DIR / "articles.db"
WEBSITE_DIR = SCRIPT_DIR / "website"
DEEPSEEK_DIR = SCRIPT_DIR / "deepseek" / "responses"
MINING_DIR = SCRIPT_DIR / "mining" / "responses"


class PurgeManager:
    def __init__(self, dry_run=True, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'database': {'articles': 0, 'records': {}},
            'files': {},
            'deepseek': 0,
            'mining': 0
        }
    
    def purge_all(self):
        """Complete purge: database, files, responses"""
        print("\n" + "="*70)
        print("🧹 COMPLETE PURGE - Everything")
        print("="*70)
        
        self.purge_database()
        self.purge_website_files()
        self.purge_deepseek_responses()
        self.purge_mining_responses()
        
        self._show_summary()
    
    def purge_database_only(self):
        """Database purge only"""
        print("\n" + "="*70)
        print("🗄️  DATABASE PURGE")
        print("="*70)
        
        self.purge_database()
        self._show_summary()
    
    def purge_files_only(self):
        """Website files purge only"""
        print("\n" + "="*70)
        print("📁 FILE PURGE")
        print("="*70)
        
        self.purge_website_files()
        self._show_summary()
    
    def purge_deepseek_only(self):
        """Deepseek responses purge only"""
        print("\n" + "="*70)
        print("🤖 DEEPSEEK RESPONSES PURGE")
        print("="*70)
        
        self.purge_deepseek_responses()
        self._show_summary()
    
    def purge_mining_only(self):
        """Mining responses purge only"""
        print("\n" + "="*70)
        print("⛏️  MINING RESPONSES PURGE")
        print("="*70)
        
        self.purge_mining_responses()
        self._show_summary()
    
    def purge_keep_db(self):
        """Delete everything except database"""
        print("\n" + "="*70)
        print("🔒 KEEP DATABASE - Purge Everything Else")
        print("="*70)
        
        self.purge_website_files()
        self.purge_deepseek_responses()
        self.purge_mining_responses()
        
        self._show_summary()
    
    def purge_database(self):
        """Purge all database records"""
        if not DB_PATH.exists():
            print(f"⚠️  Database not found: {DB_PATH}")
            return
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Tables to purge (ONLY article-related data)
            # PRESERVED: apikey, feeds, categories, difficulty_levels, users, user_* tables
            tables_ordered = [
                'choices',           # Depends on questions
                'questions',         # Depends on articles
                'article_images',    # Depends on articles
                'article_summaries', # Depends on articles
                'article_analysis',  # Depends on articles
                'keywords',          # Depends on articles
                'comments',          # Depends on articles
                'background_read',   # Depends on articles
                'response',          # Depends on articles
                'articles',          # Main table (last, after all dependent data)
            ]
            
            # Configuration tables that are NEVER deleted
            preserved_tables = [
                'apikey',                    # API keys
                'feeds',                     # RSS feed sources
                'categories',                # Article categories
                'difficulty_levels',         # Difficulty ratings
                'users',                     # User accounts
                'user_difficulty_levels',    # User preferences
                'user_categories',           # User preferences
                'user_preferences',          # User settings
                'user_awards',               # User stats
            ]
            
            # Count records before deletion
            for table in tables_ordered:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stats['database']['records'][table] = count
                    if self.verbose and count > 0:
                        print(f"  Found {count} {table} records")
                except:
                    pass
            
            if not self.dry_run:
                print("\n🗑️  Deleting article data (preserving configuration tables)...")
                # Disable foreign key checks temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                for table in tables_ordered:
                    cursor.execute(f"DELETE FROM {table}")
                    deleted = cursor.rowcount
                    if deleted > 0:
                        print(f"  ✓ {table}: {deleted} records")
                
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                self.stats['database']['articles'] = sum(self.stats['database']['records'].values())
                print(f"\n✅ Database purged: {self.stats['database']['articles']} records deleted")
                
                # Show preserved tables
                print("\n📌 Preserved (not deleted):")
                for table in preserved_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  • {table}: {count} records")
            else:
                total = sum(self.stats['database']['records'].values())
                self.stats['database']['articles'] = total
                print(f"\n📊 DRY RUN - Would delete {total} article records:")
                for table, count in self.stats['database']['records'].items():
                    if count > 0:
                        print(f"  • {table}: {count}")
                
                # Show what will be preserved
                print(f"\n📌 Preserved (not deleted):")
                for table in preserved_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  • {table}: {count} records")
            
            conn.close()
        
        except Exception as e:
            print(f"❌ ERROR purging database: {e}")
            sys.exit(1)
    
    def purge_website_files(self):
        """Purge website files"""
        print("\n📁 Website Files:")
        
        dirs_to_check = [
            ('article_page', WEBSITE_DIR / 'article_page'),
            ('article_image', WEBSITE_DIR / 'article_image'),
            ('article_response', WEBSITE_DIR / 'article_response'),
        ]
        
        total_files = 0
        
        for dir_name, dir_path in dirs_to_check:
            if not dir_path.exists():
                print(f"  ℹ️  {dir_name}/ not found")
                continue
            
            files = list(dir_path.glob('*'))
            file_count = len([f for f in files if f.is_file()])
            
            if file_count > 0:
                self.stats['files'][dir_name] = file_count
                total_files += file_count
                print(f"  Found {file_count} files in {dir_name}/")
                
                if not self.dry_run:
                    for file_path in files:
                        if file_path.is_file():
                            file_path.unlink()
                    print(f"  ✓ Deleted {file_count} files from {dir_name}/")
        
        if self.dry_run and total_files > 0:
            print(f"\n📊 DRY RUN - Would delete {total_files} website files")
        elif not self.dry_run and total_files > 0:
            print(f"\n✅ Website files purged: {total_files} files deleted")
    
    def purge_deepseek_responses(self):
        """Purge deepseek response files"""
        print("\n🤖 Deepseek Responses:")
        
        if not DEEPSEEK_DIR.exists():
            print(f"  ℹ️  {DEEPSEEK_DIR} not found")
            return
        
        files = list(DEEPSEEK_DIR.glob('*'))
        file_count = len([f for f in files if f.is_file()])
        
        if file_count > 0:
            self.stats['deepseek'] = file_count
            print(f"  Found {file_count} response files")
            
            if not self.dry_run:
                for file_path in files:
                    if file_path.is_file():
                        file_path.unlink()
                print(f"  ✓ Deleted {file_count} deepseek response files")
            else:
                print(f"  📊 DRY RUN - Would delete {file_count} files")
    
    def purge_mining_responses(self):
        """Purge mining response files"""
        print("\n⛏️  Mining Responses:")
        
        if not MINING_DIR.exists():
            print(f"  ℹ️  {MINING_DIR} not found")
            return
        
        files = list(MINING_DIR.glob('*'))
        file_count = len([f for f in files if f.is_file()])
        
        if file_count > 0:
            self.stats['mining'] = file_count
            print(f"  Found {file_count} response files")
            
            if not self.dry_run:
                for file_path in files:
                    if file_path.is_file():
                        file_path.unlink()
                print(f"  ✓ Deleted {file_count} mining response files")
            else:
                print(f"  📊 DRY RUN - Would delete {file_count} files")
    
    def _show_summary(self):
        """Show purge summary"""
        print("\n" + "="*70)
        if self.dry_run:
            print("DRY RUN - No data was actually deleted")
            print("Use --force flag to execute the purge")
        else:
            print("✅ PURGE COMPLETE")
        print("="*70)
        
        print("\n📊 Summary:")
        
        if self.stats['database']['articles'] > 0:
            print(f"  • Database: {self.stats['database']['articles']} records")
        
        if self.stats['files']:
            total = sum(self.stats['files'].values())
            print(f"  • Website files: {total} files")
        
        if self.stats['deepseek'] > 0:
            print(f"  • Deepseek responses: {self.stats['deepseek']} files")
        
        if self.stats['mining'] > 0:
            print(f"  • Mining responses: {self.stats['mining']} files")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Complete purge tool - Reset everything to clean state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Preview what will be deleted (default: dry-run)
  python3 reset_all.py
  
  # Actually delete everything (CAUTION!)
  python3 reset_all.py --force
  
  # Database only
  python3 reset_all.py --db-only --force
  
  # Website files only
  python3 reset_all.py --files-only --force
  
  # Everything except database
  python3 reset_all.py --keep-db --force
  
  # Deepseek responses only
  python3 reset_all.py --deepseek-only --force
  
  # Mining responses only
  python3 reset_all.py --mining-only --force
  
  # Verbose output
  python3 reset_all.py --force -v
        """
    )
    
    # Purge options (mutually exclusive)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--db-only", action="store_true", 
                      help="Delete database records only")
    group.add_argument("--files-only", action="store_true", 
                      help="Delete website files only")
    group.add_argument("--deepseek-only", action="store_true", 
                      help="Delete deepseek responses only")
    group.add_argument("--mining-only", action="store_true", 
                      help="Delete mining responses only")
    group.add_argument("--keep-db", action="store_true", 
                      help="Delete everything except database")
    
    parser.add_argument("--force", action="store_true", 
                       help="Actually delete (default is dry-run)")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Confirm force flag if not present
    if not args.force:
        print("⚠️  DRY RUN MODE (no data will be deleted)")
        print("    Use --force flag to actually execute purge\n")
    
    manager = PurgeManager(dry_run=not args.force, verbose=args.verbose)
    
    try:
        if args.db_only:
            manager.purge_database_only()
        elif args.files_only:
            manager.purge_files_only()
        elif args.deepseek_only:
            manager.purge_deepseek_only()
        elif args.mining_only:
            manager.purge_mining_only()
        elif args.keep_db:
            manager.purge_keep_db()
        else:
            # Default: full purge
            manager.purge_all()
    
    except KeyboardInterrupt:
        print("\n\n❌ Purge cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
