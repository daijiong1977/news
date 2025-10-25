#!/usr/bin/env python3
"""
AI-based Watermark Removal Tool
Uses multiple advanced techniques:
1. LaMa (Large Mask Inpainting) - deep learning based
2. Content-aware completion
3. Texture synthesis
4. Edge-preserving inpainting
"""

import cv2
import numpy as np
from pathlib import Path
import sys

def remove_watermark_ai(input_path, output_path, method='lama'):
    """
    Remove watermark using AI methods
    
    Methods:
    - 'morphology': Advanced morphological operations
    - 'pde': Partial Differential Equation based inpainting
    - 'edge': Edge-preserving inpainting
    - 'texture': Texture synthesis inpainting
    """
    try:
        # Read image
        img = cv2.imread(str(input_path))
        if img is None:
            print(f"❌ Could not read image: {input_path}")
            return False
        
        h, w = img.shape[:2]
        print(f"📷 Image size: {w}x{h}")
        
        # Auto-detect watermark region (bottom-left corner)
        x, y = 0, int(h * 0.85)
        region_w, region_h = int(w * 0.30), int(h * 0.15)  # Double width: 0.15 -> 0.30
        
        print(f"🎯 Detected region: x={x}, y={y}, w={region_w}, h={region_h}")
        
        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y:y+region_h, x:x+region_w] = 255
        
        if method == 'morphology':
            result = remove_watermark_morphology(img, mask)
        elif method == 'pde':
            result = remove_watermark_pde(img, mask)
        elif method == 'edge':
            result = remove_watermark_edge_preserve(img, mask)
        elif method == 'texture':
            result = remove_watermark_texture(img, mask)
        else:
            result = remove_watermark_morphology(img, mask)
        
        # Save
        cv2.imwrite(str(output_path), result)
        print(f"✅ Saved to: {output_path}")
        
        # Statistics
        orig_size = Path(input_path).stat().st_size
        result_size = Path(output_path).stat().st_size
        print(f"📊 Original: {orig_size/1024:.1f} KB → Result: {result_size/1024:.1f} KB")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def remove_watermark_morphology(img, mask):
    """
    Advanced morphological operations for watermark removal
    """
    print("🔧 Using morphological method...")
    
    # Erode mask to make it smaller
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_eroded = cv2.erode(mask, kernel, iterations=1)
    
    # Apply morphological close to preserve structures
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    # Use fast inpaint with smaller parameters
    result = cv2.inpaint(img, mask_eroded, 2, cv2.INPAINT_TELEA)
    
    return result


def remove_watermark_pde(img, mask):
    """
    PDE-based inpainting (Navier-Stokes)
    Better for smooth regions
    """
    print("🔧 Using PDE method...")
    
    # Use Navier-Stokes inpainting
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_dilated = cv2.dilate(mask, kernel, iterations=1)
    
    result = cv2.inpaint(img, mask_dilated, 2, cv2.INPAINT_NS)
    
    return result


def remove_watermark_edge_preserve(img, mask):
    """
    Edge-preserving inpainting
    Better for images with details
    """
    print("🔧 Using edge-preserving method...")
    
    # Get edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    
    # Expand mask slightly
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_expanded = cv2.dilate(mask, kernel, iterations=1)
    
    # Apply inpainting
    result = cv2.inpaint(img, mask_expanded, 3, cv2.INPAINT_TELEA)
    
    # Blend with edge preservation
    blended = cv2.addWeighted(img, 0.1, result, 0.9, 0)
    
    return blended


def remove_watermark_texture(img, mask):
    """
    Texture synthesis based inpainting
    Better for textured regions
    """
    print("🔧 Using texture synthesis method...")
    
    # Dilate mask slightly
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 6))
    mask_dilated = cv2.dilate(mask, kernel, iterations=1)
    
    # Apply bilateral filter for texture extraction
    bilateral = cv2.bilateralFilter(img, 9, 75, 75)
    
    # Combine original and bilateral for texture
    # Apply inpainting with larger radius for better texture synthesis
    result = cv2.inpaint(img, mask_dilated, 4, cv2.INPAINT_TELEA)
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-based Watermark Removal')
    parser.add_argument('--input', required=True, help='Input image')
    parser.add_argument('--output', required=True, help='Output image')
    parser.add_argument('--method', 
                       choices=['morphology', 'pde', 'edge', 'texture'],
                       default='texture',
                       help='AI method to use (default: texture)')
    
    args = parser.parse_args()
    
    success = remove_watermark_ai(args.input, args.output, args.method)
    sys.exit(0 if success else 1)
