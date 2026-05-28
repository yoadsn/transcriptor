from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User

router = APIRouter()


@router.get("/me/progress")
def my_progress(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    count = db.execute(
        select(func.count(Transcription.id)).where(
            Transcription.user_id == user.id,
            Transcription.kind == TranscriptionKind.text,
        )
    ).scalar_one()
    return {"text_transcription_count": count}
