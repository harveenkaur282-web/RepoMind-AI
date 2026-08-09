from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.document import Document


class RepositoryStatus(StrEnum):
    PENDING = "pending"
    INGESTING = "ingesting"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)

    github_url: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
    )

    owner: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    default_branch: Mapped[str] = mapped_column(
        String(255),
        default="main",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[RepositoryStatus] = mapped_column(
        String(50),
        default=RepositoryStatus.PENDING,
        index=True,
    )

    last_ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )