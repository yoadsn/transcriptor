from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.line import Line
from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User

router = APIRouter()

_DAILY_GOAL = 150  # placeholder until per-user goals are stored


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


@router.get("/me/profile")
def my_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    base = select(func.count(Transcription.id)).where(
        Transcription.user_id == user.id,
        Transcription.kind == TranscriptionKind.text,
    )

    total: int = db.execute(base).scalar_one()
    today: int = db.execute(base.where(Transcription.created_at >= today_start)).scalar_one()
    week: int = db.execute(base.where(Transcription.created_at >= week_start)).scalar_one()

    pages: int = db.execute(
        select(func.count(func.distinct(Line.page_id)))
        .join(Transcription, Transcription.line_id == Line.id)
        .where(
            Transcription.user_id == user.id,
            Transcription.kind == TranscriptionKind.text,
        )
    ).scalar_one()

    return {
        "name": user.display_name,
        "today": today,
        "goal": _DAILY_GOAL,
        "streak": 0,  # streak tracking not yet implemented
        "week": week,
        "total": total,
        "pages": pages,
    }
