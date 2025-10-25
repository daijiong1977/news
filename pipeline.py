#!/usr/bin/env python3
"""
Complete News Pipeline

Orchestrates the complete data pipeline (NO PURGE - run manually via cron):
1. MINING: Collect articles from RSS feeds
2. IMAGE HANDLING: Generate web and mobile versions
3. DEEPSEEK: AI analysis and enrichment
4. VERIFY: Validate results

Note: Purge/reset is separate (python3 tools/reset_all.py --force)

Usage:
    python3 pipeline.py --mine                       # Mining only
    python3 pipeline.py --images                     # Image optimization only
    python3 pipeline.py --deepseek                   # Deepseek processing only
    python3 pipeline.py --full                       # Complete pipeline: mine + images + deepseek + verify
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


def setup_logging(phase_name):
    """Setup logging for a pipeline phase
    
    Returns: (log_file_path, log_file_handle)
    """
    log_dir = PROJECT_ROOT / "log"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"phase_{phase_name}_{timestamp}.log"
    
    return log_file


def log_to_file(log_file, message):
    """Append message to log file"""
    try:
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception as e:
        print_warning(f"Could not write to log: {e}")


def run_command(cmd, description, dry_run=False, verbose=False, log_file=None, timeout=3600):
    """
    Run a shell command and track result
    
    Returns: (success, stdout, stderr)
    """
    print_info(description)
    if log_file:
        log_to_file(log_file, f"→ {description}")
        log_to_file(log_file, f"Command: {' '.join(cmd)}")
    
    if dry_run:
        msg = f"  [DRY-RUN] {' '.join(cmd)}"
        print(msg)
        if log_file:
            log_to_file(log_file, f"[DRY-RUN] {' '.join(cmd)}")
        return True, "", ""
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if log_file:
            log_to_file(log_file, f"Exit code: {result.returncode}")
            if result.stdout:
                log_to_file(log_file, f"STDOUT:\n{result.stdout}")
            if result.stderr:
                log_to_file(log_file, f"STDERR:\n{result.stderr}")
        
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
        msg = f"{description} (timeout)"
        print_error(msg)
        if log_file:
            log_to_file(log_file, f"✗ {msg}")
        return False, "", "Timeout"
    except Exception as e:
        msg = f"{description}: {e}"
        print_error(msg)
        if log_file:
            log_to_file(log_file, f"✗ {msg}")
        return False, "", str(e)


def phase_mining(dry_run=False, verbose=False, articles_per_seed=2):
    """
    PHASE 1: Mining - Collect articles from RSS feeds
    
    Runs mining cycle to populate database with new articles
    
    Args:
        dry_run: Preview without making changes
        verbose: Detailed output
        articles_per_seed: Number of articles to collect per feed seed (default: 2)
    """
    print_header("PHASE 1: MINING")
    
    log_file = setup_logging("mining")
    log_to_file(log_file, f"Starting mining phase (articles per seed: {articles_per_seed})")
    
    results = {
        'phase': 'mining',
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'articles_per_seed': articles_per_seed,
        'log_file': str(log_file)
    }
    
    print_info(f"Starting mining cycle (articles per seed: {articles_per_seed})...")
    print_info(f"Logging to: {log_file}")
    
    mining_script = MINING_DIR / 'run_mining_cycle.py'
    if not mining_script.exists():
        msg = f"Mining script not found: {mining_script}"
        print_error(msg)
        log_to_file(log_file, f"✗ {msg}")
        return False, results
    
    # Build command - mining script only collects articles
    cmd = ['python3', str(mining_script)]
    
    success, stdout, stderr = run_command(
        cmd,
        "Mining cycle complete",
        dry_run=dry_run,
        verbose=verbose,
        log_file=log_file
    )
    results['steps'].append({
        'step': 'mining_cycle',
        'success': success
    })
    
    if not success:
        log_to_file(log_file, "✗ Mining cycle failed")
        print_error("Mining cycle failed")
        return False, results
    
    # Verify articles were collected
    if not dry_run:
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            
            # Get total article count
            cur.execute("SELECT COUNT(*) FROM articles")
            total_count = cur.fetchone()[0]
            
            # Get articles by source
            cur.execute("SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC")
            source_counts = cur.fetchall()
            
            # Get articles with images
            cur.execute("SELECT COUNT(*) FROM articles WHERE image_id IS NOT NULL")
            images_count = cur.fetchone()[0]
            
            conn.close()
            
            msg = f"Database now contains {total_count} articles"
            print_info(msg)
            log_to_file(log_file, msg)
            
            # Log details by source
            log_to_file(log_file, "\nArticles by source:")
            for source, count in source_counts:
                msg = f"  {source}: {count} article(s)"
                print_info(msg)
                log_to_file(log_file, msg)
            
            # Log image status
            msg = f"Articles with images: {images_count}/{total_count}"
            print_info(msg)
            log_to_file(log_file, msg)
            
            results['articles_collected'] = total_count
            results['articles_by_source'] = {source: count for source, count in source_counts}
            results['articles_with_images'] = images_count
        except Exception as e:
            msg = f"Could not verify article count: {e}"
            print_warning(msg)
            log_to_file(log_file, f"⚠ {msg}")
    
    print_success("Mining phase complete")
    return True, results


def phase_image_handling(dry_run=False, verbose=False):
    """
    PHASE 2: Image Handling - Generate web and mobile versions
    
    Resizes images and creates optimized mobile versions
    """
    print_header("PHASE 2: IMAGE HANDLING")
    
    log_file = setup_logging("image_handling")
    log_to_file(log_file, "Starting image handling phase")
    
    results = {
        'phase': 'image_handling',
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'log_file': str(log_file)
    }
    
    print_info(f"Logging to: {log_file}")
    
    # Check if any images exist
    if not ARTICLE_IMAGE_DIR.exists():
        msg = "Article image directory not found, skipping image processing"
        print_warning(msg)
        log_to_file(log_file, f"⚠ {msg}")
        return True, results
    
    image_count = len(list(ARTICLE_IMAGE_DIR.glob('article_*.jpg'))) + \
                  len(list(ARTICLE_IMAGE_DIR.glob('article_*.png'))) + \
                  len(list(ARTICLE_IMAGE_DIR.glob('article_*.webp')))
    
    if image_count == 0:
        msg = "No images found to process, skipping"
        print_warning(msg)
        log_to_file(log_file, f"⚠ {msg}")
        return True, results
    
    print_info(f"Found {image_count} image(s) to process...")
    log_to_file(log_file, f"Found {image_count} image(s) to process")
    
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
        verbose=verbose,
        log_file=log_file
    )
    results['steps'].append({
        'step': 'image_optimization',
        'success': success,
        'images_processed': image_count
    })
    
    if not success:
        log_to_file(log_file, "✗ Image optimization failed")
        print_error("Image optimization failed")
        return False, results
    
    log_to_file(log_file, "✓ Image handling phase complete")
    print_success("Image handling phase complete")
    return True, results


def phase_deepseek(dry_run=False, verbose=False):
    """
    PHASE 3: Deepseek - AI analysis and enrichment
    
    Uses Deepseek API to analyze articles and generate summaries
    Runs batch processing to handle all unprocessed articles
    """
    print_header("PHASE 3: DEEPSEEK PROCESSING")
    
    log_file = setup_logging("deepseek")
    log_to_file(log_file, "Starting Deepseek processing phase")
    
    results = {
        'phase': 'deepseek',
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'log_file': str(log_file)
    }
    
    print_info(f"Logging to: {log_file}")
    
    # Check if Deepseek processing script exists
    deepseek_script = PROJECT_ROOT / 'deepseek' / 'process_one_article.py'
    if not deepseek_script.exists():
        msg = f"Deepseek script not found: {deepseek_script}"
        print_error(msg)
        log_to_file(log_file, f"✗ {msg}")
        return False, results
    
    # Count unprocessed articles
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0")
        unprocessed = cur.fetchone()[0]
        conn.close()
        print_info(f"Found {unprocessed} unprocessed article(s)")
        log_to_file(log_file, f"Found {unprocessed} unprocessed article(s)")
    except Exception as e:
        msg = f"Could not count unprocessed articles: {e}"
        print_error(msg)
        log_to_file(log_file, f"✗ {msg}")
        return False, results
    
    if unprocessed == 0:
        print_info("All articles already processed, skipping Deepseek phase")
        log_to_file(log_file, "All articles already processed, skipping")
        results['steps'].append({
            'step': 'deepseek_processing',
            'status': 'skipped',
            'reason': 'No unprocessed articles',
            'articles_processed': 0
        })
        return True, results
    
    # Process articles with Deepseek batch mode (with retry)
    print_info(f"Processing {unprocessed} article(s) with Deepseek API...")
    log_to_file(log_file, f"Starting batch processing of {unprocessed} articles")
    
    cmd = ['python3', str(deepseek_script)]
    
    # Try twice if it fails (timeout or error)
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        print_info(f"Deepseek processing attempt {attempt}/{max_attempts}...")
        log_to_file(log_file, f"Deepseek processing attempt {attempt}/{max_attempts}")
        
        success, stdout, stderr = run_command(
            cmd,
            "Deepseek batch processing complete",
            dry_run=dry_run,
            verbose=verbose,
            log_file=log_file,
            timeout=7200  # 2 hours for deepseek (takes longer)
        )
        
        if success:
            print_info(f"✓ Deepseek processing successful on attempt {attempt}")
            break
        else:
            if attempt < max_attempts:
                print_warning(f"Deepseek attempt {attempt} failed, retrying...")
                log_to_file(log_file, f"⚠ Attempt {attempt} failed, retrying...")
            else:
                print_error("Deepseek processing failed after all retries")
    
    if not success:
        log_to_file(log_file, "✗ Deepseek batch processing failed after retries")
        print_warning("Deepseek batch processing had issues, skipping insertion")
        results['steps'].append({
            'step': 'deepseek_api_processing',
            'status': 'failed',
            'articles_target': unprocessed,
            'articles_processed': 0
        })
        return False, results
    
    # Now insert all response files into database
    print_info("Inserting Deepseek responses into database...")
    log_to_file(log_file, "Starting response insertion into database")
    
    insert_script = PROJECT_ROOT / 'deepseek' / 'insert_from_response.py'
    if not insert_script.exists():
        msg = f"Insert script not found: {insert_script}"
        print_error(msg)
        log_to_file(log_file, f"✗ {msg}")
        return False, results
    
    # Get list of response files to insert
    responses_dir = PROJECT_ROOT / 'deepseek' / 'responses'
    response_files = sorted(responses_dir.glob('article_*_response.json'))
    
    if not response_files:
        print_warning("No response files found to insert")
        log_to_file(log_file, "⚠ No response files found to insert")
        results['articles_processed'] = 0
        results['steps'].append({
            'step': 'deepseek_insertion',
            'status': 'no_files',
            'articles_inserted': 0
        })
        return True, results
    
    inserted_count = 0
    failed_count = 0
    
    for response_file in response_files:
        # Extract article_id from filename (article_XXXXX_response.json)
        try:
            article_id = response_file.stem.split('_')[1]
            
            cmd = ['python3', str(insert_script), article_id, str(response_file)]
            
            success, _, _ = run_command(
                cmd,
                f"Inserting article {article_id}",
                dry_run=dry_run,
                verbose=False,  # Keep verbose=False to avoid spam
                log_file=log_file
            )
            
            if success:
                inserted_count += 1
            else:
                failed_count += 1
                log_to_file(log_file, f"⚠ Failed to insert article {article_id}")
        except Exception as e:
            failed_count += 1
            log_to_file(log_file, f"✗ Error processing {response_file.name}: {e}")
    
    print_info(f"Insertion complete: {inserted_count} inserted, {failed_count} failed")
    log_to_file(log_file, f"Insertion complete: {inserted_count} inserted, {failed_count} failed")
    
    # Count final processed articles
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1")
        processed = cur.fetchone()[0]
        conn.close()
        results['articles_processed'] = processed
        print_info(f"Total processed in database: {processed} article(s)")
        log_to_file(log_file, f"Total processed in database: {processed} article(s)")
    except Exception as e:
        msg = f"Could not verify final processed count: {e}"
        print_warning(msg)
        log_to_file(log_file, f"⚠ {msg}")
        results['articles_processed'] = inserted_count
    
    results['steps'].append({
        'step': 'deepseek_api_processing',
        'status': 'completed',
        'articles_target': unprocessed,
        'articles_api_called': len(response_files)
    })
    
    results['steps'].append({
        'step': 'deepseek_insertion',
        'status': 'completed',
        'articles_inserted': inserted_count,
        'articles_failed': failed_count
    })
    
    if not success:
        print_error("Deepseek processing encountered errors")
    else:
        print_success("Deepseek processing complete")
    
    return success, results


def phase_deepseek_with_retry(dry_run=False, verbose=False, max_passes=2):
    """
    PHASE 3 WITH RETRY: Deepseek processing with automatic retry for remaining articles
    
    Runs Deepseek processing up to max_passes times.
    - First pass: Process all unprocessed articles
    - Check database for how many were actually processed
    - If there are still unprocessed articles, run again (second pass)
    - Continue until all are processed or max passes reached
    
    Args:
        dry_run: Preview mode
        verbose: Verbose output
        max_passes: Maximum number of processing passes (default: 2)
    
    Returns: (success, combined_results)
    """
    print_header(f"PHASE 3: DEEPSEEK PROCESSING WITH RETRY (MAX {max_passes} PASSES)")
    
    combined_results = {
        'phase': 'deepseek_with_retry',
        'start_time': datetime.now().isoformat(),
        'passes': [],
        'total_processed': 0
    }
    
    for pass_num in range(1, max_passes + 1):
        print_info(f"\n{'='*60}")
        print_info(f"DEEPSEEK PROCESSING PASS {pass_num}/{max_passes}")
        print_info(f"{'='*60}\n")
        
        # Run one pass of deepseek processing
        success, pass_results = phase_deepseek(dry_run=dry_run, verbose=verbose)
        combined_results['passes'].append({
            'pass': pass_num,
            'result': pass_results
        })
        
        # Check how many articles are still unprocessed
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 1")
            processed = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM articles WHERE deepseek_processed = 0")
            remaining = cur.fetchone()[0]
            
            conn.close()
            
            combined_results['total_processed'] = processed
            print_info(f"\nAfter pass {pass_num}:")
            print_info(f"  - Processed: {processed} articles")
            print_info(f"  - Remaining: {remaining} articles")
            
            # If no remaining articles, we're done
            if remaining == 0:
                print_success(f"All articles processed after {pass_num} pass(es)!")
                combined_results['status'] = 'completed_all'
                combined_results['passes_used'] = pass_num
                return True, combined_results
            
            # If this is the last pass, show warning
            if pass_num == max_passes:
                if remaining > 0:
                    print_warning(f"Max passes ({max_passes}) reached with {remaining} articles still unprocessed")
                    print_warning("These will be retried in the next pipeline run")
                    combined_results['status'] = 'max_passes_reached'
                    combined_results['articles_still_remaining'] = remaining
                else:
                    combined_results['status'] = 'completed_all'
                    print_success(f"All articles processed!")
            
        except Exception as e:
            msg = f"Could not check processed count: {e}"
            print_error(msg)
            combined_results['status'] = 'error_checking_count'
            return False, combined_results
    
    print_info(f"\nDeepseek processing complete ({max_passes} passes)")
    combined_results['end_time'] = datetime.now().isoformat()
    return True, combined_results


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
Pipeline Phases:
  1. MINING      - Collect articles from RSS feeds (--mine)
  2. IMAGE       - Generate web and mobile versions (--images)
  3. DEEPSEEK    - AI analysis and enrichment (--deepseek)

Note: Purge/reset is separate (run manually: python3 tools/reset_all.py --force)

Examples:
  # Full pipeline (default 2 articles per seed)
  python3 pipeline.py --full

  # Full pipeline with 5 articles per seed
  python3 pipeline.py --full --articles-per-seed 5

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
    
    parser.add_argument("--mine", action="store_true",
                       help="Run mining cycle")
    parser.add_argument("--images", action="store_true",
                       help="Process images (web + mobile)")
    parser.add_argument("--deepseek", action="store_true",
                       help="Process articles with Deepseek API")
    parser.add_argument("--full", action="store_true",
                       help="Run complete pipeline: mine → images → deepseek → verify")
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
    if not any([args.mine, args.images, args.deepseek, args.full, args.verify]):
        print_error("Please specify at least one phase: --mine, --images, --deepseek, --full, or --verify")
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
    
    # Execute phases (NO PURGE - run separately)
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
        success, results = phase_deepseek_with_retry(dry_run=args.dry_run, verbose=args.verbose, max_passes=2)
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
