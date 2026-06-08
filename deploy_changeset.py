#!/usr/bin/env python3
"""Deploy changeset to xhost."""
import json
import urllib.request
import urllib.error
import ssl

XHOST_TOKEN = "xh_d2zP4gObQpdT0UY0IaC98HoCzS9axSDCiCLjtAXpZiZ"
APP_ID = "0b7fc7d5-64f5-4fd4-b87e-c19702bcfb27"
CHANNEL_ID = "4e0f9aa8-72c2-4753-9891-3c1c67bbe328"
API_BASE = "https://api.xhostd.com"

BASE = "C:/Users/Yanir/Dropbox/Projects/transcriptor"


def read(path):
    with open(f"{BASE}/{path}", "r", encoding="utf-8") as f:
        return f.read()


def post(url, payload):
    ctx = ssl.create_default_context()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {XHOST_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


# ── merged app/main.py (includes auth, community, frontend serving) ──
MAIN_PY = '''from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, community, consent, leaderboard, progress, session, transcription
from app.config import settings

app = FastAPI(title="Transcriptor")

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

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

app.include_router(auth.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(transcription.router, prefix="/api")
app.include_router(consent.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
'''

changes = {
    # Backend
    "app/main.py": MAIN_PY,
    "app/api/routes/community.py": read("app/api/routes/community.py"),
    "app/api/routes/progress.py": read("app/api/routes/progress.py"),
    # Frontend dist - updated
    "frontend/dist/index.html": read("frontend/dist/index.html"),
    "frontend/dist/assets/index-DA3FrC_K.js": read("frontend/dist/assets/index-DA3FrC_K.js"),
    "frontend/dist/assets/index-n7V6efoB.css": read("frontend/dist/assets/index-n7V6efoB.css"),
    # Delete old bundles
    "frontend/dist/assets/index-D5fHRAy5.js": None,
    "frontend/dist/assets/index-BTg3WXxF.js": None,
    "frontend/dist/assets/index-DavyPLeL.js": None,
}

print(f"Uploading changeset with {len(changes)} file changes...")
for k, v in changes.items():
    sz = len(v) if v else 0
    print(f"  {'DEL' if v is None else 'UPD'} {k} ({sz} bytes)")

result = post(
    f"{API_BASE}/apps/{APP_ID}/changeset",
    {"message": "Replace תמלל/מתמלל with תעתיק/תעתוק, fix BrandMark logo letter", "changes": changes},
)
print(f"\nChangeset SHA: {result}")

sha = result.get("sha") or result.get("id") or (result if isinstance(result, str) else None)
if not sha:
    print("ERROR: could not extract SHA from result")
    import sys; sys.exit(1)

print(f"\nDeploying SHA {sha} to channel {CHANNEL_ID}...")
deploy_result = post(
    f"{API_BASE}/apps/{APP_ID}/channels/{CHANNEL_ID}/deploy",
    {"sha": sha},
)
print(f"Deploy result: {deploy_result}")
