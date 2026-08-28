"""add answer column to rag_events

Revision ID: 7g8h9i0j1k2l
Revises: 6f7g8h9i0j1k
Create Date: 2026-08-28 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7g8h9i0j1k2l"
down_revision: str | Sequence[str] | None = "6f7g8h9i0j1k"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rag_events", sa.Column("answer", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rag_events", "answer")
