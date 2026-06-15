"""ensure source_metadata and document_name columns exist (idempotent repair)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE batches ADD COLUMN IF NOT EXISTS source_metadata JSONB"
    )
    op.execute(
        "ALTER TABLE pages ADD COLUMN IF NOT EXISTS document_name VARCHAR"
    )
    op.execute(
        "UPDATE pages SET document_name = split_part(external_id, ':', 1) WHERE document_name IS NULL"
    )
    op.execute(
        "ALTER TABLE pages ALTER COLUMN document_name SET NOT NULL"
    )


def downgrade() -> None:
    pass
