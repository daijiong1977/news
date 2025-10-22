Watermark removal (best-effort)
================================

This repository includes a small, optional utility to attempt best-effort
watermark removal from downloaded preview images using OpenCV's inpainting.

Files
- `scripts/remove_watermark.py` — attempt to remove a watermark using a mask
  or a light automatic heuristic. Produces an inpainted output image.

Dependencies
- Python packages: `opencv-python`, `numpy`

Install:

```bash
pip install opencv-python numpy
```

Usage examples

- Manual mask (preferred when watermark position is known):

```bash
python3 scripts/remove_watermark.py --input article_images/preview_xxx.jpg --mask masks/mask_xxx.png --output cleaned.jpg
```

- Automatic heuristic (best-effort; looks in the top-right area for bright overlays):

```bash
python3 scripts/remove_watermark.py --input article_images/preview_xxx.jpg --auto --output cleaned.jpg
```

Caveats and legal / ethical note
- Removing watermarks can infringe on copyrights or violate terms of use.
  Use this tool only for local review purposes and never to redistribute
  content that you do not have the rights to modify or publish.
- The algorithm is heuristic and will not perfectly remove complex logos or
  patterned watermarks. Results vary widely depending on the watermark style,
  background complexity, and image quality.

Technical notes
- The script supports an input binary mask: white pixels mark areas to inpaint.
- When `--auto` is used, the script examines the top-right area and applies
  adaptive thresholding to detect bright overlays; this is intentionally
  conservative to avoid modifying important content.
- Inpainting uses OpenCV's `INPAINT_TELEA` method.

If you'd like, I can:
- Add a small helper to produce masks interactively (simple GUI) using OpenCV's
  polygon drawing tools.
- Integrate a per-feed site rule to avoid downloading images with visible
  publisher watermarks (e.g., prefer OG images hosted on a CDN without overlays).
