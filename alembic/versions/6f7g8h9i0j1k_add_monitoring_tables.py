"""add monitoring tables

Revision ID: 6f7g8h9i0j1k
Revises: a1b2c3d4e5f6
Create Date: 2026-08-18 01:00:00.000000

"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f7g8h9i0j1k"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create rag_events and user_feedback tables with performance indexes."""
    # 1. Create rag_events
    op.create_table(
        "rag_events",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("retrieval_strategy", sa.String(length=50), nullable=False),
        sa.Column("prompt_strategy", sa.String(length=50), nullable=False),
        sa.Column("retrieval_latency_ms", sa.Float(), nullable=False),
        sa.Column("generation_latency_ms", sa.Float(), nullable=False),
        sa.Column("total_latency_ms", sa.Float(), nullable=False),
        sa.Column("retrieved_chunk_count", sa.Integer(), nullable=False),
        sa.Column("assembled_chunk_count", sa.Integer(), nullable=False),
        sa.Column("context_token_count", sa.Integer(), nullable=False),
        sa.Column("llm_provider", sa.String(length=50), nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("answer_length", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("repository_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )

    # Indexes for rag_events
    op.create_index(op.f("ix_rag_events_request_id"), "rag_events", ["request_id"], unique=True)
    op.create_index(op.f("ix_rag_events_created_at"), "rag_events", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_rag_events_retrieval_strategy"), "rag_events", ["retrieval_strategy"], unique=False
    )

    # 2. Create user_feedback
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"], ["rag_events.request_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for user_feedback
    op.create_index(
        op.f("ix_user_feedback_request_id"), "user_feedback", ["request_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_feedback_created_at"), "user_feedback", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Drop tables and indexes."""
    op.drop_index(op.f("ix_user_feedback_created_at"), table_name="user_feedback")
    op.drop_index(op.f("ix_user_feedback_request_id"), table_name="user_feedback")
    op.drop_table("user_feedback")

    op.drop_index(op.f("ix_rag_events_retrieval_strategy"), table_name="rag_events")
    op.drop_index(op.f("ix_rag_events_created_at"), table_name="rag_events")
    op.drop_index(op.f("ix_rag_events_request_id"), table_name="rag_events")
    op.drop_table("rag_events")
