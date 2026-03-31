"""initial platform schema

Revision ID: 20260320_0001
Revises:
Create Date: 2026-03-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260320_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    user_role = postgresql.ENUM("candidate", "recruiter", "admin", name="user_role", create_type=False)
    resume_source_type = postgresql.ENUM("upload", "pasted_text", name="resume_source_type", create_type=False)
    resume_parse_status = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="resume_parse_status",
        create_type=False,
    )
    interview_status = postgresql.ENUM(
        "created",
        "ready",
        "active",
        "paused",
        "completed",
        "failed",
        name="interview_status",
        create_type=False,
    )
    interview_mode = postgresql.ENUM("behavioral", "technical", "mixed", name="interview_mode", create_type=False)
    job_type = postgresql.ENUM("resume_analysis", "interview_summary", name="job_type", create_type=False)
    job_status = postgresql.ENUM("queued", "running", "succeeded", "failed", name="job_status", create_type=False)

    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    resume_source_type.create(bind, checkfirst=True)
    resume_parse_status.create(bind, checkfirst=True)
    interview_status.create(bind, checkfirst=True)
    interview_mode.create(bind, checkfirst=True)
    job_type.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=512), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"], unique=True)

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", resume_source_type, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=True),
        sa.Column("parse_status", resume_parse_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"], unique=False)

    op.create_table(
        "resume_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extracted_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("analysis_version", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id"),
    )
    op.create_index("ix_resume_analyses_resume_id", "resume_analyses", ["resume_id"], unique=True)

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_target", sa.String(length=255), nullable=False),
        sa.Column("status", interview_status, nullable=False),
        sa.Column("session_mode", interview_mode, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"], unique=False)

    op.create_table(
        "interview_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("interviewer_message", sa.Text(), nullable=False),
        sa.Column("candidate_message", sa.Text(), nullable=True),
        sa.Column("model_feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score_overall", sa.Float(), nullable=True),
        sa.Column("score_communication", sa.Float(), nullable=True),
        sa.Column("score_technical", sa.Float(), nullable=True),
        sa.Column("score_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_session_turn_index"),
    )
    op.create_index("ix_interview_turns_session_id", "interview_turns", ["session_id"], unique=False)

    op.create_table(
        "interview_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=100), nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("improvement_areas", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_interview_summaries_session_id", "interview_summaries", ["session_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=200), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False)
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_jti", sa.String(length=255), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_token_jti", "refresh_tokens", ["token_jti"], unique=True)

    op.create_table(
        "platform_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_jobs_user_id", "platform_jobs", ["user_id"], unique=False)
    op.create_index("ix_platform_jobs_job_type", "platform_jobs", ["job_type"], unique=False)
    op.create_index("ix_platform_jobs_status", "platform_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_platform_jobs_status", table_name="platform_jobs")
    op.drop_index("ix_platform_jobs_job_type", table_name="platform_jobs")
    op.drop_index("ix_platform_jobs_user_id", table_name="platform_jobs")
    op.drop_table("platform_jobs")

    op.drop_index("ix_refresh_tokens_token_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_interview_summaries_session_id", table_name="interview_summaries")
    op.drop_table("interview_summaries")

    op.drop_index("ix_interview_turns_session_id", table_name="interview_turns")
    op.drop_table("interview_turns")

    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")

    op.drop_index("ix_resume_analyses_resume_id", table_name="resume_analyses")
    op.drop_table("resume_analyses")

    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")

    op.drop_index("ix_candidate_profiles_user_id", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="job_status").drop(bind, checkfirst=True)
    sa.Enum(name="job_type").drop(bind, checkfirst=True)
    sa.Enum(name="interview_mode").drop(bind, checkfirst=True)
    sa.Enum(name="interview_status").drop(bind, checkfirst=True)
    sa.Enum(name="resume_parse_status").drop(bind, checkfirst=True)
    sa.Enum(name="resume_source_type").drop(bind, checkfirst=True)
    sa.Enum(name="user_role").drop(bind, checkfirst=True)
