"""Import a Surya batch into the database.

Usage:
    uv run python scripts/import_batch.py <batch_external_id> <source> <license> <surya_json_path>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.batch import Batch
from app.models.line import Line
from app.models.page import Page
from app.services.rules import mint_line_external_id


def _parse_surya_page(surya_page: dict) -> dict:
    """Adapter: isolates Surya JSON shape from the rest of the import logic."""
    return {
        "external_id": surya_page["page_id"],
        "image_path": surya_page["image_path"],
        "width_px": surya_page["width"],
        "height_px": surya_page["height"],
        "lines": [
            {
                "line_index": i,
                "bbox": line["bbox"],
                "polygon": line.get("polygon"),
                "detection_confidence": line.get("confidence"),
            }
            for i, line in enumerate(surya_page.get("text_lines", []))
        ],
    }


def import_batch(
    session: Session,
    external_id: str,
    source: str,
    license_: str,
    pages_data: list[dict],
) -> Batch:
    batch = session.execute(
        select(Batch).where(Batch.external_id == external_id)
    ).scalar_one_or_none()
    if batch is None:
        batch = Batch(external_id=external_id, source=source, license=license_)
        session.add(batch)
        session.flush()
    else:
        batch.source = source
        batch.license = license_

    for page_data in pages_data:
        page = session.execute(
            select(Page).where(
                Page.batch_id == batch.id,
                Page.external_id == page_data["external_id"],
            )
        ).scalar_one_or_none()
        if page is None:
            page = Page(
                batch_id=batch.id,
                external_id=page_data["external_id"],
                image_path=page_data["image_path"],
                width_px=page_data["width_px"],
                height_px=page_data["height_px"],
            )
            session.add(page)
            session.flush()
        else:
            page.image_path = page_data["image_path"]
            page.width_px = page_data["width_px"]
            page.height_px = page_data["height_px"]

        for line_data in page_data["lines"]:
            ext_id = mint_line_external_id(external_id, page_data["external_id"], line_data["line_index"])
            line = session.execute(
                select(Line).where(
                    Line.page_id == page.id,
                    Line.external_id == ext_id,
                )
            ).scalar_one_or_none()
            if line is None:
                line = Line(
                    page_id=page.id,
                    external_id=ext_id,
                    line_index=line_data["line_index"],
                    bbox=line_data["bbox"],
                    polygon=line_data.get("polygon"),
                    detection_confidence=line_data.get("detection_confidence"),
                )
                session.add(line)
            else:
                line.line_index = line_data["line_index"]
                line.bbox = line_data["bbox"]
                line.polygon = line_data.get("polygon")
                line.detection_confidence = line_data.get("detection_confidence")

    session.flush()
    return batch


def main() -> None:
    if len(sys.argv) != 5:
        print("Usage: import_batch.py <batch_id> <source> <license> <surya_json>")
        sys.exit(1)
    _, batch_id, source, license_, json_path = sys.argv
    surya_data = json.loads(Path(json_path).read_text())
    pages_data = [_parse_surya_page(p) for p in surya_data["pages"]]
    with SessionLocal() as session:
        import_batch(session, batch_id, source, license_, pages_data)
        session.commit()
    print(f"Imported batch {batch_id}")


if __name__ == "__main__":
    main()
