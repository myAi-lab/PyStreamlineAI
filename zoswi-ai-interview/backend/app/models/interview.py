import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin
from app.models.base import Base
from app.models.enums import InterviewMode, InterviewStatus


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_target: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(
            InterviewStatus,
            name="interview_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=InterviewStatus.CREATED,
    )
    session_mode: Mapped[InterviewMode] = mapped_column(
        Enum(
            InterviewMode,
            name="interview_mode",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=InterviewMode.MIXED,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    turns = relationship(
        "InterviewTurn",
        back_populates="session",
        order_by="InterviewTurn.turn_index",
        cascade="all, delete-orphan",
    )
    summary = relationship(
        "InterviewSummary",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_index", name="uq_session_turn_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    interviewer_message: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    score_overall: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_communication: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_technical: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    session = relationship("InterviewSession", back_populates="turns")


class InterviewSummary(Base):
    __tablename__ = "interview_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    improvement_areas: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    session = relationship("InterviewSession", back_populates="summary")
