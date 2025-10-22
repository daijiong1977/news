#!/usr/bin/env python3
"""
Best-effort watermark remover using OpenCV inpainting.

Usage:
  python3 scripts/remove_watermark.py --input article_images/preview_xxx.jpg --output cleaned.jpg

Options:
  --mask MASK_FILE    : optional binary mask image where white pixels indicate watermark region
  --auto              : try an automatic heuristic to detect a top-right/source watermark

Notes:
  - This is a best-effort tool. Results vary by watermark style (text vs semi-transparent logo).
  - Requires `opencv-python` (cv2) and `numpy` installed in your environment.
  - Use responsibly: do not remove copyright or attribution for unauthorized redistribution.
"""
import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--mask')
    parser.add_argument('--auto', action='store_true')
    args = parser.parse_args()

    try:
        import cv2
        import numpy as np
    except Exception as e:
        print('Error: OpenCV (cv2) and numpy are required to run this script.')
        print('Install with: pip install opencv-python numpy')
        sys.exit(1)

    if not os.path.exists(args.input):
        print('Input file not found:', args.input)
        sys.exit(1)

    img = cv2.imread(args.input)
    if img is None:
        print('Failed to read image')
        sys.exit(1)

    h, w = img.shape[:2]

    mask = None
    if args.mask:
        if not os.path.exists(args.mask):
            print('Mask file not found:', args.mask)
            sys.exit(1)
        m = cv2.imread(args.mask, cv2.IMREAD_GRAYSCALE)
        if m is None:
            print('Failed to read mask file')
            sys.exit(1)
        _, mask = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)

    if mask is None and args.auto:
        # Heuristic: look for semi-transparent white-ish overlays in top-right quarter
        # Convert to gray and detect bright low-contrast regions
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Focus on top-right area (common watermark placement)
        xr = int(w * 0.5)
        yr = int(h * 0.0)
        area = gray[yr:int(h*0.4), xr:w]
        # adaptive threshold to capture light logos/text
        t = cv2.adaptiveThreshold(area, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 25, 10)
        # Post-process mask: remove small blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        t = cv2.morphologyEx(t, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = np.zeros((h,w), dtype=np.uint8)
        mask[yr:int(h*0.4), xr:w] = t
        # Optionally dilate to cover semi-transparent edges
        mask = cv2.dilate(mask, kernel, iterations=2)

    if mask is None:
        print('No mask provided and auto detection not selected. Nothing to do.')
        sys.exit(1)

    # Inpaint
    inpainted = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

    # Save output
    cv2.imwrite(args.output, inpainted)
    print('Wrote', args.output)

if __name__ == '__main__':
    main()
