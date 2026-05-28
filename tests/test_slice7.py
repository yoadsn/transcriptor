"""Slice 7 — Auth dependency & wiring."""
from app.api.deps import get_current_user
from app.db import get_db
from app.main import app
from starlette.testclient import TestClient
from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from app.models.user import User


# Register a protected dummy route for testing
_dummy_router = APIRouter()


@_dummy_router.get("/_test/protected")
def protected(user: Annotated[User, Depends(get_current_user)]) -> dict:
    return {"user_id": str(user.id)}


app.include_router(_dummy_router)


def test_protected_route_with_override(db_session, test_user):
    def override_db():
        yield db_session

    def override_user():
        return test_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        with TestClient(app) as c:
            r = c.get("/_test/protected")
        assert r.status_code == 200
        assert r.json()["user_id"] == str(test_user.id)
    finally:
        app.dependency_overrides.clear()


def test_protected_route_without_auth(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get("/_test/protected")
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_consent_gate_blocks_without_consent(client_no_consent):
    r = client_no_consent.get("/api/next-session")
    assert r.status_code == 403
    assert "consent" in r.json()["detail"].lower()
