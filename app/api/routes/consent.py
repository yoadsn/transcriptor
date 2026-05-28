from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.consent import ConsentType
from app.models.user import User
from app.services.consent import record_consent

router = APIRouter()


class ConsentBody(BaseModel):
    consent_type: ConsentType
    version: str
    shown_text_ref: str = "default"


@router.post("/consent")
def post_consent(
    body: ConsentBody,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    consent = record_consent(db, user, body.consent_type, body.version, body.shown_text_ref)
    return {"consent_id": str(consent.id)}
