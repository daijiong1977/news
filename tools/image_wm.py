#!/usr/bin/env python3
"""
Watermark Removal Tool - Remove watermarks from images before compression

Supported watermark removal methods:
- Text watermark detection and removal (BBC NEWS, CNN, etc.)
- Logo watermark removal using inpainting
- Edge-based watermark detection
- Content-aware fill using OpenCV inpainting

Usage:
    python3 image_wm.py --input image.jpg --output clean_image.jpg
    python3 image_wm.py --dir website/article_image/ --auto
    python3 image_wm.py --input image.jpg --method inpaint --output clean.jpg
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
import os
import cv2
import numpy as np
from datetime import datetime

# Get script directory
SCRIPT_DIR = Path(__file__).parent.parent
WEBSITE_DIR = SCRIPT_DIR / "website"
WATERMARK_CHECKPOINT = SCRIPT_DIR / ".image_wm_checkpoint.json"

# Watermark detection parameters
COMMON_WATERMARKS = ['BBC', 'CNN', 'REUTERS', 'AFP', 'AP', 'NBC', 'CBS', 'FOX', 'GETTY', 'SHUTTERSTOCK']
MIN_WATERMARK_SIZE = 20  # Minimum watermark area in pixels


def detect_text_watermark(image_cv):
    """
    Detect text-based watermarks using edge detection and morphology
    Returns: mask of detected watermark regions
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask for potential watermarks
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        # Filter contours by size and shape (watermarks are usually rectangular and in corners/edges)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < MIN_WATERMARK_SIZE:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check if watermark is likely in corner or edge (typical for logos/text)
            h_img, w_img = gray.shape
            is_in_corner = (x < w_img * 0.2 or x + w > w_img * 0.8) and (y < h_img * 0.2 or y + h > h_img * 0.8)
            is_in_edge = (x < w_img * 0.15) or (x + w > w_img * 0.85) or (y < h_img * 0.15) or (y + h > h_img * 0.85)
            
            if is_in_corner or is_in_edge:
                cv2.drawContours(mask, [contour], 0, 255, -1)
        
        return mask
    except Exception as e:
        print(f"  Warning: Text watermark detection failed: {e}", file=sys.stderr)
        return None


def detect_logo_watermark(image_cv):
    """
    Detect logo/image watermarks using color anomaly detection
    Returns: mask of detected watermark regions
    """
    try:
        # Convert to LAB color space for better anomaly detection
        lab = cv2.cvtColor(image_cv, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Create mask using threshold on all channels
        # Watermarks often have distinct color characteristics
        mask = np.zeros(l.shape, dtype=np.uint8)
        
        # Apply morphological operations to find distinct regions
        for channel in [l, a, b]:
            # Threshold
            _, thresh = cv2.threshold(channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological opening to remove small objects
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            mask = cv2.bitwise_or(mask, opened)
        
        # Filter to regions likely to be watermarks (usually corners/edges)
        h, w = mask.shape
        for y in range(h):
            for x in range(w):
                # Keep only edge regions
                is_edge = (x < w * 0.1 or x > w * 0.9) or (y < h * 0.1 or y > h * 0.9)
                if not is_edge:
                    mask[y, x] = 0
        
        return mask if np.any(mask > 0) else None
    except Exception as e:
        print(f"  Warning: Logo watermark detection failed: {e}", file=sys.stderr)
        return None


def remove_watermark_inpaint(image_cv, mask):
    """
    Remove watermark using content-aware inpainting
    """
    try:
        if mask is None or not np.any(mask > 0):
            return image_cv
        
        # Dilate mask slightly to ensure full watermark removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask_dilated = cv2.dilate(mask, kernel, iterations=2)
        
        # Apply inpainting using Telea or Navier-Stokes method
        inpainted = cv2.inpaint(image_cv, mask_dilated, 3, cv2.INPAINT_TELEA)
        
        return inpainted
    except Exception as e:
        print(f"  Warning: Inpainting failed: {e}", file=sys.stderr)
        return image_cv


def process_image_watermark(input_path, output_path=None, verbose=False, method='auto'):
    """
    Process image to remove watermarks
    
    Args:
        input_path: Path to input image
        output_path: Path to save cleaned image (default: overwrite input)
        verbose: Print progress
        method: 'auto', 'text', 'logo', or 'inpaint'
    
    Returns: (success, detected_watermark)
    """
    try:
        input_file = Path(input_path)
        
        if not input_file.exists():
            print(f"  ✗ File not found: {input_file}", file=sys.stderr)
            return False, False
        
        # Read image
        image_cv = cv2.imread(str(input_file))
        if image_cv is None:
            print(f"  ✗ Could not read image: {input_file}", file=sys.stderr)
            return False, False
        
        detected_watermark = False
        mask = None
        
        # Auto-detect watermark
        if method in ['auto', 'text']:
            mask = detect_text_watermark(image_cv)
            if mask is not None and np.any(mask > 0):
                detected_watermark = True
                if verbose:
                    print(f"  ✓ Text watermark detected in {input_file.name}")
        
        # If no text watermark, try logo detection
        if not detected_watermark and method in ['auto', 'logo']:
            mask = detect_logo_watermark(image_cv)
            if mask is not None and np.any(mask > 0):
                detected_watermark = True
                if verbose:
                    print(f"  ✓ Logo watermark detected in {input_file.name}")
        
        # Remove watermark if detected
        if detected_watermark:
            cleaned_image = remove_watermark_inpaint(image_cv, mask)
            
            # Save cleaned image
            output_file = Path(output_path) if output_path else input_file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(str(output_file), cleaned_image)
            
            if verbose:
                print(f"  ✓ Watermark removed: {output_file.name}")
            
            return True, True
        else:
            if verbose:
                print(f"  - No watermark detected: {input_file.name}")
            
            # Still copy to output if specified
            if output_path and str(output_path) != str(input_file):
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy(input_file, output_file)
            
            return True, False
    
    except Exception as e:
        print(f"  ✗ Error processing {input_path}: {e}", file=sys.stderr)
        return False, False


def process_directory(directory, verbose=False, method='auto'):
    """
    Process all images in directory for watermark removal
    """
    directory = Path(directory)
    
    if not directory.exists():
        print(f"✗ Directory not found: {directory}")
        return
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(directory.glob(f'*{ext}'))
        image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No images found in {directory}")
        return
    
    print(f"\n🔍 Watermark Removal - Processing {len(image_files)} images from {directory.name}/")
    print(f"Method: {method}")
    print("-" * 60)
    
    watermark_count = 0
    success_count = 0
    
    for image_file in sorted(image_files):
        # Skip already processed _mobile versions
        if '_mobile' in image_file.name:
            continue
        
        # Create temporary output path
        temp_output = image_file.parent / f"{image_file.stem}_wm_removed{image_file.suffix}"
        
        success, has_watermark = process_image_watermark(image_file, temp_output, verbose, method)
        
        if success:
            success_count += 1
            if has_watermark:
                watermark_count += 1
                # Replace original with cleaned version
                import shutil
                shutil.move(temp_output, image_file)
            else:
                # No watermark, remove temp file
                temp_output.unlink(missing_ok=True)
    
    print("-" * 60)
    print(f"✓ Processed: {success_count}/{len(image_files)}")
    print(f"✓ Watermarks removed: {watermark_count}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Watermark Removal Tool')
    parser.add_argument('--input', help='Input image file')
    parser.add_argument('--output', help='Output image file (default: overwrite input)')
    parser.add_argument('--dir', help='Process all images in directory')
    parser.add_argument('--method', choices=['auto', 'text', 'logo', 'inpaint'], default='auto',
                       help='Watermark removal method (default: auto)')
    parser.add_argument('--auto', action='store_true', help='Process website/article_image/ directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.auto:
        images_dir = WEBSITE_DIR / 'article_image'
        process_directory(images_dir, args.verbose, args.method)
    elif args.dir:
        process_directory(args.dir, args.verbose, args.method)
    elif args.input:
        output = args.output if args.output else args.input
        success, has_watermark = process_image_watermark(args.input, output, args.verbose, args.method)
        if success:
            if has_watermark:
                print(f"✓ Watermark removed: {output}")
            else:
                print(f"- No watermark detected: {output}")
        else:
            print(f"✗ Failed to process: {args.input}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
