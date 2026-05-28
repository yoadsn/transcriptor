"""Slice 4 — User resolution & consent service."""
from app.models.consent import ConsentType
from app.models.user import User
from app.services.consent import has_active_contribution_consent, record_consent
from app.services.users import get_or_create_user


def test_get_or_create_user_creates(db_session):
    user = get_or_create_user(db_session, "sub-new", "new@test.com", "New User")
    assert user.id is not None
    assert user.google_sub == "sub-new"


def test_get_or_create_user_idempotent(db_session):
    u1 = get_or_create_user(db_session, "sub-idem", "a@test.com", "A")
    u2 = get_or_create_user(db_session, "sub-idem", "a@test.com", "A")
    assert u1.id == u2.id


def test_record_consent_appends(db_session):
    user = User(google_sub="sub-consent", email="c@test.com", display_name="C")
    db_session.add(user)
    db_session.flush()

    c1 = record_consent(db_session, user, ConsentType.contribution_license, "1.0", "ref-1")
    c2 = record_consent(db_session, user, ConsentType.contribution_license, "2.0", "ref-2")
    assert c1.id != c2.id
    assert c1.version == "1.0"
    assert c2.version == "2.0"


def test_has_active_consent_false_before(db_session):
    user = User(google_sub="sub-no-consent", email="nc@test.com", display_name="NC")
    db_session.add(user)
    db_session.flush()
    assert has_active_contribution_consent(db_session, user, "1.0") is False


def test_has_active_consent_true_after(db_session):
    user = User(google_sub="sub-with-consent", email="wc@test.com", display_name="WC")
    db_session.add(user)
    db_session.flush()
    record_consent(db_session, user, ConsentType.contribution_license, "1.0", "ref")
    assert has_active_contribution_consent(db_session, user, "1.0") is True


def test_has_active_consent_false_when_version_bumped(db_session):
    user = User(google_sub="sub-old-consent", email="oc@test.com", display_name="OC")
    db_session.add(user)
    db_session.flush()
    record_consent(db_session, user, ConsentType.contribution_license, "1.0", "ref")
    # Version bumped — old consent no longer valid
    assert has_active_contribution_consent(db_session, user, "2.0") is False
