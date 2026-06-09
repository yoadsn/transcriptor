#!/usr/bin/env python3
"""
Seed the database with demo data: 7 manuscript images, each split into 20 equal lines.
Idempotent — skips if the 'demo' batch already exists.
Run with: python scripts/seed_demo.py
"""
import os
import struct
import sys
import uuid

# ── DB setup ────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_fGTvI0B2esjM@ep-old-boat-appf9jln.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require",
)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.models.batch import Batch
from app.models.line import Line
from app.models.page import Page

engine = create_engine(DATABASE_URL)

# ── Image dimension reader (no Pillow needed) ────────────────────────────────

def _jpeg_dims(path: str) -> tuple[int, int]:
    """Return (width, height) by parsing JPEG SOF markers."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2  # skip SOI (0xFFD8)
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = (data[i] << 8) | data[i + 1]
        i += 2
        if marker in (0xFFC0, 0xFFC1, 0xFFC2):  # SOF0/1/2
            # segment: length(2) precision(1) height(2) width(2)
            h = (data[i + 3] << 8) | data[i + 4]
            w = (data[i + 5] << 8) | data[i + 6]
            return w, h
        if marker == 0xFFD9:
            break
        seg_len = (data[i] << 8) | data[i + 1]
        i += seg_len
    raise ValueError(f"Cannot read JPEG dimensions from {path}")


# ── Seed ─────────────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_sample")
DEMO_BATCH_EXTERNAL_ID = "demo-data-sample-v2"
N_LINES = 10

IMAGE_FILES = sorted(
    f for f in os.listdir(DATA_DIR) if f.lower().endswith((".jpg", ".jpeg"))
)
if not IMAGE_FILES:
    print("No JPEG files found in data_sample/")
    sys.exit(1)

print(f"Found {len(IMAGE_FILES)} images: {IMAGE_FILES}")

with Session(engine) as db:
    # Idempotency check
    existing = db.execute(
        select(Batch).where(Batch.external_id == DEMO_BATCH_EXTERNAL_ID)
    ).scalar_one_or_none()

    if existing:
        print(f"Demo batch already exists (id={existing.id}). Nothing to do.")
        sys.exit(0)

    # Create batch
    batch = Batch(
        external_id=DEMO_BATCH_EXTERNAL_ID,
        source="demo",
        license="CC0",
    )
    db.add(batch)
    db.flush()
    print(f"Created batch {batch.id}")

    for img_file in IMAGE_FILES:
        img_path = os.path.join(DATA_DIR, img_file)
        width, height = _jpeg_dims(img_path)
        print(f"  {img_file}: {width}x{height}px")

        page = Page(
            batch_id=batch.id,
            external_id=img_file,
            image_path=img_file,           # resolves to /images/<img_file>
            width_px=width,
            height_px=height,
        )
        db.add(page)
        db.flush()

        line_h = height / N_LINES
        for i in range(N_LINES):
            y = round(i * line_h)
            h = round((i + 1) * line_h) - y
            line = Line(
                page_id=page.id,
                line_index=i,
                bbox={"x": 0, "y": y, "w": width, "h": h},
                polygon=None,
                detection_confidence=None,
                transcription_count=0,
                external_id=f"{img_file}-line-{i:02d}",
            )
            db.add(line)

        print(f"    added {N_LINES} lines")

    db.commit()
    print("\nDone — demo data seeded successfully.")
