# Watermark Removal Tool (image_wm.py)

Automatically detects and removes watermarks from images before compression.

## Features

- **Automatic watermark detection** using edge detection and morphology
- **Text watermark removal** (BBC, CNN, Reuters, AFP, etc.)
- **Logo watermark removal** using content-aware inpainting
- **Batch processing** for entire directories
- **Smart detection** - only processes images with detected watermarks
- **Preserves original** until processing is complete

## Methods

### Auto (Default)
```bash
python3 tools/image_wm.py --auto --verbose
```
- Tries text detection first
- Falls back to logo detection
- Applies inpainting only if watermark found

### Text Watermark
```bash
python3 tools/image_wm.py --dir website/article_image/ --method text --verbose
```
- Detects text-based watermarks using edge detection
- Targets corner and edge regions

### Logo Watermark
```bash
python3 tools/image_wm.py --dir website/article_image/ --method logo --verbose
```
- Detects visual anomalies using LAB color space
- Focuses on corner/edge regions

## Usage Examples

**Process single image:**
```bash
python3 tools/image_wm.py --input article.jpg --output clean_article.jpg --verbose
```

**Process all images in website:**
```bash
python3 tools/image_wm.py --auto --verbose
```

**Process custom directory:**
```bash
python3 tools/image_wm.py --dir /path/to/images/ --method auto --verbose
```

## Workflow Integration

**Recommended workflow before compression:**
```bash
# Step 1: Remove watermarks
python3 tools/image_wm.py --auto --verbose

# Step 2: Compress images
python3 tools/imgcompress.py --auto
```

## How It Works

1. **Detection Phase**
   - Text watermarks: Edge detection + morphological operations
   - Logo watermarks: Color anomaly detection in LAB space
   - Smart filtering: Only targets regions likely to be watermarks (edges/corners)

2. **Removal Phase**
   - Uses OpenCV inpainting (Telea's method)
   - Content-aware fill to seamlessly remove detected regions
   - Preserves image quality and composition

3. **Output**
   - Cleaned images replace originals in-place
   - No watermark detected = original preserved
   - Verbose mode shows processing details

## Requirements

- OpenCV: `pip install opencv-python`
- NumPy: `pip install numpy`
- PIL/Pillow: Already installed

## Performance

- Single image: ~100-500ms depending on size
- Batch processing: ~500ms-1s per image
- Most images with no watermarks skip inpainting (fast)

## Notes

- Works best with RGB/JPG images
- Handles PNG and WebP formats
- Skips _mobile versions (already processed)
- Safe for repeated runs (no double-processing)

