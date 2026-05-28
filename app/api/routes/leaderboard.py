from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.leaderboard import get_leaderboard

router = APIRouter()


@router.get("/leaderboard")
def leaderboard(db: Annotated[Session, Depends(get_db)]) -> list:
    return get_leaderboard(db, ttl=0)  # ttl=0 disables cache; enable in production
