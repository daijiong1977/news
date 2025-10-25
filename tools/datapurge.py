#!/usr/bin/env python3
"""
Data Purge Tool - Remove articles and related data from DATABASE ONLY

⚠️  DATABASE ONLY: This tool deletes database records only. 
    It does NOT delete files in website/ directory (images, responses, etc.)

Supports purging by:
- Article ID (e.g., 2025102401)
- Specific date (e.g., 2025-10-24)
- Week range (e.g., 2025-week-43)
- Before/after date (e.g., before 2025-10-20)

Database records deleted:
- articles, article_images (references only)
- keywords, questions, choices
- comments, background_read
- article_analysis, article_summaries
- response (records only, files preserved)

Files PRESERVED (not deleted):
- website/article_image/ ✓
- website/article_response/ ✓
- deepseek/responses/ ✓
- mining/responses/ ✓

Usage:
    python3 datapurge.py --article-id 2025102401
    python3 datapurge.py --date 2025-10-24
    python3 datapurge.py --week 2025-week-43
    python3 datapurge.py --before 2025-10-20
    python3 datapurge.py --after 2025-10-15
    python3 datapurge.py --date-range 2025-10-15 2025-10-20
"""

import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

# Get database path (parent of tools directory)
SCRIPT_DIR = Path(__file__).parent.parent
DB_PATH = SCRIPT_DIR / "articles.db"


def get_connection():
    """Create database connection."""
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(str(DB_PATH))


def parse_date(date_str):
    """Parse date string in format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def get_article_ids_by_date(date_obj):
    """Get all article IDs for a specific date."""
    date_str = date_obj.strftime("%Y%m%d")
    return (f"{date_str}00", f"{date_str}99")  # From 00 to 99


def get_article_ids_by_week(year, week):
    """Get article ID range for a specific ISO week.
    
    Example: 2025-week-43 returns all articles from that week
    """
    # Get first day of the week
    jan4 = datetime(year, 1, 4)
    week_one_monday = jan4 - timedelta(days=jan4.weekday())
    first_day = week_one_monday + timedelta(weeks=week - 1)
    last_day = first_day + timedelta(days=6)
    
    # Convert to date range format (YYYYMMDD)
    start_date = first_day.strftime("%Y%m%d")
    end_date = last_day.strftime("%Y%m%d")
    
    return (start_date + "00", end_date + "99")


def get_related_data_stats(conn, article_ids):
    """Get statistics about related data for articles."""
    if not article_ids:
        return {}
    
    placeholders = ",".join("?" * len(article_ids))
    cursor = conn.cursor()
    
    stats = {}
    
    # Count related data
    cursor.execute(f"""
        SELECT 'article_images' as table_name, COUNT(*) as count 
        FROM article_images WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['article_images'] = result[1]
    
    cursor.execute(f"""
        SELECT 'keywords' as table_name, COUNT(*) as count 
        FROM keywords WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['keywords'] = result[1]
    
    cursor.execute(f"""
        SELECT 'questions' as table_name, COUNT(*) as count 
        FROM questions WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['questions'] = result[1]
    
    cursor.execute(f"""
        SELECT 'comments' as table_name, COUNT(*) as count 
        FROM comments WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['comments'] = result[1]
    
    cursor.execute(f"""
        SELECT 'background_read' as table_name, COUNT(*) as count 
        FROM background_read WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['background_read'] = result[1]
    
    cursor.execute(f"""
        SELECT 'article_analysis' as table_name, COUNT(*) as count 
        FROM article_analysis WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['article_analysis'] = result[1]
    
    cursor.execute(f"""
        SELECT 'response' as table_name, COUNT(*) as count 
        FROM response WHERE article_id IN ({placeholders})
    """, article_ids)
    if result := cursor.fetchone():
        stats['response'] = result[1]
    
    return stats


def get_article_ids_by_filter(conn, filter_type, filter_value):
    """Get list of article IDs matching filter criteria."""
    cursor = conn.cursor()
    
    if filter_type == "article_id":
        # Check if specific article exists
        cursor.execute("SELECT id FROM articles WHERE id = ?", (filter_value,))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    elif filter_type == "date":
        start_id, end_id = get_article_ids_by_date(filter_value)
        cursor.execute("""
            SELECT id FROM articles WHERE id BETWEEN ? AND ?
        """, (start_id, end_id))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    elif filter_type == "week":
        start_id, end_id = filter_value  # Already parsed
        cursor.execute("""
            SELECT id FROM articles WHERE id BETWEEN ? AND ?
        """, (start_id, end_id))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    elif filter_type == "before":
        end_id = filter_value.strftime("%Y%m%d") + "99"
        cursor.execute("""
            SELECT id FROM articles WHERE id <= ?
        """, (end_id,))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    elif filter_type == "after":
        start_id = filter_value.strftime("%Y%m%d") + "00"
        cursor.execute("""
            SELECT id FROM articles WHERE id >= ?
        """, (start_id,))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    elif filter_type == "date_range":
        start_date, end_date = filter_value
        start_id = start_date.strftime("%Y%m%d") + "00"
        end_id = end_date.strftime("%Y%m%d") + "99"
        cursor.execute("""
            SELECT id FROM articles WHERE id BETWEEN ? AND ?
        """, (start_id, end_id))
        article_ids = [row[0] for row in cursor.fetchall()]
        return article_ids
    
    return []


def purge_articles(conn, article_ids, dry_run=True):
    """Purge articles and all related data.
    
    Args:
        conn: Database connection
        article_ids: List of article IDs to purge
        dry_run: If True, only show what would be deleted
    
    Returns:
        Dictionary with deletion statistics
    """
    if not article_ids:
        print("ERROR: No articles found matching criteria")
        return None
    
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(article_ids))
    
    stats = {
        'articles': 0,
        'article_images': 0,
        'keywords': 0,
        'questions': 0,
        'choices': 0,
        'comments': 0,
        'background_read': 0,
        'article_analysis': 0,
        'article_summaries': 0,
        'response': 0
    }
    
    try:
        # Get related data counts first
        for table in stats.keys():
            if table == 'articles':
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id IN ({placeholders})", article_ids)
            elif table == 'choices':
                # Special case: choices linked through questions
                cursor.execute(f"""
                    SELECT COUNT(*) FROM choices 
                    WHERE question_id IN (
                        SELECT question_id FROM questions WHERE article_id IN ({placeholders})
                    )
                """, article_ids)
            else:
                # All other tables have article_id
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE article_id IN ({placeholders})", article_ids)
            
            count = cursor.fetchone()[0]
            stats[table] = count
        
        if dry_run:
            print("\n" + "="*70)
            print("DRY RUN: Data that would be DELETED:")
            print("="*70)
            for table, count in stats.items():
                if count > 0:
                    print(f"  {table:25} {count:5} rows")
            print("="*70)
            print(f"\nTotal articles to delete: {len(article_ids)}")
            print("To actually delete, run with --force flag\n")
        else:
            print("\n" + "="*70)
            print("DELETING Data...")
            print("="*70)
            
            # Delete in order (respecting foreign keys)
            # 1. Delete choices (linked through questions)
            cursor.execute(f"""
                DELETE FROM choices 
                WHERE question_id IN (
                    SELECT question_id FROM questions WHERE article_id IN ({placeholders})
                )
            """, article_ids)
            
            # 2. Delete everything else directly
            for table in ['questions', 'article_images', 'keywords', 'comments', 
                         'background_read', 'article_analysis', 'article_summaries', 'response']:
                cursor.execute(f"DELETE FROM {table} WHERE article_id IN ({placeholders})", article_ids)
            
            # 3. Delete articles last
            cursor.execute(f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids)
            
            conn.commit()
            
            print("\nDeletion complete!")
            for table, count in stats.items():
                if count > 0:
                    print(f"  {table:25} {count:5} rows deleted")
            print("="*70 + "\n")
        
        return stats
    
    except Exception as e:
        print(f"ERROR during deletion: {e}")
        conn.rollback()
        return None


def show_articles_preview(conn, article_ids):
    """Show preview of articles to be deleted."""
    if not article_ids:
        return
    
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(article_ids))
    
    cursor.execute(f"""
        SELECT id, title, source, pub_date, deepseek_processed 
        FROM articles 
        WHERE id IN ({placeholders})
        ORDER BY id DESC
    """, article_ids)
    
    print("\n" + "="*70)
    print("Articles matching filter:")
    print("="*70)
    
    rows = cursor.fetchall()
    for i, (article_id, title, source, pub_date, processed) in enumerate(rows, 1):
        status = "✓" if processed else "✗"
        print(f"\n{i}. ID: {article_id} [{status}]")
        print(f"   Title:  {title[:60]}...")
        print(f"   Source: {source}")
        print(f"   Date:   {pub_date}")
    
    print("\n" + "="*70)
    print(f"Total: {len(rows)} article(s)\n")


def main():
    parser = argparse.ArgumentParser(
        description="Purge articles and related data from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete specific article
  python3 datapurge.py --article-id 2025102401
  
  # Delete all articles from specific date
  python3 datapurge.py --date 2025-10-24
  
  # Delete all articles from ISO week 43
  python3 datapurge.py --week 2025-week-43
  
  # Delete all articles before date
  python3 datapurge.py --before 2025-10-20
  
  # Delete all articles after date
  python3 datapurge.py --after 2025-10-15
  
  # Delete date range
  python3 datapurge.py --date-range 2025-10-15 2025-10-20
  
  # Use --force to actually delete (default is dry-run)
  python3 datapurge.py --date 2025-10-24 --force
  
  # Preview articles without deleting
  python3 datapurge.py --date 2025-10-24 --preview
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--article-id", type=str, help="Purge specific article by ID")
    group.add_argument("--date", type=str, help="Purge all articles from date (YYYY-MM-DD)")
    group.add_argument("--week", type=str, help="Purge articles from ISO week (YYYY-week-WW)")
    group.add_argument("--before", type=str, help="Purge articles before date (YYYY-MM-DD)")
    group.add_argument("--after", type=str, help="Purge articles after date (YYYY-MM-DD)")
    group.add_argument("--date-range", nargs=2, metavar=("START", "END"), 
                      help="Purge articles in date range (YYYY-MM-DD YYYY-MM-DD)")
    
    parser.add_argument("--force", action="store_true", 
                       help="Actually delete data (default is dry-run preview)")
    parser.add_argument("--preview", action="store_true", 
                       help="Show preview of articles to be deleted")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Connect to database
    conn = get_connection()
    
    try:
        # Parse filter arguments
        filter_type = None
        filter_value = None
        
        if args.article_id:
            filter_type = "article_id"
            filter_value = args.article_id
        elif args.date:
            filter_type = "date"
            filter_value = parse_date(args.date)
        elif args.week:
            # Parse week string like "2025-week-43"
            try:
                parts = args.week.split("-")
                if len(parts) != 3 or parts[1] != "week":
                    raise ValueError()
                year = int(parts[0])
                week = int(parts[2])
                filter_type = "week"
                filter_value = get_article_ids_by_week(year, week)
                if args.verbose:
                    print(f"Week range: {filter_value[0]} to {filter_value[1]}")
            except (ValueError, IndexError):
                print("ERROR: Invalid week format. Use: YYYY-week-WW")
                sys.exit(1)
        elif args.before:
            filter_type = "before"
            filter_value = parse_date(args.before)
        elif args.after:
            filter_type = "after"
            filter_value = parse_date(args.after)
        elif args.date_range:
            filter_type = "date_range"
            start = parse_date(args.date_range[0])
            end = parse_date(args.date_range[1])
            if start > end:
                print("ERROR: Start date must be before end date")
                sys.exit(1)
            filter_value = (start, end)
        
        # Get matching article IDs
        article_ids = get_article_ids_by_filter(conn, filter_type, filter_value)
        
        if not article_ids:
            print("\nNo articles found matching filter criteria")
            sys.exit(0)
        
        print(f"\nFound {len(article_ids)} article(s) matching filter")
        
        # Show preview if requested
        if args.preview or (not args.force):
            show_articles_preview(conn, article_ids)
        
        # Purge data
        if args.force:
            confirm = input("Are you sure you want to DELETE this data? (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled.")
                sys.exit(0)
        
        stats = purge_articles(conn, article_ids, dry_run=not args.force)
        
        if stats and args.force:
            print("✓ Data purge completed successfully\n")
        
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
