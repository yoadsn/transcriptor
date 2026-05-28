"""Slice 11 — End-to-end smoke test."""
from sqlalchemy import select

from app.models.line import Line
from app.models.transcription import TranscriptionKind
from app.models.user import User
from app.services.consent import record_consent
from app.models.consent import ConsentType
from app.services.dispatch import get_next_session
from app.services.transcriptions import submit_response
from scripts.export_dataset import export_dataset
from scripts.import_batch import _parse_surya_page, import_batch

SURYA_BATCH = {
    "pages": [
        {
            "page_id": "smoke-page-1",
            "image_path": "smoke.jpg",
            "width": 800,
            "height": 1200,
            "text_lines": [
                {"bbox": {"x": 0, "y": i * 30, "w": 400, "h": 28}, "confidence": 0.9}
                for i in range(4)
            ],
        }
    ]
}


def _make_user(db, sub):
    u = User(google_sub=sub, email=f"{sub}@smoke.com", display_name=sub)
    db.add(u)
    db.flush()
    record_consent(db, u, ConsentType.contribution_license, "1.0", "ref")
    return u


def test_full_lifecycle_smoke(db_session):
    # 1. Import batch
    pages_data = [_parse_surya_page(p) for p in SURYA_BATCH["pages"]]
    import_batch(db_session, "smoke-batch", "ivrit.ai", "cc-by-4.0", pages_data)

    lines = db_session.execute(select(Line).order_by(Line.line_index)).scalars().all()
    assert len(lines) == 4

    # 2. Three users consent + work through the page
    users = [_make_user(db_session, f"smoke-user-{i}") for i in range(3)]

    # User 0: text some, flag one, edit one
    session0 = get_next_session(db_session, users[0])
    assert session0 is not None
    submit_response(db_session, users[0], lines[0].id, TranscriptionKind.text, "line zero")
    submit_response(db_session, users[0], lines[1].id, TranscriptionKind.bad_crop, None)
    submit_response(db_session, users[0], lines[2].id, TranscriptionKind.text, "line two v1")
    submit_response(db_session, users[0], lines[2].id, TranscriptionKind.text, "line two v2")  # edit

    # Users 1 and 2: complete lines 0, 1, 2 (reaching count 3)
    for u in users[1:]:
        for line in lines[:3]:
            submit_response(db_session, u, line.id, TranscriptionKind.text, f"text by {u.google_sub}")

    # 3. Lines 0-2 should have count >= 3 and drop out of new sessions for these users
    for line in lines[:3]:
        assert line.transcription_count >= 3

    # 4. A fresh 4th user gets only line 3 (lines 0-2 are full)
    user3 = _make_user(db_session, "smoke-user-3")
    session3 = get_next_session(db_session, user3)
    assert session3 is not None
    eligible = [l for l in session3.lines if l.status == "eligible"]
    assert all(l.line_index == 3 for l in eligible)

    # 5. Export and verify all transcriptions in output
    records = export_dataset(db_session)
    assert len(records) == 4

    line0_record = next(r for r in records if r["line_id"] == str(lines[0].id))
    assert len(line0_record["transcriptions"]) >= 3
    assert line0_record["batch"]["source"] == "ivrit.ai"
    assert line0_record["batch"]["license"] == "cc-by-4.0"

    # User 0's edit is stored as single row with final text
    user0_t = next(
        t for t in line0_record["transcriptions"]
        if t["user_id"] == str(users[0].id)
    )
    assert user0_t["text"] == "line zero"

    # line 2: user 0's edit should reflect final value
    line2_record = next(r for r in records if r["line_id"] == str(lines[2].id))
    user0_line2 = next(
        t for t in line2_record["transcriptions"]
        if t["user_id"] == str(users[0].id)
    )
    assert user0_line2["text"] == "line two v2"
