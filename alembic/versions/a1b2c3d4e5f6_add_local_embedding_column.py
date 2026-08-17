"""add local embedding column for nomic-embed-code

Revision ID: a1b2c3d4e5f6
Revises: 4fafc4e7184e
Create Date: 2026-08-18 00:00:00.000000

"""

from collections.abc import Sequence

import pgvector
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "4fafc4e7184e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add local_embedding column (768 dimensions) for nomic-embed-code."""
    op.add_column(
        "chunks",
        sa.Column(
            "local_embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=768),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove local_embedding column."""
    op.drop_column("chunks", "local_embedding")
