import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
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


class UserInterviewQuota(Base):
    __tablename__ = "user_interview_quotas"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    total_chances: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
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
    owner_user_id: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)
    org_id: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)
    candidate_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), default="", nullable=False)
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
    interview_plan: Mapped["InterviewPlan | None"] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    interview_turns: Mapped[list["InterviewTurn"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    integrity_events: Mapped[list["IntegrityEvent"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    final_assessment: Mapped["FinalAssessment | None"] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recruiter_reviews: Mapped[list["RecruiterReview"]] = relationship(
        back_populates="session",
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


class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_no", name="uq_interview_turn_no"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    turn_no: Mapped[int] = mapped_column(Integer, nullable=False)
    competency_key: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    candidate_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    answer_quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stt_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="interview_turns")
    turn_score: Mapped["TurnScore | None"] = relationship(back_populates="turn", uselist=False, cascade="all, delete-orphan")


class TurnScore(Base):
    __tablename__ = "turn_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_turns.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    technical_correctness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    problem_solving_debugging: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    architecture_design: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    communication_clarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tradeoff_reasoning: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    professional_integrity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    coverage_update: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    turn: Mapped["InterviewTurn"] = relationship(back_populates="turn_score")


class IntegrityEvent(Base):
    __tablename__ = "integrity_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_turns.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="integrity_events")


class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain: Mapped[str] = mapped_column(String(100), default="", nullable=False, index=True)
    competency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RoleCompetency(Base):
    __tablename__ = "role_competencies"
    __table_args__ = (UniqueConstraint("role_name", "competency_id", name="uq_role_competency"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="SET NULL"),
        nullable=True,
    )
    domain: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    role_hint: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(80), default="mixed", nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewPlan(Base):
    __tablename__ = "interview_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    detected_domain: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    coverage_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="interview_plan")
    items: Mapped[list["InterviewPlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class InterviewPlanItem(Base):
    __tablename__ = "interview_plan_items"
    __table_args__ = (UniqueConstraint("plan_id", "competency_key", name="uq_plan_competency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="SET NULL"),
        nullable=True,
    )
    competency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_turns: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    covered_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    plan: Mapped["InterviewPlan"] = relationship(back_populates="items")


class FinalAssessment(Base):
    __tablename__ = "final_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competency_coverage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), default="No Hire", nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="final_assessment")


class RecruiterReview(Base):
    __tablename__ = "recruiter_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    override_recommendation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="recruiter_reviews")
