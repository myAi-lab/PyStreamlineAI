"""Add scalable interview platform tables.

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260318_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspector().get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(str(column.get("name")) == column_name for column in _inspector().get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(str(index.get("name")) == index_name for index in _inspector().get_indexes(table_name))


def _column_type(table_name: str, column_name: str):
    if not _table_exists(table_name):
        return None
    for column in _inspector().get_columns(table_name):
        if str(column.get("name")) == column_name:
            return column.get("type")
    return None


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = str(bind.dialect.name).lower() in {"postgresql", "postgres"}

    if is_postgres:
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interview_status') THEN
                        CREATE TYPE interview_status AS ENUM ('in_progress', 'completed');
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transcript_speaker') THEN
                        CREATE TYPE transcript_speaker AS ENUM ('ai', 'candidate', 'system');
                    END IF;
                END $$;
                """
            )
        )

    status_type = (
        postgresql.ENUM("in_progress", "completed", name="interview_status", create_type=False)
        if is_postgres
        else sa.String(length=32)
    )
    speaker_type = (
        postgresql.ENUM("ai", "candidate", "system", name="transcript_speaker", create_type=False)
        if is_postgres
        else sa.String(length=32)
    )
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    json_empty_array_default = sa.text("'[]'::jsonb") if is_postgres else sa.text("'[]'")
    json_empty_object_default = sa.text("'{}'::jsonb") if is_postgres else sa.text("'{}'")
    status_default = sa.text("'in_progress'::interview_status") if is_postgres else sa.text("'in_progress'")
    uuid_type = sa.Uuid()

    if not _table_exists("app_settings"):
        op.create_table(
            "app_settings",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("setting_key", sa.String(length=255), nullable=False),
            sa.Column("setting_value", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("setting_key"),
        )
        _create_index_if_missing("ix_app_settings_setting_key", "app_settings", ["setting_key"])

    if not _table_exists("interview_sessions"):
        op.create_table(
            "interview_sessions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("owner_user_id", sa.String(length=128), server_default="", nullable=False),
            sa.Column("org_id", sa.String(length=128), server_default="", nullable=False),
            sa.Column("candidate_name", sa.String(length=200), nullable=False),
            sa.Column("role", sa.String(length=200), nullable=False),
            sa.Column("domain", sa.String(length=64), server_default="", nullable=False),
            sa.Column("interview_type", sa.String(length=32), server_default="mixed", nullable=False),
            sa.Column("status", status_type, server_default=status_default, nullable=False),
            sa.Column("current_question", sa.Text(), server_default="", nullable=False),
            sa.Column("turn_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("max_turns", sa.Integer(), server_default="5", nullable=False),
            sa.Column("transcript_history", json_type, server_default=json_empty_array_default, nullable=False),
            sa.Column("evaluation_signals", json_type, server_default=json_empty_object_default, nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        if not _column_exists("interview_sessions", "owner_user_id"):
            op.add_column(
                "interview_sessions",
                sa.Column("owner_user_id", sa.String(length=128), server_default="", nullable=False),
            )
        if not _column_exists("interview_sessions", "org_id"):
            op.add_column("interview_sessions", sa.Column("org_id", sa.String(length=128), server_default="", nullable=False))
        if not _column_exists("interview_sessions", "domain"):
            op.add_column("interview_sessions", sa.Column("domain", sa.String(length=64), server_default="", nullable=False))
        if not _column_exists("interview_sessions", "interview_type"):
            op.add_column(
                "interview_sessions",
                sa.Column("interview_type", sa.String(length=32), server_default="mixed", nullable=False),
            )
        if not _column_exists("interview_sessions", "status"):
            op.add_column("interview_sessions", sa.Column("status", status_type, server_default=status_default, nullable=False))
        if not _column_exists("interview_sessions", "current_question"):
            op.add_column("interview_sessions", sa.Column("current_question", sa.Text(), server_default="", nullable=False))
        if not _column_exists("interview_sessions", "turn_count"):
            op.add_column("interview_sessions", sa.Column("turn_count", sa.Integer(), server_default="0", nullable=False))
        if not _column_exists("interview_sessions", "max_turns"):
            op.add_column("interview_sessions", sa.Column("max_turns", sa.Integer(), server_default="5", nullable=False))
        if not _column_exists("interview_sessions", "transcript_history"):
            op.add_column(
                "interview_sessions",
                sa.Column("transcript_history", json_type, server_default=json_empty_array_default, nullable=False),
            )
        if not _column_exists("interview_sessions", "evaluation_signals"):
            op.add_column(
                "interview_sessions",
                sa.Column("evaluation_signals", json_type, server_default=json_empty_object_default, nullable=False),
            )
        if not _column_exists("interview_sessions", "started_at"):
            op.add_column(
                "interview_sessions",
                sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            )
        if not _column_exists("interview_sessions", "ended_at"):
            op.add_column("interview_sessions", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
        if not _column_exists("interview_sessions", "created_at"):
            op.add_column(
                "interview_sessions",
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            )
        if not _column_exists("interview_sessions", "updated_at"):
            op.add_column(
                "interview_sessions",
                sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            )

    _create_index_if_missing("ix_interview_sessions_owner_user_id", "interview_sessions", ["owner_user_id"])
    _create_index_if_missing("ix_interview_sessions_org_id", "interview_sessions", ["org_id"])

    session_id_type = _column_type("interview_sessions", "id") or uuid_type

    if not _table_exists("conversation_transcripts"):
        op.create_table(
            "conversation_transcripts",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("speaker", speaker_type, nullable=False),
            sa.Column("message_text", sa.Text(), nullable=False),
            sa.Column("sequence_no", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "sequence_no", name="uq_transcript_sequence"),
        )

    if not _table_exists("ai_questions"):
        op.create_table(
            "ai_questions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("question_order", sa.Integer(), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "question_order", name="uq_ai_question_order"),
        )

    ai_question_id_type = _column_type("ai_questions", "id") or uuid_type

    if not _table_exists("candidate_responses"):
        op.create_table(
            "candidate_responses",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("question_id", ai_question_id_type, nullable=True),
            sa.Column("response_order", sa.Integer(), nullable=False),
            sa.Column("transcript_text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["ai_questions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "response_order", name="uq_candidate_response_order"),
        )

    if not _table_exists("evaluation_summary"):
        op.create_table(
            "evaluation_summary",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("technical_accuracy", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("communication_clarity", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("confidence", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("overall_rating", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("summary_text", sa.Text(), server_default="", nullable=False),
            sa.Column("signals_json", json_type, server_default=json_empty_object_default, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id"),
        )

    if not _table_exists("interview_turns"):
        op.create_table(
            "interview_turns",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("question_id", ai_question_id_type, nullable=True),
            sa.Column("turn_no", sa.Integer(), nullable=False),
            sa.Column("competency_key", sa.String(length=80), nullable=False),
            sa.Column("candidate_transcript", sa.Text(), nullable=False),
            sa.Column("answer_quality_score", sa.Float(), nullable=False),
            sa.Column("is_follow_up", sa.Boolean(), nullable=False),
            sa.Column("latency_ms", sa.Integer(), nullable=False),
            sa.Column("stt_confidence", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["ai_questions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", "turn_no", name="uq_interview_turn_no"),
        )
    _create_index_if_missing("ix_interview_turns_session_id", "interview_turns", ["session_id"])

    interview_turn_id_type = _column_type("interview_turns", "id") or uuid_type

    if not _table_exists("turn_scores"):
        op.create_table(
            "turn_scores",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("turn_id", interview_turn_id_type, nullable=False),
            sa.Column("technical_correctness", sa.Float(), nullable=False),
            sa.Column("problem_solving_debugging", sa.Float(), nullable=False),
            sa.Column("architecture_design", sa.Float(), nullable=False),
            sa.Column("communication_clarity", sa.Float(), nullable=False),
            sa.Column("tradeoff_reasoning", sa.Float(), nullable=False),
            sa.Column("professional_integrity", sa.Float(), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False),
            sa.Column("weighted_score", sa.Float(), nullable=False),
            sa.Column("evidence_snippet", sa.Text(), nullable=False),
            sa.Column("coverage_update", json_type, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["turn_id"], ["interview_turns.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("turn_id"),
        )

    if not _table_exists("integrity_events"):
        op.create_table(
            "integrity_events",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("turn_id", interview_turn_id_type, nullable=True),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("severity", sa.Float(), nullable=False),
            sa.Column("details", json_type, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["turn_id"], ["interview_turns.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_integrity_events_session_id", "integrity_events", ["session_id"])
    _create_index_if_missing("ix_integrity_events_event_type", "integrity_events", ["event_type"])

    if not _table_exists("usage_ledger"):
        op.create_table(
            "usage_ledger",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("org_id", sa.String(length=128), nullable=False),
            sa.Column("session_id", session_id_type, nullable=True),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("input_tokens", sa.Integer(), nullable=False),
            sa.Column("output_tokens", sa.Integer(), nullable=False),
            sa.Column("audio_seconds", sa.Float(), nullable=False),
            sa.Column("cost_usd", sa.Float(), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_usage_ledger_org_id", "usage_ledger", ["org_id"])
    _create_index_if_missing("ix_usage_ledger_session_id", "usage_ledger", ["session_id"])
    _create_index_if_missing("ix_usage_ledger_model", "usage_ledger", ["model"])

    if not _table_exists("competencies"):
        op.create_table(
            "competencies",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("domain", sa.String(length=100), nullable=False),
            sa.Column("competency_key", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("competency_key"),
        )
    _create_index_if_missing("ix_competencies_domain", "competencies", ["domain"])

    if not _table_exists("role_competencies"):
        op.create_table(
            "role_competencies",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("role_name", sa.String(length=200), nullable=False),
            sa.Column("competency_id", _column_type("competencies", "id") or uuid_type, nullable=False),
            sa.Column("weight", sa.Float(), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("role_name", "competency_id", name="uq_role_competency"),
        )
    _create_index_if_missing("ix_role_competencies_role_name", "role_competencies", ["role_name"])

    if not _table_exists("question_bank"):
        op.create_table(
            "question_bank",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("competency_id", _column_type("competencies", "id") or uuid_type, nullable=True),
            sa.Column("domain", sa.String(length=100), nullable=False),
            sa.Column("role_hint", sa.String(length=200), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("question_type", sa.String(length=80), nullable=False),
            sa.Column("difficulty", sa.Integer(), nullable=False),
            sa.Column("tags", json_type, nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("interview_plans"):
        op.create_table(
            "interview_plans",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("detected_domain", sa.String(length=100), nullable=False),
            sa.Column("coverage_policy", json_type, nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id"),
        )

    if not _table_exists("interview_plan_items"):
        op.create_table(
            "interview_plan_items",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("plan_id", _column_type("interview_plans", "id") or uuid_type, nullable=False),
            sa.Column("competency_id", _column_type("competencies", "id") or uuid_type, nullable=True),
            sa.Column("competency_key", sa.String(length=100), nullable=False),
            sa.Column("target_turns", sa.Integer(), nullable=False),
            sa.Column("covered_turns", sa.Integer(), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["plan_id"], ["interview_plans.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("plan_id", "competency_key", name="uq_plan_competency_key"),
        )

    if not _table_exists("final_assessments"):
        op.create_table(
            "final_assessments",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("overall_score", sa.Float(), nullable=False),
            sa.Column("competency_coverage", sa.Float(), nullable=False),
            sa.Column("strengths", json_type, nullable=False),
            sa.Column("weaknesses", json_type, nullable=False),
            sa.Column("recommendation", sa.String(length=50), nullable=False),
            sa.Column("summary_text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id"),
        )

    if not _table_exists("recruiter_reviews"):
        op.create_table(
            "recruiter_reviews",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("session_id", session_id_type, nullable=False),
            sa.Column("reviewer_user_id", sa.String(length=128), nullable=False),
            sa.Column("decision", sa.String(length=64), nullable=False),
            sa.Column("override_recommendation", sa.Boolean(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_recruiter_reviews_session_id", "recruiter_reviews", ["session_id"])
    _create_index_if_missing("ix_recruiter_reviews_reviewer_user_id", "recruiter_reviews", ["reviewer_user_id"])


def downgrade() -> None:
    _drop_index_if_exists("ix_recruiter_reviews_reviewer_user_id", "recruiter_reviews")
    _drop_index_if_exists("ix_recruiter_reviews_session_id", "recruiter_reviews")
    if _table_exists("recruiter_reviews"):
        op.drop_table("recruiter_reviews")

    if _table_exists("final_assessments"):
        op.drop_table("final_assessments")

    if _table_exists("interview_plan_items"):
        op.drop_table("interview_plan_items")

    if _table_exists("interview_plans"):
        op.drop_table("interview_plans")

    if _table_exists("question_bank"):
        op.drop_table("question_bank")

    _drop_index_if_exists("ix_role_competencies_role_name", "role_competencies")
    if _table_exists("role_competencies"):
        op.drop_table("role_competencies")

    _drop_index_if_exists("ix_competencies_domain", "competencies")
    if _table_exists("competencies"):
        op.drop_table("competencies")

    _drop_index_if_exists("ix_usage_ledger_model", "usage_ledger")
    _drop_index_if_exists("ix_usage_ledger_session_id", "usage_ledger")
    _drop_index_if_exists("ix_usage_ledger_org_id", "usage_ledger")
    if _table_exists("usage_ledger"):
        op.drop_table("usage_ledger")

    _drop_index_if_exists("ix_integrity_events_event_type", "integrity_events")
    _drop_index_if_exists("ix_integrity_events_session_id", "integrity_events")
    if _table_exists("integrity_events"):
        op.drop_table("integrity_events")

    if _table_exists("turn_scores"):
        op.drop_table("turn_scores")

    _drop_index_if_exists("ix_interview_turns_session_id", "interview_turns")
    if _table_exists("interview_turns"):
        op.drop_table("interview_turns")

    _drop_index_if_exists("ix_interview_sessions_org_id", "interview_sessions")
    _drop_index_if_exists("ix_interview_sessions_owner_user_id", "interview_sessions")
    if _column_exists("interview_sessions", "domain"):
        op.drop_column("interview_sessions", "domain")
    if _column_exists("interview_sessions", "org_id"):
        op.drop_column("interview_sessions", "org_id")
    if _column_exists("interview_sessions", "owner_user_id"):
        op.drop_column("interview_sessions", "owner_user_id")
