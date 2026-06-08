from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.batch import Batch
from app.models.line import Line
from app.models.page import Page
from app.models.transcription import Transcription, TranscriptionKind
from app.models.user import User

router = APIRouter()

_COMPLETION_TARGET = 3


@router.get("/stats")
def admin_stats(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    total_users: int = db.execute(select(func.count(User.id))).scalar_one()

    active_today: int = db.execute(
        select(func.count(func.distinct(Transcription.user_id))).where(
            Transcription.updated_at >= today_start
        )
    ).scalar_one()

    active_week: int = db.execute(
        select(func.count(func.distinct(Transcription.user_id))).where(
            Transcription.updated_at >= week_start
        )
    ).scalar_one()

    total_transcriptions: int = db.execute(
        select(func.count(Transcription.id))
    ).scalar_one()

    text_transcriptions: int = db.execute(
        select(func.count(Transcription.id)).where(
            Transcription.kind == TranscriptionKind.text
        )
    ).scalar_one()

    total_lines: int = db.execute(select(func.count(Line.id))).scalar_one()
    complete_lines: int = db.execute(
        select(func.count(Line.id)).where(Line.transcription_count >= _COMPLETION_TARGET)
    ).scalar_one()

    completion_pct = round(100.0 * complete_lines / total_lines, 1) if total_lines else 0.0

    return {
        "total_users": total_users,
        "active_today": active_today,
        "active_this_week": active_week,
        "total_transcriptions": total_transcriptions,
        "text_transcriptions": text_transcriptions,
        "overall_completion_pct": completion_pct,
    }


@router.get("/users")
def admin_users(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    rows = db.execute(
        select(
            User.id,
            User.display_name,
            User.email,
            User.created_at,
            func.max(Transcription.updated_at).label("last_active"),
            func.count(Transcription.id).label("total_submissions"),
            func.count(
                case((Transcription.kind == TranscriptionKind.text, Transcription.id))
            ).label("text_count"),
            func.count(
                case((Transcription.kind == TranscriptionKind.cant_read, Transcription.id))
            ).label("cant_read_count"),
            func.count(
                case((
                    Transcription.kind.in_([
                        TranscriptionKind.bad_crop,
                        TranscriptionKind.not_hebrew,
                        TranscriptionKind.not_text,
                    ]),
                    Transcription.id,
                ))
            ).label("flag_count"),
        )
        .outerjoin(Transcription, Transcription.user_id == User.id)
        .group_by(User.id, User.display_name, User.email, User.created_at)
        .order_by(func.count(
            case((Transcription.kind == TranscriptionKind.text, Transcription.id))
        ).desc())
    ).mappings().all()

    return [
        {
            "user_id": str(r["id"]),
            "display_name": r["display_name"],
            "email": r["email"],
            "joined_at": r["created_at"].isoformat() if r["created_at"] else None,
            "last_active": r["last_active"].isoformat() if r["last_active"] else None,
            "total_submissions": r["total_submissions"],
            "text_count": r["text_count"],
            "cant_read_count": r["cant_read_count"],
            "flag_count": r["flag_count"],
        }
        for r in rows
    ]


@router.get("/coverage")
def admin_coverage(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    rows = db.execute(
        select(
            Batch.id,
            Batch.external_id,
            Batch.source,
            func.count(func.distinct(Page.id)).label("total_pages"),
            func.count(Line.id).label("total_lines"),
            func.count(
                case((Line.transcription_count > 0, Line.id))
            ).label("lines_with_any"),
            func.count(
                case((Line.transcription_count >= _COMPLETION_TARGET, Line.id))
            ).label("lines_complete"),
        )
        .join(Page, Page.batch_id == Batch.id)
        .join(Line, Line.page_id == Page.id)
        .group_by(Batch.id, Batch.external_id, Batch.source)
        .order_by(Batch.external_id)
    ).mappings().all()

    return [
        {
            "batch_id": str(r["id"]),
            "external_id": r["external_id"],
            "source": r["source"],
            "total_pages": r["total_pages"],
            "total_lines": r["total_lines"],
            "lines_with_any": r["lines_with_any"],
            "lines_complete": r["lines_complete"],
            "completion_pct": round(
                100.0 * r["lines_complete"] / r["total_lines"], 1
            ) if r["total_lines"] else 0.0,
        }
        for r in rows
    ]


@router.get("/queue")
def admin_queue(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    line_stats = db.execute(
        select(
            func.count(Line.id).label("total"),
            func.count(case((Line.transcription_count == 0, Line.id))).label("untouched"),
            func.count(case((
                (Line.transcription_count > 0) & (Line.transcription_count < _COMPLETION_TARGET),
                Line.id,
            ))).label("in_progress"),
            func.count(
                case((Line.transcription_count >= _COMPLETION_TARGET, Line.id))
            ).label("complete"),
        )
    ).mappings().one()

    pages_complete: int = db.execute(
        select(func.count(Page.id)).where(
            ~select(Line.id)
            .where(
                Line.page_id == Page.id,
                Line.transcription_count < _COMPLETION_TARGET,
            )
            .exists()
        )
    ).scalar_one()

    batches_complete: int = db.execute(
        select(func.count(Batch.id)).where(
            ~select(Page.id)
            .join(Line, Line.page_id == Page.id)
            .where(
                Page.batch_id == Batch.id,
                Line.transcription_count < _COMPLETION_TARGET,
            )
            .exists()
        )
    ).scalar_one()

    return {
        "total_lines": line_stats["total"],
        "lines_untouched": line_stats["untouched"],
        "lines_in_progress": line_stats["in_progress"],
        "lines_complete": line_stats["complete"],
        "pages_complete": pages_complete,
        "batches_complete": batches_complete,
    }
