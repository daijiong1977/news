#!/usr/bin/env python3
"""
Image Optimizer Tool - Generate optimized image versions

Workflow:
1. ALL VERSIONS: Compress to <60KB WebP (resize to fit 1024×768, keep aspect ratio)
2. Same compression applied for web, mobile, email, and all channels
3. Single optimized image used across all platforms

Supported formats:
- JPG / JPEG → WebP (<60KB)
- PNG → WebP (<60KB)
- WebP → WebP optimized (<60KB)

Usage:
    python3 imgcompress.py --input image.jpg --web
    python3 imgcompress.py --input image.jpg --mobile
    python3 imgcompress.py --dir website/article_image/ --web --mobile
    python3 imgcompress.py --dir website/article_image/ --auto
"""

import argparse
import sys
from pathlib import Path
from PIL import Image
import os
import json
import sqlite3
from datetime import datetime
import re

# Get script directory
SCRIPT_DIR = Path(__file__).parent.parent
WEBSITE_DIR = SCRIPT_DIR / "website"
DB_PATH = SCRIPT_DIR / "articles.db"
CHECKPOINT_FILE = SCRIPT_DIR / ".imgcompress_checkpoint.json"

# Image dimensions - unified for all versions
IMAGE_MAX_DIMENSIONS = (1024, 768)  # All versions: 1024×768, compress to <60KB
TARGET_SIZE = 60000  # 60KB for all channels (web, mobile, email)


def load_checkpoint():
    """Load checkpoint data tracking processed images"""
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_checkpoint(checkpoint):
    """Save checkpoint data to file"""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save checkpoint: {e}", file=sys.stderr)


def is_already_resized(filename):
    """Check if file has already been resized"""
    return '_mobile' in filename


def update_database_mobile_location(article_id, image_name, mobile_location):
    """Update article_images table with mobile_location"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        # Check if small_location column exists, if not use it for mobile_location
        cur.execute(
            "UPDATE article_images SET small_location = ? WHERE article_id = ? AND image_name = ?",
            (str(mobile_location), str(article_id), image_name)
        )
        
        conn.commit()
        conn.close()
        
        return cur.rowcount > 0
    except Exception as e:
        if "--verbose" in sys.argv or "-v" in sys.argv:
            print(f"  Warning: Could not update DB for article {article_id}: {e}", file=sys.stderr)
        return False


def resize_image_web(input_path, output_path=None, verbose=False):
    """
    Deprecated - use compress_image_mobile instead (unified compression)
    
    Returns: (success, original_size, new_size)
    """
    return compress_image_mobile(input_path, output_path, verbose)[:3]


def compress_image_mobile(input_path, output_path, verbose=False):
    """
    Compress image: fit within 1024×768, compress to <60KB, save as WebP
    
    Returns: (success, original_size, compressed_size, quality_used)
    """
    try:
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        original_size = input_file.stat().st_size
        
        if verbose:
            print(f"  {input_file.name} → {output_file.name}")
        
        # Open image
        img = Image.open(input_file)
        original_width, original_height = img.size
        
        # Convert RGBA to RGB if needed (for WebP)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Calculate scale to fit within 1024×768
        max_width, max_height = IMAGE_MAX_DIMENSIONS
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
        
        if scale_ratio < 1.0:
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            if verbose:
                print(f"    Resized: {original_width}x{original_height} → {new_width}x{new_height}")
            
            original_width, original_height = new_width, new_height
        else:
            if verbose:
                print(f"    Already fits {original_width}x{original_height} within {max_width}x{max_height}")
        
        # Binary search for optimal WebP compression
        current_quality = 85
        current_scale = 1.0
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Calculate new dimensions if scaling
            new_width = int(original_width * current_scale)
            new_height = int(original_height * current_scale)
            
            # Ensure minimum dimensions
            if new_width < 50 or new_height < 50:
                break
            
            # Resize and save
            if current_scale < 1.0:
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                resized_img = img
            
            # Save as WebP
            resized_img.save(output_file, format='WEBP', quality=current_quality, method=6)
            
            # Check size
            compressed_size = output_file.stat().st_size
            
            if verbose and iteration % 5 == 0:
                print(f"    Iteration {iteration}: {compressed_size / 1024:.1f} KB (quality={current_quality})")
            
            # Check if we're within target
            if compressed_size <= TARGET_SIZE:
                if verbose:
                    print(f"    ✓ {output_file.name}: {compressed_size / 1024:.1f} KB (quality={current_quality})")
                
                return True, original_size, compressed_size, current_quality
            
            # Not yet at target, try different strategies
            if current_quality > 40:
                # Reduce quality
                current_quality = max(current_quality - 5, 40)
            elif current_scale >= 1.0:
                # Haven't scaled yet, start scaling
                current_scale = 0.95
            else:
                # Both at minimum, scale more aggressively
                current_scale *= 0.9
            
            # Prevent infinite loop
            if current_scale < 0.1 and current_quality <= 40:
                print(f"  ⚠ Warning: Could not compress to target size. Saved at {compressed_size / 1024:.1f} KB")
                return False, original_size, compressed_size, current_quality
        
        # Final save
        resized_img.save(output_file, format='WEBP', quality=current_quality, method=6)
        compressed_size = output_file.stat().st_size
        
        if verbose:
            print(f"    ✓ {output_file.name}: {compressed_size / 1024:.1f} KB (quality={current_quality})")
        
        return True, original_size, compressed_size, current_quality
        
    except Exception as e:
        print(f"  ✗ Error compressing {input_path}: {e}", file=sys.stderr)
        return False, 0, 0, 0


def process_directory(input_dir, web=False, mobile=False, dry_run=False, verbose=False, auto_mode=False, resume=False):
    """
    Process all images in directory.
    
    If auto_mode=True: process images that don't have web/mobile versions yet
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory not found: {input_dir}")
        return 0, 0
    
    # Load checkpoint if resuming
    checkpoint = {}
    resume_from = None
    if auto_mode and resume:
        checkpoint = load_checkpoint()
        if checkpoint and 'directory' in checkpoint and checkpoint['directory'] == str(input_path):
            resume_from = checkpoint.get('last_processed')
            if verbose:
                print(f"Resuming from: {resume_from}")
    
    # Find all image files (only JPG/PNG/original WebP, skip _mobile files)
    image_extensions = ('.jpg', '.jpeg', '.png')
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    # Also include original WebP files (those without _mobile in name)
    for webp_file in input_path.glob('*.webp'):
        if '_mobile' not in webp_file.name:
            image_files.append(webp_file)
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return 0, 0
    
    image_files = sorted(image_files)
    
    # In auto_mode, filter out already-processed images
    if auto_mode:
        filtered_files = []
        for img_file in image_files:
            if is_already_resized(img_file.name):
                if verbose:
                    print(f"[OK] Already processed: {img_file.name}")
            else:
                filtered_files.append(img_file)
        
        image_files = filtered_files
        
        if resume_from:
            # Find index of resume_from
            for i, f in enumerate(image_files):
                if f.name == resume_from:
                    image_files = image_files[i+1:]
                    break
        
        if image_files:
            print(f"Found {len(image_files)} image file(s) to process")
        else:
            print("No new images to process")
            return 0, 0
    
    total_web_size = 0
    total_mobile_size = 0
    processed_count = 0
    
    for idx, img_file in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] Processing: {img_file.name}")
        print("=" * 80)
        
        # Extract article_id from filename (article_1.jpg → 1)
        match = re.match(r'article_(\d+|[\d-]+)', img_file.name)
        article_id = match.group(1) if match else None
        
        if web:
            if dry_run:
                print(f"  [DRY-RUN] Would resize for web: {img_file} → {img_file}")
            else:
                success, orig_size, new_size = resize_image_web(img_file, img_file, verbose=verbose)
                if success:
                    total_web_size += new_size
        
        if mobile:
            # Create mobile filename: article_1.jpg → article_1_mobile.webp
            mobile_filename = f"{img_file.stem}_mobile.webp"
            mobile_path = img_file.parent / mobile_filename
            
            # Check if _mobile version already exists and is under 60KB
            if mobile_path.exists():
                mobile_size = mobile_path.stat().st_size
                if mobile_size <= TARGET_SIZE:
                    if verbose:
                        print(f"  ✓ Skipping: {mobile_path.name} already {mobile_size / 1024:.1f} KB (under {TARGET_SIZE/1024:.0f}KB)")
                    continue
                else:
                    if verbose:
                        print(f"  ⚠ Reprocessing: {mobile_path.name} is {mobile_size / 1024:.1f} KB (over {TARGET_SIZE/1024:.0f}KB)")
            
            if dry_run:
                print(f"  [DRY-RUN] Would create: {img_file} → {mobile_path}")
            else:
                success, orig_size, comp_size, quality = compress_image_mobile(img_file, mobile_path, verbose=verbose)
                if success:
                    total_mobile_size += comp_size
                    
                    # Update database if in article_image directory
                    if str(img_file.parent) == str(WEBSITE_DIR / "article_image"):
                        if article_id:
                            update_database_mobile_location(article_id, img_file.name, str(mobile_path))
        
        processed_count += 1
        
        # Update checkpoint
        if auto_mode:
            checkpoint = {
                'directory': str(input_path),
                'last_processed': img_file.name,
                'timestamp': datetime.now().isoformat(),
                'processed_count': processed_count
            }
            save_checkpoint(checkpoint)
    
    print("\n" + "=" * 80)
    if web:
        print(f"✓ Web versions: {total_web_size / 1024 / 1024:.1f} MB total")
    if mobile:
        print(f"✓ Mobile versions: {total_mobile_size / 1024 / 1024:.1f} MB total")
    print(f"✓ Processed {processed_count} file(s)")
    
    return processed_count, total_mobile_size


def main():
    parser = argparse.ArgumentParser(
        description="Generate web and mobile versions of images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resize single image for web (1024×768, keep format)
  python3 imgcompress.py --input image.jpg --web
  
  # Create mobile version (600×450, WebP, <50KB)
  python3 imgcompress.py --input image.jpg --mobile
  
  # Both web and mobile versions
  python3 imgcompress.py --input image.jpg --web --mobile
  
  # Process all images in directory (auto-mode, skip processed)
  python3 imgcompress.py --dir website/article_image/ --auto --web --mobile
  
  # Resume auto-mode from last checkpoint
  python3 imgcompress.py --dir website/article_image/ --auto --resume --web --mobile
  
  # Only mobile versions
  python3 imgcompress.py --dir website/article_image/ --mobile -v
  
  # Preview without making changes
  python3 imgcompress.py --dir website/article_image/ --web --mobile --dry-run
        """
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", type=str, help="Single image file")
    input_group.add_argument("--dir", type=str, help="Directory containing images")
    
    parser.add_argument("--web", action="store_true", 
                       help=f"Generate web version (<{TARGET_SIZE/1024:.0f}KB WebP, 1024×768)")
    parser.add_argument("--mobile", action="store_true", 
                       help=f"Generate mobile version (<{TARGET_SIZE/1024:.0f}KB WebP, 1024×768)")
    parser.add_argument("--auto", action="store_true", 
                       help="Auto-mode: process only images that don't have versions yet, track progress")
    parser.add_argument("--resume", action="store_true", 
                       help="Resume from last checkpoint (requires --auto)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without processing")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.resume and not args.auto:
        print("Error: --resume requires --auto mode", file=sys.stderr)
        sys.exit(1)
    
    if args.input:
        # Single file processing
        input_file = Path(args.input)
        if not input_file.exists():
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Processing: {input_file.name}")
        print("=" * 80)
        
        if args.web:
            print("→ Web version")
            success, orig_size, new_size = resize_image_web(input_file, verbose=args.verbose)
            if success and args.verbose:
                print(f"  Reduction: {orig_size / 1024:.1f} KB → {new_size / 1024:.1f} KB")
        
        if args.mobile:
            mobile_filename = f"{input_file.stem}_mobile.webp"
            mobile_path = input_file.parent / mobile_filename
            print("→ Mobile version")
            success, orig_size, comp_size, quality = compress_image_mobile(input_file, mobile_path, verbose=args.verbose)
    
    elif args.dir:
        # Directory processing
        if not args.web and not args.mobile:
            print("Error: Specify at least --web or --mobile", file=sys.stderr)
            sys.exit(1)
        
        print(f"Processing directory: {args.dir}")
        print("=" * 80)
        
        process_directory(
            args.dir, 
            web=args.web, 
            mobile=args.mobile,
            dry_run=args.dry_run,
            verbose=args.verbose,
            auto_mode=args.auto,
            resume=args.resume
        )


if __name__ == "__main__":
    main()
