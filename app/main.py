from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import consent, leaderboard, progress, session, transcription
from app.config import settings

app = FastAPI(title="Transcriptor")

if settings.dev_mode:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _data_dir = Path(__file__).parent.parent / "data_sample"
    if _data_dir.exists():
        app.mount("/images", StaticFiles(directory=str(_data_dir)), name="images")

app.include_router(session.router, prefix="/api")
app.include_router(transcription.router, prefix="/api")
app.include_router(consent.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
