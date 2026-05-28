import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ConsentType(str, enum.Enum):
    contribution_license = "contribution_license"
    telemetry = "telemetry"


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    consent_type: Mapped[ConsentType] = mapped_column(
        SAEnum(ConsentType, name="consenttype"), nullable=False
    )
    version: Mapped[str] = mapped_column(String, nullable=False)
    shown_text_ref: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
