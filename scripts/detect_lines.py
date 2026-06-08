"""Detect text lines in images using horizontal projection and import as a batch.

Uses Pillow + numpy only. Works on manuscript/parchment images by using
per-image adaptive thresholding rather than a fixed pixel value.

Usage:
    uv run python scripts/detect_lines.py [--batch-id BATCH_ID] [--image-dir DIR]

Defaults:
    --batch-id   demo-batch-001
    --image-dir  data_sample
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from scripts.import_batch import import_batch

# ── tunable parameters ────────────────────────────────────────────────────────
SMOOTH_WINDOW = 15         # rows to average when smoothing the projection
GAP_RATIO = 0.20           # row is a "gap" if ink density < GAP_RATIO * peak density
MIN_GAP_ROWS = 3           # a gap must be at least this many rows to split lines
MIN_LINE_HEIGHT = 12       # discard detected regions shorter than this (px)
VERTICAL_PADDING = 3       # extra px added above/below each line bbox
HORIZONTAL_MARGIN = 0.005  # fraction of width trimmed from each side
# ─────────────────────────────────────────────────────────────────────────────


def _smooth(arr: np.ndarray, window: int) -> np.ndarray:
    kernel = np.ones(window) / window
    return np.convolve(arr, kernel, mode="same")


def _ink_projection(pixels: np.ndarray) -> np.ndarray:
    """Per-row ink density using an adaptive per-image threshold (Otsu-like).

    Rather than a fixed pixel value, we split "ink" from "background" at
    mean - 0.75*std of the image. On yellowish parchment this correctly
    classifies only the actual ink strokes as dark pixels.
    """
    mu = pixels.mean()
    sd = pixels.std()
    threshold = mu - 0.75 * sd
    ink = (pixels < threshold).astype(float)
    return ink.mean(axis=1)   # fraction of ink pixels per row


def detect_lines(image_path: Path) -> list[dict]:
    """Return list of bbox dicts {x, y, w, h} for each detected text line."""
    img = Image.open(image_path).convert("L")
    w, h = img.size
    pixels = np.array(img, dtype=float)

    row_ink = _ink_projection(pixels)
    smoothed = _smooth(row_ink, SMOOTH_WINDOW)

    peak = smoothed.max()
    if peak == 0:
        return []

    # adaptive gap threshold: relative to the densest text row in this image
    gap_threshold = peak * GAP_RATIO
    is_text_row = smoothed > gap_threshold

    # merge tiny gaps (< MIN_GAP_ROWS) back into text runs to avoid over-splitting
    # find gap runs and fill short ones
    in_gap = False
    gap_start = 0
    for r in range(h):
        if not is_text_row[r] and not in_gap:
            in_gap = True
            gap_start = r
        elif is_text_row[r] and in_gap:
            in_gap = False
            if (r - gap_start) < MIN_GAP_ROWS:
                is_text_row[gap_start:r] = True

    # collect contiguous text runs as line bboxes
    lines = []
    margin = int(w * HORIZONTAL_MARGIN)

    in_run = False
    run_start = 0
    for r in range(h):
        if is_text_row[r] and not in_run:
            in_run = True
            run_start = r
        elif not is_text_row[r] and in_run:
            in_run = False
            _add_line(lines, run_start, r, w, h, margin)
    if in_run:
        _add_line(lines, run_start, h, w, h, margin)

    return lines


def _add_line(lines, run_start, run_end, w, h, margin):
    if (run_end - run_start) >= MIN_LINE_HEIGHT:
        y1 = max(0, run_start - VERTICAL_PADDING)
        y2 = min(h, run_end + VERTICAL_PADDING)
        lines.append({"x": margin, "y": y1, "w": w - 2 * margin, "h": y2 - y1})


def build_pages_data(image_dir: Path, images: list[Path]) -> list[dict]:
    pages = []
    for img_path in images:
        bboxes = detect_lines(img_path)
        img = Image.open(img_path)
        w, h = img.size
        pages.append({
            "external_id": img_path.stem,
            "image_path": img_path.name,
            "width_px": w,
            "height_px": h,
            "lines": [
                {"line_index": i, "bbox": bbox}
                for i, bbox in enumerate(bboxes)
            ],
        })
        print(f"  {img_path.name}: {len(bboxes)} lines detected")
    return pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="demo-batch-001")
    parser.add_argument("--image-dir", default="data_sample")
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    if not image_dir.exists():
        print(f"Image directory not found: {image_dir}", file=sys.stderr)
        sys.exit(1)

    skip = {"OIP-4077272563.jpg"}
    images = sorted(
        p for p in image_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.name not in skip
    )
    if not images:
        print("No images found (after skipping seed image).", file=sys.stderr)
        sys.exit(1)

    print(f"Detecting lines in {len(images)} image(s) -> batch '{args.batch_id}'")
    pages_data = build_pages_data(image_dir, images)

    total_lines = sum(len(p["lines"]) for p in pages_data)
    if total_lines == 0:
        print("No lines detected. Try lowering GAP_RATIO.", file=sys.stderr)
        sys.exit(1)

    with SessionLocal() as session:
        import_batch(session, args.batch_id, "demo", "public-domain", pages_data)
        session.commit()

    print(f"Imported batch '{args.batch_id}': {len(pages_data)} pages, {total_lines} lines total.")


if __name__ == "__main__":
    main()
