"""profile parity and role-aware signup fields

Revision ID: 20260321_0003
Revises: 20260321_0002
Create Date: 2026-03-21 00:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_0003"
down_revision: str | None = "20260321_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'student'")

    op.add_column("users", sa.Column("role_contact_email", sa.String(length=320), nullable=True))
    op.create_index("ix_users_role_contact_email", "users", ["role_contact_email"], unique=True)

    op.add_column(
        "candidate_profiles",
        sa.Column(
            "role_profile",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column(
        "candidate_profiles",
        "years_experience",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="years_experience::double precision",
    )


def downgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "years_experience",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="round(years_experience)::integer",
    )
    op.drop_column("candidate_profiles", "role_profile")

    op.drop_index("ix_users_role_contact_email", table_name="users")
    op.drop_column("users", "role_contact_email")

    # PostgreSQL enum values cannot be dropped safely in-place; retaining `student` is intentional.
