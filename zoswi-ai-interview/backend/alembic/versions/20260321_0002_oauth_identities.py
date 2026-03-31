"""oauth identities

Revision ID: 20260321_0002
Revises: 20260320_0001
Create Date: 2026-03-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_0002"
down_revision: str | None = "20260320_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index("ix_oauth_identities_user_id", "oauth_identities", ["user_id"], unique=False)
    op.create_index("ix_oauth_identities_provider", "oauth_identities", ["provider"], unique=False)
    op.create_index(
        "ix_oauth_identities_provider_user_id",
        "oauth_identities",
        ["provider_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_oauth_identities_provider_user_id", table_name="oauth_identities")
    op.drop_index("ix_oauth_identities_provider", table_name="oauth_identities")
    op.drop_index("ix_oauth_identities_user_id", table_name="oauth_identities")
    op.drop_table("oauth_identities")

