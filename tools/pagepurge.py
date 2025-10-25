#!/usr/bin/env python3
"""
Page Purge Tool - Remove webpage files for article_id or date

Deletes files from website/ directory based on article_id or date.
Parses article_id directly from filenames (article_<ID>_*).

Files removed from:
- website/article_page/ — Article HTML pages
- website/article_image/ — Article preview images
- website/article_response/ — Article response JSON files

Supports purging by:
- Article ID (e.g., 2025102401)
- Specific date (e.g., 2025-10-24)
- Week range (e.g., 2025-week-43)
- Before/after date (e.g., before 2025-10-20)

Usage:
    python3 pagepurge.py --article-id 2025102401
    python3 pagepurge.py --date 2025-10-24
    python3 pagepurge.py --week 2025-week-43
    python3 pagepurge.py --before 2025-10-20
    python3 pagepurge.py --after 2025-10-15
    python3 pagepurge.py --date-range 2025-10-15 2025-10-20
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import re

# Get database path relative to this script
SCRIPT_DIR = Path(__file__).parent.parent
WEBSITE_DIR = SCRIPT_DIR / "website"
ARTICLE_PAGE_DIR = WEBSITE_DIR / "article_page"
ARTICLE_IMAGE_DIR = WEBSITE_DIR / "article_image"
ARTICLE_RESPONSE_DIR = WEBSITE_DIR / "article_response"


def parse_article_id_from_filename(filename):
    """Extract article_id from filename like 'article_<ID>_...' or 'article_<ID>.*'"""
    # Pattern: article_<something>_<something> or article_<something>.<ext>
    match = re.match(r'article_(\d+)(?:_|\.)', filename)
    if match:
        return match.group(1)
    return None


def get_files_by_article_id(article_id):
    """Find all files matching an article_id across all website directories"""
    article_id_str = str(article_id)
    files_to_delete = []
    
    # Search in all article directories
    for directory in [ARTICLE_PAGE_DIR, ARTICLE_IMAGE_DIR, ARTICLE_RESPONSE_DIR]:
        if not directory.exists():
            continue
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                parsed_id = parse_article_id_from_filename(file_path.name)
                if parsed_id == article_id_str:
                    files_to_delete.append(file_path)
    
    return files_to_delete


def get_article_ids_from_files():
    """Get all article_ids found in website files"""
    article_ids = set()
    
    for directory in [ARTICLE_PAGE_DIR, ARTICLE_IMAGE_DIR, ARTICLE_RESPONSE_DIR]:
        if not directory.exists():
            continue
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                parsed_id = parse_article_id_from_filename(file_path.name)
                if parsed_id:
                    article_ids.add(parsed_id)
    
    return sorted(article_ids, key=lambda x: int(x))


def get_article_ids_by_date(date_obj):
    """Get article_ids from date (format: YYYYMMDD + 2-digit counter)"""
    date_str = date_obj.strftime("%Y%m%d")
    all_ids = get_article_ids_from_files()
    
    matching_ids = [aid for aid in all_ids if aid.startswith(date_str)]
    return matching_ids


def get_article_ids_by_week(year, week):
    """Get article_ids from ISO week range"""
    # ISO week format: week 1 starts on Monday
    # Calculate date range for the week
    jan_4 = datetime(year, 1, 4)
    week_one_monday = jan_4 - timedelta(days=jan_4.weekday())
    start_date = week_one_monday + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    
    all_ids = get_article_ids_from_files()
    matching_ids = []
    
    for aid in all_ids:
        # Parse date from article_id (first 8 digits: YYYYMMDD)
        try:
            article_date = datetime.strptime(aid[:8], "%Y%m%d")
            if start_date <= article_date <= end_date:
                matching_ids.append(aid)
        except ValueError:
            continue
    
    return matching_ids


def get_article_ids_by_date_range(start_date, end_date):
    """Get article_ids within date range"""
    all_ids = get_article_ids_from_files()
    matching_ids = []
    
    for aid in all_ids:
        try:
            article_date = datetime.strptime(aid[:8], "%Y%m%d")
            if start_date <= article_date <= end_date:
                matching_ids.append(aid)
        except ValueError:
            continue
    
    return matching_ids


def get_article_ids_before_date(cutoff_date):
    """Get article_ids before cutoff date"""
    all_ids = get_article_ids_from_files()
    matching_ids = []
    
    for aid in all_ids:
        try:
            article_date = datetime.strptime(aid[:8], "%Y%m%d")
            if article_date < cutoff_date:
                matching_ids.append(aid)
        except ValueError:
            continue
    
    return matching_ids


def get_article_ids_after_date(cutoff_date):
    """Get article_ids after cutoff date"""
    all_ids = get_article_ids_from_files()
    matching_ids = []
    
    for aid in all_ids:
        try:
            article_date = datetime.strptime(aid[:8], "%Y%m%d")
            if article_date > cutoff_date:
                matching_ids.append(aid)
        except ValueError:
            continue
    
    return matching_ids


def show_files_preview(article_ids):
    """Show preview of files that match article_ids"""
    if not article_ids:
        print("No files found matching filter")
        return 0
    
    all_files = []
    total_size = 0
    
    for aid in article_ids:
        files = get_files_by_article_id(aid)
        for file_path in files:
            size = file_path.stat().st_size
            total_size += size
            relative_path = file_path.relative_to(WEBSITE_DIR)
            all_files.append((aid, relative_path, size))
    
    print("=" * 78)
    print("Files matching filter:")
    print("=" * 78)
    
    for aid, rel_path, size in sorted(all_files):
        size_kb = size / 1024
        print(f". ID: {aid}")
        print(f"  {rel_path} ({size_kb:.1f} KB)")
    
    print("=" * 78)
    print(f"Total: {len(all_files)} file(s), {total_size / 1024:.1f} KB")
    print("=" * 78)
    
    return len(all_files)


def purge_files(article_ids, dry_run=True, verbose=False):
    """Delete files matching article_ids"""
    if not article_ids:
        print("No files found matching filter")
        return 0
    
    deleted_count = 0
    total_size = 0
    
    for aid in article_ids:
        files = get_files_by_article_id(aid)
        
        for file_path in files:
            size = file_path.stat().st_size
            total_size += size
            
            if dry_run:
                if verbose:
                    print(f"[DRY-RUN] Would delete: {file_path.relative_to(WEBSITE_DIR)}")
            else:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    if verbose:
                        print(f"[DELETED] {file_path.relative_to(WEBSITE_DIR)}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete {file_path}: {e}", file=sys.stderr)
    
    return deleted_count, total_size


def main():
    parser = argparse.ArgumentParser(
        description="Remove webpage files from website/ directory by article_id or date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run: See what would be deleted
  python3 pagepurge.py --article-id 2025102401
  python3 pagepurge.py --date 2025-10-24
  
  # Actually delete files (requires confirmation)
  python3 pagepurge.py --article-id 2025102401 --force
  python3 pagepurge.py --date 2025-10-24 --force
  python3 pagepurge.py --week 2025-week-43 --force
        """
    )
    
    filter_group = parser.add_mutually_exclusive_group(required=True)
    filter_group.add_argument("--article-id", type=str, help="Delete files for specific article")
    filter_group.add_argument("--date", type=str, help="Delete files from date (YYYY-MM-DD)")
    filter_group.add_argument("--week", type=str, help="Delete files from ISO week (YYYY-week-WW)")
    filter_group.add_argument("--date-range", nargs=2, metavar=("START", "END"), 
                             help="Delete files in date range (YYYY-MM-DD YYYY-MM-DD)")
    filter_group.add_argument("--before", type=str, help="Delete files before date (YYYY-MM-DD)")
    filter_group.add_argument("--after", type=str, help="Delete files after date (YYYY-MM-DD)")
    
    parser.add_argument("--force", action="store_true", help="Actually delete files (default: dry-run)")
    parser.add_argument("--preview", action="store_true", help="Show preview of files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Determine which article_ids to target
    article_ids = []
    
    try:
        if args.article_id:
            article_ids = [args.article_id]
        
        elif args.date:
            date_obj = datetime.strptime(args.date, "%Y-%m-%d")
            article_ids = get_article_ids_by_date(date_obj)
        
        elif args.week:
            # Parse YYYY-week-WW format
            parts = args.week.split("-")
            if len(parts) != 3 or parts[1] != "week":
                print(f"Invalid week format: {args.week}. Use YYYY-week-WW", file=sys.stderr)
                sys.exit(1)
            
            year = int(parts[0])
            week = int(parts[2])
            article_ids = get_article_ids_by_week(year, week)
        
        elif args.date_range:
            start_date = datetime.strptime(args.date_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(args.date_range[1], "%Y-%m-%d")
            article_ids = get_article_ids_by_date_range(start_date, end_date)
        
        elif args.before:
            cutoff_date = datetime.strptime(args.before, "%Y-%m-%d")
            article_ids = get_article_ids_before_date(cutoff_date)
        
        elif args.after:
            cutoff_date = datetime.strptime(args.after, "%Y-%m-%d")
            article_ids = get_article_ids_after_date(cutoff_date)
    
    except ValueError as e:
        print(f"Invalid date format: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not article_ids:
        print("Found 0 file(s) matching filter")
        return
    
    print(f"Found {len(article_ids)} article(s) matching filter")
    print()
    
    # Show preview
    show_files_preview(article_ids)
    print()
    
    if args.preview:
        print("Preview mode - not deleting")
        return
    
    # Check if --force flag is set
    if not args.force:
        print("DRY RUN: Files that would be DELETED:")
        print("=" * 78)
        deleted_count, total_size = purge_files(article_ids, dry_run=True, verbose=args.verbose)
        print("=" * 78)
        print(f"Total: {deleted_count} file(s) to delete ({total_size / 1024:.1f} KB)")
        print()
        print("To actually delete, run with --force flag")
        return
    
    # Force mode - delete with confirmation
    print("WARNING: This will DELETE files permanently!")
    print("=" * 78)
    deleted_count, total_size = purge_files(article_ids, dry_run=True, verbose=False)
    print("=" * 78)
    print(f"Files to delete: {deleted_count} file(s) ({total_size / 1024:.1f} KB)")
    print()
    
    response = input('Type "yes" to confirm deletion: ')
    if response.lower() != "yes":
        print("Deletion cancelled")
        return
    
    print()
    print("Deleting files...")
    deleted_count, total_size = purge_files(article_ids, dry_run=False, verbose=args.verbose)
    print("=" * 78)
    print(f"✓ Deleted {deleted_count} file(s) ({total_size / 1024:.1f} KB)")
    print("=" * 78)


if __name__ == "__main__":
    main()
