from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.services.consent import has_active_contribution_consent
from app.services.users import get_or_create_user

_DEV_USER_SUB = "dev-user-001"
_DEV_USER_EMAIL = "dev@localhost"
_DEV_USER_NAME = "Dev User"


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if settings.dev_mode:
        return get_or_create_user(
            db,
            google_sub=_DEV_USER_SUB,
            email=_DEV_USER_EMAIL,
            display_name=_DEV_USER_NAME,
        )
    sub = request.headers.get("x-xhost-user-sub")
    email = request.headers.get("x-xhost-user-email")
    name = request.headers.get("x-xhost-user-name") or email
    if not sub or not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_or_create_user(
        db,
        google_sub=sub,
        email=email,
        display_name=name,
    )


def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if settings.dev_mode:
        return user
    if user.email not in settings.admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_contribution_consent(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if settings.dev_mode:
        return user
    if not has_active_contribution_consent(db, user, settings.consent_version):
        raise HTTPException(status_code=403, detail="Contribution consent required")
    return user
