"""Seed the database with a dev batch using the data_sample image."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from scripts.import_batch import import_batch

IMAGE_FILE = "OIP-4077272563.jpg"
WIDTH = 474
HEIGHT = 218

# Three horizontal strips across the image
LINES = [
    {"line_index": 0, "bbox": {"x": 10, "y": 10,  "w": 454, "h": 60}},
    {"line_index": 1, "bbox": {"x": 10, "y": 80,  "w": 454, "h": 60}},
    {"line_index": 2, "bbox": {"x": 10, "y": 150, "w": 454, "h": 58}},
]

pages_data = [
    {
        "external_id": "page-001",
        "image_path": IMAGE_FILE,
        "width_px": WIDTH,
        "height_px": HEIGHT,
        "lines": LINES,
    }
]

with SessionLocal() as db:
    import_batch(db, "dev-batch-001", "dev", "public-domain", pages_data)
    db.commit()

print("Seeded dev-batch-001 with 1 page, 3 lines.")
