#!/usr/bin/env python3
"""
Manual Watermark Removal - Precise control for testing
Focuses on specific regions of images
"""

import cv2
import numpy as np
from pathlib import Path
import sys

def remove_watermark_manual(input_path, output_path, region=None, method='inpaint'):
    """
    Manually remove watermark from specified region
    
    Args:
        input_path: Input image
        output_path: Output image
        region: (x, y, w, h) - region to remove. If None, auto-detect bottom-right
        method: 'inpaint' or 'blur'
    """
    try:
        # Read image
        img = cv2.imread(str(input_path))
        if img is None:
            print(f"❌ Could not read image: {input_path}")
            return False
        
        h, w = img.shape[:2]
        print(f"📷 Image size: {w}x{h}")
        
        # If no region specified, target bottom-right corner (typical logo location)
        if region is None:
            # Target bottom-right 20% of image
            x = int(w * 0.7)
            y = int(h * 0.8)
            region_w = int(w * 0.25)
            region_h = int(h * 0.18)
            region = (x, y, region_w, region_h)
        
        x, y, rw, rh = region
        print(f"🎯 Target region: x={x}, y={y}, w={rw}, h={rh}")
        
        # Create mask for the region
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y:y+rh, x:x+rw] = 255
        
        if method == 'inpaint':
            print("🔧 Using inpainting method...")
            # Dilate mask slightly
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask_dilated = cv2.dilate(mask, kernel, iterations=2)
            
            # Apply inpainting
            result = cv2.inpaint(img, mask_dilated, 3, cv2.INPAINT_TELEA)
        else:  # blur
            print("🔧 Using blur method...")
            result = img.copy()
            # Blur the region
            result[y:y+rh, x:x+rw] = cv2.GaussianBlur(img[y:y+rh, x:x+rw], (15, 15), 0)
        
        # Save result
        cv2.imwrite(str(output_path), result)
        print(f"✅ Saved to: {output_path}")
        
        # Show statistics
        original_size = Path(input_path).stat().st_size
        result_size = Path(output_path).stat().st_size
        print(f"📊 Original: {original_size/1024:.1f} KB → Result: {result_size/1024:.1f} KB")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual Watermark Removal')
    parser.add_argument('--input', required=True, help='Input image')
    parser.add_argument('--output', required=True, help='Output image')
    parser.add_argument('--region', help='Region to remove as x,y,w,h (default: auto bottom-right)')
    parser.add_argument('--method', choices=['inpaint', 'blur'], default='inpaint',
                       help='Removal method')
    
    args = parser.parse_args()
    
    region = None
    if args.region:
        region = tuple(map(int, args.region.split(',')))
    
    success = remove_watermark_manual(args.input, args.output, region, args.method)
    sys.exit(0 if success else 1)
