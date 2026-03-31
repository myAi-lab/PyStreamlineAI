import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin
from app.models.base import Base
from app.models.enums import ResumeParseStatus, ResumeSourceType


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[ResumeSourceType] = mapped_column(
        Enum(
            ResumeSourceType,
            name="resume_source_type",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parse_status: Mapped[ResumeParseStatus] = mapped_column(
        Enum(
            ResumeParseStatus,
            name="resume_parse_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=ResumeParseStatus.PENDING,
    )

    user = relationship("User", back_populates="resumes")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
