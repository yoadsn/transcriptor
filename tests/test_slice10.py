"""Slice 10 — Export scripts (faithful dumps)."""
from app.models.transcription import TranscriptionKind
from app.models.user import User
from app.services.transcriptions import submit_response
from scripts.export_dataset import export_dataset
from scripts.export_telemetry import export_telemetry
from scripts.import_batch import _parse_surya_page, import_batch
from tests.conftest import make_batch, make_line, make_page


SURYA_PAGE = {
    "page_id": "export-page-1",
    "image_path": "export.jpg",
    "width": 400,
    "height": 600,
    "text_lines": [
        {"bbox": {"x": 0, "y": 0, "w": 10, "h": 10}, "confidence": 0.9},
        {"bbox": {"x": 0, "y": 20, "w": 10, "h": 10}, "confidence": 0.8},
    ],
}


def _seed(db, batch_ext="b-export"):
    pages_data = [_parse_surya_page(SURYA_PAGE)]
    batch = import_batch(db, batch_ext, "source", "cc0", pages_data)
    return batch


def _user(db, sub):
    u = User(google_sub=sub, email=f"{sub}@t.com", display_name=sub)
    db.add(u)
    db.flush()
    return u


def test_dataset_export_includes_all_transcriptions(db_session):
    batch = _seed(db_session)
    from sqlalchemy import select
    from app.models.line import Line
    lines = db_session.execute(select(Line)).scalars().all()
    line = lines[0]

    u1 = _user(db_session, "u-exp-1")
    u2 = _user(db_session, "u-exp-2")
    submit_response(db_session, u1, line.id, TranscriptionKind.text, "transcription1")
    submit_response(db_session, u2, line.id, TranscriptionKind.cant_read, None)

    records = export_dataset(db_session)
    target = next(r for r in records if r["line_id"] == str(line.id))
    assert len(target["transcriptions"]) == 2
    kinds = {t["kind"] for t in target["transcriptions"]}
    assert kinds == {"text", "cant_read"}


def test_dataset_record_count_equals_line_count(db_session):
    _seed(db_session, "b-count")
    records = export_dataset(db_session)
    from sqlalchemy import select, func
    from app.models.line import Line
    db_count = db_session.execute(select(func.count(Line.id))).scalar_one()
    assert len(records) == db_count


def test_dataset_includes_provenance(db_session):
    _seed(db_session, "b-prov")
    records = export_dataset(db_session)
    r = records[0]
    assert r["batch"]["source"] == "source"
    assert r["batch"]["license"] == "cc0"
    assert "image_path" in r["page"]


def test_telemetry_export_row_count_matches_events(db_session):
    _seed(db_session, "b-telem")
    from sqlalchemy import select, func
    from app.models.line import Line
    lines = db_session.execute(select(Line)).scalars().all()
    u = _user(db_session, "u-telem")
    submit_response(db_session, u, lines[0].id, TranscriptionKind.text, "x")

    from app.models.event import Event
    db_event_count = db_session.execute(select(func.count(Event.id))).scalar_one()
    telem_records = export_telemetry(db_session)
    assert len(telem_records) == db_event_count


def test_dataset_and_telemetry_have_separate_schemas(db_session):
    _seed(db_session, "b-schema")
    dataset_records = export_dataset(db_session)
    telemetry_records = export_telemetry(db_session)

    dataset_keys = set(dataset_records[0].keys()) if dataset_records else set()
    telem_keys = set(telemetry_records[0].keys()) if telemetry_records else set()

    # Dataset must not have behavioural/event fields
    event_fields = {"event_type", "payload"}
    assert not dataset_keys.intersection(event_fields)
    # Telemetry must not have content fields
    content_fields = {"bbox", "polygon", "transcriptions"}
    assert not telem_keys.intersection(content_fields)
