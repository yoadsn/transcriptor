"""Slice 6 — Dispatch a session (the read path)."""
from unittest.mock import patch

from app.models.transcription import TranscriptionKind
from app.models.user import User
from app.services.dispatch import get_next_session
from app.services.transcriptions import submit_response
from tests.conftest import make_batch, make_line, make_page


def _user(db, sub):
    u = User(google_sub=sub, email=f"{sub}@test.com", display_name=sub)
    db.add(u)
    db.flush()
    return u


def test_fresh_page_all_eligible(db_session):
    batch = make_batch(db_session, "b-fresh")
    page = make_page(db_session, batch, "p-fresh")
    for i in range(3):
        make_line(db_session, page, line_index=i)
    user = _user(db_session, "u-fresh")

    dto = get_next_session(db_session, user)
    assert dto is not None
    assert all(l.status == "eligible" for l in dto.lines)
    assert [l.line_index for l in dto.lines] == [0, 1, 2]


def test_done_line_is_done_by_you(db_session):
    batch = make_batch(db_session, "b-done")
    page = make_page(db_session, batch, "p-done")
    l0 = make_line(db_session, page, line_index=0)
    make_line(db_session, page, line_index=1)
    user = _user(db_session, "u-done")

    submit_response(db_session, user, l0.id, TranscriptionKind.text, "transcribed")
    dto = get_next_session(db_session, user)
    assert dto is not None
    statuses = {l.line_index: l.status for l in dto.lines}
    assert statuses[0] == "done_by_you"
    assert statuses[1] == "eligible"
    done_line = next(l for l in dto.lines if l.line_index == 0)
    assert done_line.prior_text == "transcribed"


def test_full_line_appears_for_context(db_session):
    batch = make_batch(db_session, "b-full")
    page = make_page(db_session, batch, "p-full")
    full_line = make_line(db_session, page, line_index=0)
    make_line(db_session, page, line_index=1)

    # Fill line 0 with 3 other users
    for i in range(3):
        u = _user(db_session, f"u-full-filler-{i}")
        submit_response(db_session, u, full_line.id, TranscriptionKind.text, "t")

    user = _user(db_session, "u-full-viewer")
    dto = get_next_session(db_session, user)
    assert dto is not None
    statuses = {l.line_index: l.status for l in dto.lines}
    assert statuses[0] == "full"
    assert statuses[1] == "eligible"


def test_fully_done_page_not_chosen(db_session):
    batch = make_batch(db_session, "b-all-done")
    page = make_page(db_session, batch, "p-all-done")
    line = make_line(db_session, page, line_index=0)
    user = _user(db_session, "u-all-done")

    submit_response(db_session, user, line.id, TranscriptionKind.text, "done")
    dto = get_next_session(db_session, user)
    assert dto is None


def test_image_url_from_resolver(db_session):
    batch = make_batch(db_session, "b-url")
    page = make_page(db_session, batch, "p-url", image_path="foo/bar.jpg")
    make_line(db_session, page, line_index=0)
    user = _user(db_session, "u-url")

    with patch("app.services.dispatch.resolve_image_url", return_value="https://cdn/foo/bar.jpg") as mock_resolver:
        dto = get_next_session(db_session, user)
        mock_resolver.assert_called_once_with("foo/bar.jpg")
    assert dto.image_url == "https://cdn/foo/bar.jpg"


def test_prefers_more_eligible_page(db_session):
    batch = make_batch(db_session, "b-pref")
    # page A: 1 eligible line; page B: 3 eligible lines
    page_a = make_page(db_session, batch, "p-pref-a")
    page_b = make_page(db_session, batch, "p-pref-b")
    make_line(db_session, page_a, line_index=0, external_id="a-0")
    for i in range(3):
        make_line(db_session, page_b, line_index=i, external_id=f"b-{i}")
    user = _user(db_session, "u-pref")

    dto = get_next_session(db_session, user)
    assert dto is not None
    assert dto.page_id == page_b.id
