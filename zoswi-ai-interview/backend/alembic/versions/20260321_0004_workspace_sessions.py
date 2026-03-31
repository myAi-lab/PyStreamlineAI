"""workspace sessions and messages

Revision ID: 20260321_0004
Revises: 20260321_0003
Create Date: 2026-03-21 01:15:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_0004"
down_revision: str | None = "20260321_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspace_sessions_user_id", "workspace_sessions", ["user_id"], unique=False)
    op.create_index("ix_workspace_sessions_updated_at", "workspace_sessions", ["updated_at"], unique=False)

    op.create_table(
        "workspace_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=30), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["workspace_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspace_messages_session_id", "workspace_messages", ["session_id"], unique=False)
    op.create_index("ix_workspace_messages_created_at", "workspace_messages", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workspace_messages_created_at", table_name="workspace_messages")
    op.drop_index("ix_workspace_messages_session_id", table_name="workspace_messages")
    op.drop_table("workspace_messages")

    op.drop_index("ix_workspace_sessions_updated_at", table_name="workspace_sessions")
    op.drop_index("ix_workspace_sessions_user_id", table_name="workspace_sessions")
    op.drop_table("workspace_sessions")
