"""Slice 1 — Project skeleton & test harness."""
from sqlalchemy import text


def test_app_boots():
    from app.main import app
    assert app is not None


def test_healthcheck(client_no_auth):
    r = client_no_auth.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_db_fixture_connects(db_session):
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1
