"""Slice 8 — The HTTP API (thin endpoints over services)."""
import uuid

from app.models.transcription import TranscriptionKind
from app.models.user import User
from app.services.transcriptions import submit_response
from tests.conftest import make_batch, make_line, make_page


def _extra_user(db, sub):
    u = User(google_sub=sub, email=f"{sub}@t.com", display_name=sub)
    db.add(u)
    db.flush()
    return u


# ── next-session ──────────────────────────────────────────────────────────────

def test_next_session_with_work(client, db_session, consented_user):
    batch = make_batch(db_session, "b-api-sess")
    page = make_page(db_session, batch, "p-api-sess")
    make_line(db_session, page, line_index=0, external_id="l-api-0")

    r = client.get("/api/next-session")
    assert r.status_code == 200
    body = r.json()
    assert body["page_id"] == str(page.id)
    assert len(body["lines"]) == 1


def test_next_session_no_work_returns_204(client, db_session):
    r = client.get("/api/next-session")
    assert r.status_code == 204


def test_next_session_without_consent(client_no_consent):
    r = client_no_consent.get("/api/next-session")
    assert r.status_code == 403


# ── submit response ───────────────────────────────────────────────────────────

def test_submit_text_response(client, db_session, consented_user):
    batch = make_batch(db_session, "b-api-sub")
    page = make_page(db_session, batch, "p-api-sub")
    line = make_line(db_session, page, line_index=0, external_id="l-sub-0")

    r = client.post(f"/api/lines/{line.id}/response", json={"kind": "text", "text": "שלום"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_edit"] is False
    assert body["transcription_count"] == 1


def test_submit_flag_response(client, db_session, consented_user):
    batch = make_batch(db_session, "b-api-flag")
    page = make_page(db_session, batch, "p-api-flag")
    line = make_line(db_session, page, line_index=0, external_id="l-flag-0")

    r = client.post(f"/api/lines/{line.id}/response", json={"kind": "bad_crop"})
    assert r.status_code == 200


def test_submit_bad_kind_text_pairing(client, db_session, consented_user):
    batch = make_batch(db_session, "b-api-bad")
    page = make_page(db_session, batch, "p-api-bad")
    line = make_line(db_session, page, external_id="l-bad-0")

    r = client.post(f"/api/lines/{line.id}/response", json={"kind": "text", "text": ""})
    assert r.status_code == 422


def test_submit_without_consent(client_no_consent, db_session):
    fake_id = uuid.uuid4()
    r = client_no_consent.post(f"/api/lines/{fake_id}/response", json={"kind": "text", "text": "x"})
    assert r.status_code == 403


# ── consent endpoint ──────────────────────────────────────────────────────────

def test_post_consent(client_no_consent):
    r = client_no_consent.post("/api/consent", json={"consent_type": "contribution_license", "version": "1.0"})
    assert r.status_code == 200
    assert "consent_id" in r.json()


# ── progress ──────────────────────────────────────────────────────────────────

def test_progress_counts_text_only(client, db_session, consented_user):
    batch = make_batch(db_session, "b-prog")
    page = make_page(db_session, batch, "p-prog")
    line_text = make_line(db_session, page, line_index=0, external_id="l-prog-0")
    line_flag = make_line(db_session, page, line_index=1, external_id="l-prog-1")

    submit_response(db_session, consented_user, line_text.id, TranscriptionKind.text, "word")
    submit_response(db_session, consented_user, line_flag.id, TranscriptionKind.cant_read, None)

    r = client.get("/api/me/progress")
    assert r.status_code == 200
    assert r.json()["text_transcription_count"] == 1


# ── leaderboard ───────────────────────────────────────────────────────────────

def test_leaderboard_excludes_flags_and_hidden(client, db_session, consented_user):
    # consented_user submits text → should appear
    batch = make_batch(db_session, "b-lb")
    page = make_page(db_session, batch, "p-lb")
    l0 = make_line(db_session, page, line_index=0, external_id="l-lb-0")
    l1 = make_line(db_session, page, line_index=1, external_id="l-lb-1")
    submit_response(db_session, consented_user, l0.id, TranscriptionKind.text, "a")

    # flag-only user → should NOT appear
    flag_user = _extra_user(db_session, "u-flag-only")
    submit_response(db_session, flag_user, l1.id, TranscriptionKind.cant_read, None)

    # hidden user → should NOT appear
    hidden = _extra_user(db_session, "u-hidden")
    hidden.show_on_leaderboard = False
    db_session.flush()
    batch2 = make_batch(db_session, "b-lb2")
    page2 = make_page(db_session, batch2, "p-lb2")
    l2 = make_line(db_session, page2, line_index=0, external_id="l-lb2-0")
    submit_response(db_session, hidden, l2.id, TranscriptionKind.text, "hidden")

    r = client.get("/api/leaderboard")
    assert r.status_code == 200
    entries = r.json()
    user_ids = [e["user_id"] for e in entries]
    assert str(consented_user.id) in user_ids
    assert str(flag_user.id) not in user_ids
    assert str(hidden.id) not in user_ids
