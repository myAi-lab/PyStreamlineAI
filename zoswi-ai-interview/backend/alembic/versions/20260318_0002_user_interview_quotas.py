"""Add per-user interview quota table.

Revision ID: 20260318_0002
Revises: 20260318_0001
Create Date: 2026-03-18 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260318_0002"
down_revision: Union[str, None] = "20260318_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspector().get_table_names())


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(str(index.get("name")) == index_name for index in _inspector().get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("user_interview_quotas"):
        op.create_table(
            "user_interview_quotas",
            sa.Column("user_id", sa.String(length=128), nullable=False),
            sa.Column("total_chances", sa.Integer(), server_default="3", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.PrimaryKeyConstraint("user_id"),
        )
    if not _index_exists("user_interview_quotas", "ix_user_interview_quotas_total_chances"):
        op.create_index(
            "ix_user_interview_quotas_total_chances",
            "user_interview_quotas",
            ["total_chances"],
            unique=False,
        )


def downgrade() -> None:
    if _index_exists("user_interview_quotas", "ix_user_interview_quotas_total_chances"):
        op.drop_index("ix_user_interview_quotas_total_chances", table_name="user_interview_quotas")
    if _table_exists("user_interview_quotas"):
        op.drop_table("user_interview_quotas")

