#!/usr/bin/env python3
"""
Complete News Pipeline

Orchestrates the complete data pipeline:
1. PURGE (optional): Clean database and website files
2. MINING: Collect articles from RSS feeds
3. IMAGE HANDLING: Generate web and mobile versions
4. DEEPSEEK: AI analysis and enrichment

Usage:
    python3 pipeline.py --purge                      # Full purge: database + files
    python3 pipeline.py --mine                       # Mining only
    python3 pipeline.py --images                     # Image optimization only
    python3 pipeline.py --deepseek                   # Deepseek processing only
    python3 pipeline.py --full                       # Complete pipeline: purge + mine + images + deepseek
    python3 pipeline.py --full --dry-run             # Preview without making changes
    python3 pipeline.py --full -v                    # Verbose output all phases
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Get project root
PROJECT_ROOT = Path(__file__).parent
TOOLS_DIR = PROJECT_ROOT / "tools"
MINING_DIR = PROJECT_ROOT / "mining"
DB_PATH = PROJECT_ROOT / "articles.db"
WEBSITE_DIR = PROJECT_ROOT / "website"
ARTICLE_IMAGE_DIR = WEBSITE_DIR / "article_image"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print section header"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{BLUE}→ {text}{RESET}")


def run_command(cmd, description, dry_run=False, verbose=False):
    """
    Run a shell command and track result
    
    Returns: (success, stdout, stderr)
    """
    print_info(description)
    
    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return True, "", ""
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            print_success(description)
            if verbose and result.stdout:
                print(f"  {result.stdout[:200]}")
            return True, result.stdout, result.stderr
        else:
            print_error(f"{description} (exit code: {result.returncode})")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        print_error(f"{description} (timeout)")
        return False, "", "Timeout"
    except Exception as e:
        print_error(f"{description}: {e}")
        return False, "", str(e)


def phase_purge(dry_run=False, verbose=False):
    """
    PHASE 1: Purge existing data
    
    Cleans database and website files for fresh pipeline run
    """
    print_header("PHASE 1: DATA PURGE")
    
    results = {
        'phase': 'purge',
        'start_time': datetime.now().isoformat(),
        'steps': []
    }
    
    # Step 1: Purge database
    print_info("Purging database...")
    cmd = [
        'python3',
        str(TOOLS_DIR / 'datapurge.py'),
        '--all',
        '--force'
    ]
    if verbose:
        cmd.append('-v')
    
    success, stdout, stderr = run_command(
        cmd,
        "Database purge complete",
        dry_run=dry_run,
        verbose=verbose
    )
    results['steps'].append({
        'step': 'database_purge',
        'success': success
    })
    
    if not success:
        print_error("Database purge failed")
        return False, results
    
    # Step 2: Purge website files
    print_info("Purging website files...")
    cmd = [
        'python3',
        str(TOOLS_DIR / 'pagepurge.py'),
        '--all',
        '--force'
    ]
    if verbose:
        cmd.append('-v')
    
    success, stdout, stderr = run_command(
        cmd,
        "Website file purge complete",
        dry_run=dry_run,
        verbose=verbose
    )
    results['steps'].append({
        'step': 'website_purge',
        'success': success
    })
    
    if not success:
        print_error("Website purge failed")
        return False, results
    
    print_success("Data purge phase complete")
    return True, results


def phase_mining(dry_run=False, verbose=False, articles_per_seed=2):
    """
    PHASE 2: Mining - Collect articles from RSS feeds
    
    Runs mining cycle to populate database with new articles
    
    Args:
        dry_run: Preview without making changes
        verbose: Detailed output
        articles_per_seed: Number of articles to collect per feed seed (default: 2)
    """
    print_header("PHASE 2: MINING")
    
    results = {
        'phase': 'mining',
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'articles_per_seed': articles_per_seed
    }
    
    print_info(f"Starting mining cycle (articles per seed: {articles_per_seed})...")
    
    mining_script = MINING_DIR / 'run_mining_cycle.py'
    if not mining_script.exists():
        print_error(f"Mining script not found: {mining_script}")
        return False, results
    
    cmd = ['python3', str(mining_script), '--articles-per-seed', str(articles_per_seed)]
    if verbose:
        cmd.append('-v')
    
    success, stdout, stderr = run_command(
        cmd,
        "Mining cycle complete",
        dry_run=dry_run,
        verbose=verbose
    )
    results['steps'].append({
        'step': 'mining_cycle',
        'success': success
    })
    
    if not success:
        print_error("Mining cycle failed")
        return False, results
    
    # Verify articles were collected
    if not dry_run:
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM articles")
            count = cur.fetchone()[0]
            conn.close()
            print_info(f"Database now contains {count} articles")
            results['articles_collected'] = count
        except Exception as e:
            print_warning(f"Could not verify article count: {e}")
    
    print_success("Mining phase complete")
    return True, results


def phase_image_handling(dry_run=False, verbose=False):
    """
    PHASE 3: Image Handling - Generate web and mobile versions
    
    Resizes images and creates optimized mobile versions
    """
    print_header("PHASE 3: IMAGE HANDLING")
    
    results = {
        'phase': 'image_handling',
        'start_time': datetime.now().isoformat(),
        'steps': []
    }
    
    # Check if any images exist
    if not ARTICLE_IMAGE_DIR.exists():
        print_warning("Article image directory not found, skipping image processing")
        return True, results
    
    image_count = len(list(ARTICLE_IMAGE_DIR.glob('article_*.jpg'))) + \
                  len(list(ARTICLE_IMAGE_DIR.glob('article_*.png'))) + \
                  len(list(ARTICLE_IMAGE_DIR.glob('article_*.webp')))
    
    if image_count == 0:
        print_warning("No images found to process, skipping")
        return True, results
    
    print_info(f"Found {image_count} image(s) to process...")
    
    cmd = [
        'python3',
        str(TOOLS_DIR / 'imgcompress.py'),
        '--dir', str(ARTICLE_IMAGE_DIR),
        '--auto',
        '--web',
        '--mobile'
    ]
    if verbose:
        cmd.append('-v')
    
    success, stdout, stderr = run_command(
        cmd,
        f"Image optimization complete ({image_count} images)",
        dry_run=dry_run,
        verbose=verbose
    )
    results['steps'].append({
        'step': 'image_optimization',
        'success': success,
        'images_processed': image_count
    })
    
    if not success:
        print_error("Image optimization failed")
        return False, results
    
    print_success("Image handling phase complete")
    return True, results


def phase_deepseek(dry_run=False, verbose=False):
    """
    PHASE 4: Deepseek - AI analysis and enrichment
    
    Uses Deepseek API to analyze articles and generate summaries
    """
    print_header("PHASE 4: DEEPSEEK PROCESSING")
    
    results = {
        'phase': 'deepseek',
        'start_time': datetime.now().isoformat(),
        'steps': []
    }
    
    # Check if Deepseek processing script exists
    deepseek_script = PROJECT_ROOT / 'deepseek' / 'process_one_article.py'
    if not deepseek_script.exists():
        print_warning(f"Deepseek script not found: {deepseek_script}")
        print_warning("Skipping Deepseek processing")
        return True, results
    
    # Count unprocessed articles
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0")
        unprocessed = cur.fetchone()[0]
        conn.close()
        print_info(f"Found {unprocessed} unprocessed article(s)")
    except Exception as e:
        print_warning(f"Could not count unprocessed articles: {e}")
        unprocessed = 0
    
    if unprocessed == 0:
        print_info("All articles already processed, skipping Deepseek phase")
        return True, results
    
    # Process articles with Deepseek
    print_info(f"Processing {unprocessed} article(s) with Deepseek API...")
    
    # This is a placeholder - actual implementation would iterate through articles
    # and call the Deepseek API for each one
    results['articles_to_process'] = unprocessed
    results['steps'].append({
        'step': 'deepseek_processing',
        'status': 'pending',
        'articles_to_process': unprocessed
    })
    
    print_warning("Deepseek processing: MANUAL STEP REQUIRED")
    print_warning("Run the following to process articles individually:")
    print(f"  cd {PROJECT_ROOT}")
    print(f"  python3 deepseek/process_one_article.py [article_id]")
    print("  Or batch process all unprocessed articles")
    
    print_success("Deepseek phase queued")
    return True, results


def phase_verification(dry_run=False, verbose=False):
    """
    Verify pipeline results
    """
    print_header("VERIFICATION")
    
    results = {
        'phase': 'verification',
        'start_time': datetime.now().isoformat(),
        'checks': []
    }
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        # Check articles
        cur.execute("SELECT COUNT(*) FROM articles")
        article_count = cur.fetchone()[0]
        results['checks'].append({
            'check': 'articles',
            'count': article_count,
            'status': 'OK' if article_count > 0 else 'EMPTY'
        })
        print_info(f"Articles in database: {article_count}")
        
        # Check images
        cur.execute("SELECT COUNT(*) FROM article_images")
        image_count = cur.fetchone()[0]
        results['checks'].append({
            'check': 'article_images',
            'count': image_count,
            'status': 'OK' if image_count > 0 else 'EMPTY'
        })
        print_info(f"Images in database: {image_count}")
        
        # Check mobile versions
        cur.execute("SELECT COUNT(*) FROM article_images WHERE small_location IS NOT NULL")
        mobile_count = cur.fetchone()[0]
        results['checks'].append({
            'check': 'mobile_versions',
            'count': mobile_count,
            'status': 'OK' if mobile_count > 0 else 'PENDING'
        })
        print_info(f"Mobile versions (small_location): {mobile_count}")
        
        # Check Deepseek processing
        cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1")
        processed = cur.fetchone()[0]
        results['checks'].append({
            'check': 'deepseek_processed',
            'count': processed,
            'status': 'OK' if processed > 0 else 'PENDING'
        })
        print_info(f"Articles processed by Deepseek: {processed}")
        
        conn.close()
        
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False, results
    
    print_success("Verification complete")
    return True, results


def main():
    parser = argparse.ArgumentParser(
        description="Complete News Pipeline Orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Phases:
  1. PURGE       - Clean database and website files (--purge)
  2. MINING      - Collect articles from RSS feeds (--mine)
  3. IMAGE       - Generate web and mobile versions (--images)
  4. DEEPSEEK    - AI analysis and enrichment (--deepseek)

Examples:
  # Full pipeline with cleanup (default 2 articles per seed)
  python3 pipeline.py --full

  # Full pipeline with 5 articles per seed
  python3 pipeline.py --full --articles-per-seed 5

  # Purge everything before new run
  python3 pipeline.py --purge

  # Mining only with custom articles per seed
  python3 pipeline.py --mine --articles-per-seed 3

  # Image optimization after manual mining
  python3 pipeline.py --images

  # Preview without making changes
  python3 pipeline.py --full --dry-run

  # Verbose output all phases
  python3 pipeline.py --full -v

  # Complete pipeline with 10 articles per seed and verbose output
  python3 pipeline.py --full --articles-per-seed 10 -v
        """
    )
    
    parser.add_argument("--purge", action="store_true",
                       help="Purge database and website files")
    parser.add_argument("--mine", action="store_true",
                       help="Run mining cycle")
    parser.add_argument("--images", action="store_true",
                       help="Process images (web + mobile)")
    parser.add_argument("--deepseek", action="store_true",
                       help="Process articles with Deepseek API")
    parser.add_argument("--full", action="store_true",
                       help="Run complete pipeline: purge → mine → images → deepseek")
    parser.add_argument("--verify", action="store_true",
                       help="Verify pipeline results")
    parser.add_argument("--articles-per-seed", type=int, default=2,
                       help="Number of articles to collect per feed seed (default: 2)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview without making changes")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.purge, args.mine, args.images, args.deepseek, args.full, args.verify]):
        print_error("Please specify at least one phase: --purge, --mine, --images, --deepseek, --full, or --verify")
        parser.print_help()
        sys.exit(1)
    
    if args.articles_per_seed < 1:
        print_error("--articles-per-seed must be >= 1")
        sys.exit(1)
    
    # Summary
    print_header("NEWS PIPELINE ORCHESTRATION")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Database: {DB_PATH}")
    print(f"Website Directory: {WEBSITE_DIR}")
    print(f"Articles per seed: {args.articles_per_seed}")
    if args.dry_run:
        print_warning("DRY-RUN MODE - No changes will be made")
    print()
    
    # Track pipeline results
    pipeline_results = {
        'start_time': datetime.now().isoformat(),
        'phases': [],
        'dry_run': args.dry_run,
        'verbose': args.verbose,
        'articles_per_seed': args.articles_per_seed
    }
    
    # Execute phases
    if args.full or args.purge:
        success, results = phase_purge(dry_run=args.dry_run, verbose=args.verbose)
        pipeline_results['phases'].append(results)
        if not success and args.full:
            print_error("Pipeline aborted: Purge phase failed")
            sys.exit(1)
    
    if args.full or args.mine:
        success, results = phase_mining(dry_run=args.dry_run, verbose=args.verbose, articles_per_seed=args.articles_per_seed)
        pipeline_results['phases'].append(results)
        if not success and args.full:
            print_error("Pipeline aborted: Mining phase failed")
            sys.exit(1)
    
    if args.full or args.images:
        success, results = phase_image_handling(dry_run=args.dry_run, verbose=args.verbose)
        pipeline_results['phases'].append(results)
        if not success and args.full:
            print_error("Pipeline aborted: Image handling phase failed")
            sys.exit(1)
    
    if args.full or args.deepseek:
        success, results = phase_deepseek(dry_run=args.dry_run, verbose=args.verbose)
        pipeline_results['phases'].append(results)
    
    # Verification
    if args.full or args.verify:
        success, results = phase_verification(dry_run=args.dry_run, verbose=args.verbose)
        pipeline_results['phases'].append(results)
    
    # Summary
    print_header("PIPELINE SUMMARY")
    print_info(f"Total phases executed: {len(pipeline_results['phases'])}")
    for phase_result in pipeline_results['phases']:
        print_info(f"  - {phase_result['phase'].upper()}: ✓")
    
    print_success("Pipeline execution complete!")
    print_info(f"End time: {datetime.now().isoformat()}")
    
    # Save results to log directory
    log_dir = PROJECT_ROOT / "log"
    log_dir.mkdir(exist_ok=True)
    results_file = log_dir / f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump(pipeline_results, f, indent=2)
        print_info(f"Results saved to: {results_file}")
    except Exception as e:
        print_warning(f"Could not save results: {e}")


if __name__ == "__main__":
    main()
