"""Export events table as JSONL (internal telemetry dump).

Usage:
    uv run python scripts/export_telemetry.py [output.jsonl]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.event import Event


def export_telemetry(session: Session) -> list[dict]:
    events = session.execute(select(Event)).scalars().all()
    return [
        {
            "id": str(e.id),
            "user_id": str(e.user_id),
            "line_id": str(e.line_id) if e.line_id else None,
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


def main() -> None:
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    with SessionLocal() as session:
        records = export_telemetry(session)
    output = "\n".join(json.dumps(r) for r in records)
    if output_path:
        Path(output_path).write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
