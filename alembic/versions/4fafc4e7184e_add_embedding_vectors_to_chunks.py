"""add embedding vectors to chunks

Revision ID: 4fafc4e7184e
Revises: ef522bc0394f
Create Date: 2026-08-16 22:57:46.252033

"""

from collections.abc import Sequence

import pgvector
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fafc4e7184e"
down_revision: str | Sequence[str] | None = "ef522bc0394f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "chunks",
        sa.Column(
            "openai_embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=1536),
            nullable=True,
        ),
    )
    op.add_column(
        "chunks",
        sa.Column(
            "voyage_embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=1024),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chunks", "voyage_embedding")
    op.drop_column("chunks", "openai_embedding")
