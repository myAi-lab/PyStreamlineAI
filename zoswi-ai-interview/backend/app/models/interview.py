import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class InterviewStatus(StrEnum):
    in_progress = "in_progress"
    completed = "completed"


class TranscriptSpeaker(StrEnum):
    ai = "ai"
    candidate = "candidate"
    system = "system"


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(32), default="mixed", nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, name="interview_status"),
        default=InterviewStatus.in_progress,
        nullable=False,
    )
    current_question: Mapped[str] = mapped_column(Text, default="", nullable=False)
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_turns: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    transcript_history: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    evaluation_signals: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    transcripts: Mapped[list["ConversationTranscript"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    ai_questions: Mapped[list["AIQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    candidate_responses: Mapped[list["CandidateResponse"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    evaluation_summary: Mapped["EvaluationSummary | None"] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ConversationTranscript(Base):
    __tablename__ = "conversation_transcripts"
    __table_args__ = (UniqueConstraint("session_id", "sequence_no", name="uq_transcript_sequence"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    speaker: Mapped[TranscriptSpeaker] = mapped_column(
        Enum(TranscriptSpeaker, name="transcript_speaker"),
        nullable=False,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="transcripts")


class AIQuestion(Base):
    __tablename__ = "ai_questions"
    __table_args__ = (UniqueConstraint("session_id", "question_order", name="uq_ai_question_order"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="ai_questions")
    candidate_responses: Mapped[list["CandidateResponse"]] = relationship(back_populates="question")


class CandidateResponse(Base):
    __tablename__ = "candidate_responses"
    __table_args__ = (UniqueConstraint("session_id", "response_order", name="uq_candidate_response_order"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    response_order: Mapped[int] = mapped_column(Integer, nullable=False)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="candidate_responses")
    question: Mapped["AIQuestion | None"] = relationship(back_populates="candidate_responses")


class EvaluationSummary(Base):
    __tablename__ = "evaluation_summary"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    technical_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    communication_clarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    signals_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="evaluation_summary")
