"""Slice 5 — Submit a transcription (the write path)."""
import pytest
from sqlalchemy import func, select

from app.models.event import Event
from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User
from app.services.transcriptions import submit_response
from tests.conftest import make_batch, make_line, make_page


def _user(db, sub):
    u = User(google_sub=sub, email=f"{sub}@test.com", display_name=sub)
    db.add(u)
    db.flush()
    return u


def _setup(db):
    batch = make_batch(db)
    page = make_page(db, batch)
    line = make_line(db, page)
    user = _user(db, "u-submit-1")
    return line, user


def test_first_submit_inserts_and_bumps_count(db_session):
    line, user = _setup(db_session)
    result = submit_response(db_session, user, line.id, TranscriptionKind.text, "שלום")
    assert result.is_edit is False
    assert result.transcription_count == 1
    db_session.flush()
    assert line.transcription_count == 1


def test_edit_does_not_change_count(db_session):
    line, user = _setup(db_session)
    submit_response(db_session, user, line.id, TranscriptionKind.text, "first")
    result = submit_response(db_session, user, line.id, TranscriptionKind.text, "second")
    assert result.is_edit is True
    assert result.transcription_count == 1
    # Only one row exists
    count = db_session.execute(
        select(func.count(Transcription.id)).where(
            Transcription.line_id == line.id,
            Transcription.user_id == user.id,
        )
    ).scalar_one()
    assert count == 1


def test_three_distinct_users_count_three(db_session):
    batch = make_batch(db_session, "b-3u")
    page = make_page(db_session, batch, "p-3u")
    line = make_line(db_session, page)
    for i in range(3):
        u = _user(db_session, f"u3-{i}")
        submit_response(db_session, u, line.id, TranscriptionKind.text, f"text{i}")
    assert line.transcription_count == 3


def test_fourth_user_accepted_count_four(db_session):
    batch = make_batch(db_session, "b-4u")
    page = make_page(db_session, batch, "p-4u")
    line = make_line(db_session, page)
    for i in range(4):
        u = _user(db_session, f"u4-{i}")
        submit_response(db_session, u, line.id, TranscriptionKind.text, f"text{i}")
    assert line.transcription_count == 4


def test_kind_text_requires_text(db_session):
    line, user = _setup(db_session)
    with pytest.raises(ValueError, match="non-empty"):
        submit_response(db_session, user, line.id, TranscriptionKind.text, "")


def test_kind_text_requires_nonempty_text(db_session):
    line, user = _setup(db_session)
    with pytest.raises(ValueError, match="non-empty"):
        submit_response(db_session, user, line.id, TranscriptionKind.text, None)


def test_flag_kind_must_have_no_text(db_session):
    line, user = _setup(db_session)
    with pytest.raises(ValueError, match="must have no text"):
        submit_response(db_session, user, line.id, TranscriptionKind.bad_crop, "some text")


def test_counter_equals_distinct_user_count(db_session):
    batch = make_batch(db_session, "b-inv")
    page = make_page(db_session, batch, "p-inv")
    line = make_line(db_session, page)

    users = [_user(db_session, f"u-inv-{i}") for i in range(3)]
    for u in users:
        submit_response(db_session, u, line.id, TranscriptionKind.text, "x")
    # Edit one
    submit_response(db_session, users[0], line.id, TranscriptionKind.cant_read, None)

    db_count = db_session.execute(
        select(func.count(Transcription.id)).where(Transcription.line_id == line.id)
    ).scalar_one()
    assert line.transcription_count == db_count


def test_events_written_per_submit_and_edit(db_session):
    line, user = _setup(db_session)
    submit_response(db_session, user, line.id, TranscriptionKind.text, "first")
    submit_response(db_session, user, line.id, TranscriptionKind.text, "second")

    events = db_session.execute(
        select(Event).where(Event.line_id == line.id, Event.user_id == user.id)
    ).scalars().all()
    types = [e.event_type for e in events]
    assert "submitted" in types
    assert "edited" in types
