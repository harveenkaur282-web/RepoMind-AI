from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.document import Document


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(Text)

    chunk_index: Mapped[int] = mapped_column(Integer, index=True)

    start_char: Mapped[int] = mapped_column(Integer, default=0)

    end_char: Mapped[int] = mapped_column(Integer, default=0)

    strategy: Mapped[str] = mapped_column(String(100), nullable=False)

    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )

    openai_embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(1536),
        nullable=True,
    )

    voyage_embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(1024),
        nullable=True,
    )
