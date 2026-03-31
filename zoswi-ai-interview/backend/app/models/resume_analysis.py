import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    extracted_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    suggestions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    analysis_version: Mapped[str] = mapped_column(String(30), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    resume = relationship("Resume", back_populates="analyses")

