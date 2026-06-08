import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.batch import Batch
from app.models.line import Line
from app.models.page import Page
from app.models.transcription import Transcription, TranscriptionKind

router = APIRouter()

_cache: dict = {"data": None, "expires_at": 0.0}
_CACHE_TTL = 300.0  # 5 minutes


@router.get("/community")
def community_stats(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    now = time.time()
    if _cache["data"] is not None and now < _cache["expires_at"]:
        return _cache["data"]

    lines: int = db.execute(
        select(func.count(Transcription.id)).where(
            Transcription.kind == TranscriptionKind.text
        )
    ).scalar_one()

    pages: int = db.execute(
        select(func.count(func.distinct(Line.page_id)))
        .join(Transcription, Transcription.line_id == Line.id)
        .where(Transcription.kind == TranscriptionKind.text)
    ).scalar_one()

    volunteers: int = db.execute(
        select(func.count(func.distinct(Transcription.user_id))).where(
            Transcription.kind == TranscriptionKind.text
        )
    ).scalar_one()

    manuscripts: int = db.execute(
        select(func.count(func.distinct(Page.batch_id)))
        .join(Line, Line.page_id == Page.id)
        .join(Transcription, Transcription.line_id == Line.id)
        .where(Transcription.kind == TranscriptionKind.text)
    ).scalar_one()

    data = {
        "lines": lines,
        "pages": pages,
        "volunteers": volunteers,
        "manuscripts": manuscripts,
    }
    _cache.update({"data": data, "expires_at": now + _CACHE_TTL})
    return data
