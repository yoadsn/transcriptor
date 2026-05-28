"""Slice 2 — Schema & migrations (the six tables)."""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from app.db import Base
from app.models.batch import Batch
from app.models.consent import Consent, ConsentType
from app.models.line import Line
from app.models.page import Page
from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User
from tests.conftest import make_batch, make_line, make_page


def test_models_create_all(test_engine):
    # create_all is idempotent; if it runs without exception, tables exist
    Base.metadata.create_all(test_engine)


def test_transcription_unique_line_user(db_session):
    batch = make_batch(db_session)
    page = make_page(db_session, batch)
    line = make_line(db_session, page)
    user = User(google_sub="sub-dup", email="dup@test.com", display_name="Dup")
    db_session.add(user)
    db_session.flush()

    t1 = Transcription(line_id=line.id, user_id=user.id, kind=TranscriptionKind.cant_read)
    db_session.add(t1)
    db_session.flush()

    t2 = Transcription(line_id=line.id, user_id=user.id, kind=TranscriptionKind.cant_read)
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_page_unique_batch_external_id(db_session):
    batch = make_batch(db_session, external_id="b-uniq")
    p1 = Page(batch_id=batch.id, external_id="same", image_path="a.jpg", width_px=1, height_px=1)
    p2 = Page(batch_id=batch.id, external_id="same", image_path="b.jpg", width_px=1, height_px=1)
    db_session.add_all([p1, p2])
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_line_unique_page_external_id(db_session):
    batch = make_batch(db_session, external_id="b-line-uniq")
    page = make_page(db_session, batch, external_id="p-uniq")
    l1 = Line(page_id=page.id, line_index=0, bbox={"x": 0, "y": 0, "w": 1, "h": 1}, external_id="same")
    l2 = Line(page_id=page.id, line_index=1, bbox={"x": 0, "y": 0, "w": 1, "h": 1}, external_id="same")
    db_session.add_all([l1, l2])
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_alembic_migration_roundtrips(test_engine):
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_engine.url.render_as_string(hide_password=False))

    from sqlalchemy import text

    def drop_all_clean(engine):
        Base.metadata.drop_all(engine)
        with engine.begin() as conn:
            conn.execute(text("DROP TYPE IF EXISTS transcriptionkind"))
            conn.execute(text("DROP TYPE IF EXISTS consenttype"))

    drop_all_clean(test_engine)
    try:
        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "base")
    finally:
        # Always restore so subsequent tests can run
        drop_all_clean(test_engine)
        Base.metadata.create_all(test_engine)
