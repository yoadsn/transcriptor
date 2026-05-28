"""Slice 9 — Import script (Surya → DB)."""
from sqlalchemy import func, select

from app.models.batch import Batch
from app.models.line import Line
from app.models.page import Page
from app.services.rules import mint_line_external_id
from scripts.import_batch import _parse_surya_page, import_batch

FIXTURE_BATCH = "batch-surya-test"
FIXTURE_SOURCE = "test-source"
FIXTURE_LICENSE = "cc-by-4.0"

SURYA_PAGES = [
    {
        "page_id": "page-001",
        "image_path": "images/p001.jpg",
        "width": 800,
        "height": 1200,
        "text_lines": [
            {"bbox": {"x": 10, "y": 20, "w": 400, "h": 28}, "confidence": 0.95},
            {"bbox": {"x": 10, "y": 60, "w": 400, "h": 28}, "confidence": 0.88},
        ],
    },
    {
        "page_id": "page-002",
        "image_path": "images/p002.jpg",
        "width": 800,
        "height": 1200,
        "text_lines": [
            {"bbox": {"x": 10, "y": 20, "w": 400, "h": 28}, "confidence": 0.91},
        ],
    },
]


def test_import_creates_expected_rows(db_session):
    pages_data = [_parse_surya_page(p) for p in SURYA_PAGES]
    import_batch(db_session, FIXTURE_BATCH, FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)

    assert db_session.execute(select(func.count(Batch.id)).where(Batch.external_id == FIXTURE_BATCH)).scalar_one() == 1
    assert db_session.execute(select(func.count(Page.id))).scalar_one() == 2
    assert db_session.execute(select(func.count(Line.id))).scalar_one() == 3


def test_reimport_same_fixture_no_new_rows(db_session):
    pages_data = [_parse_surya_page(p) for p in SURYA_PAGES]
    import_batch(db_session, FIXTURE_BATCH, FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)
    import_batch(db_session, FIXTURE_BATCH, FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)

    assert db_session.execute(select(func.count(Batch.id)).where(Batch.external_id == FIXTURE_BATCH)).scalar_one() == 1
    assert db_session.execute(select(func.count(Line.id))).scalar_one() == 3


def test_line_index_matches_reading_order(db_session):
    pages_data = [_parse_surya_page(SURYA_PAGES[0])]
    import_batch(db_session, FIXTURE_BATCH + "-idx", FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)

    lines = db_session.execute(select(Line).order_by(Line.line_index)).scalars().all()
    assert [l.line_index for l in lines] == [0, 1]


def test_polygon_and_confidence_persisted(db_session):
    surya_page = {
        "page_id": "page-poly",
        "image_path": "p.jpg",
        "width": 100,
        "height": 100,
        "text_lines": [
            {
                "bbox": {"x": 0, "y": 0, "w": 10, "h": 10},
                "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                "confidence": 0.75,
            }
        ],
    }
    pages_data = [_parse_surya_page(surya_page)]
    import_batch(db_session, FIXTURE_BATCH + "-poly", FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)

    line = db_session.execute(select(Line)).scalar_one()
    assert line.polygon is not None
    assert line.detection_confidence == 0.75


def test_minted_external_id_stable_no_duplication(db_session):
    pages_data = [_parse_surya_page(SURYA_PAGES[0])]
    import_batch(db_session, FIXTURE_BATCH + "-stable", FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)
    import_batch(db_session, FIXTURE_BATCH + "-stable", FIXTURE_SOURCE, FIXTURE_LICENSE, pages_data)

    count = db_session.execute(select(func.count(Line.id))).scalar_one()
    assert count == 2  # 2 lines in first page, no duplication

    # Verify external_id matches the mint function
    expected_id = mint_line_external_id(FIXTURE_BATCH + "-stable", "page-001", 0)
    line = db_session.execute(select(Line).where(Line.external_id == expected_id)).scalar_one_or_none()
    assert line is not None
