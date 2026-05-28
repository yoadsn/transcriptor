import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User

_cache: dict = {"data": None, "expires_at": 0.0}
CACHE_TTL = 60.0


def get_leaderboard(session: Session, ttl: float = CACHE_TTL) -> list[dict]:
    now = time.time()
    if ttl > 0 and _cache["data"] is not None and now < _cache["expires_at"]:
        return _cache["data"]
    data = _query_leaderboard(session)
    if ttl > 0:
        _cache.update({"data": data, "expires_at": now + ttl})
    return data


def _query_leaderboard(session: Session) -> list[dict]:
    rows = session.execute(
        select(User.id, User.display_name, func.count(Transcription.id).label("count"))
        .join(Transcription, Transcription.user_id == User.id)
        .where(
            Transcription.kind == TranscriptionKind.text,
            User.show_on_leaderboard == True,
        )
        .group_by(User.id, User.display_name)
        .order_by(func.count(Transcription.id).desc())
        .limit(100)
    ).all()
    return [{"user_id": str(r.id), "display_name": r.display_name, "count": r.count} for r in rows]


def clear_cache() -> None:
    _cache.update({"data": None, "expires_at": 0.0})
