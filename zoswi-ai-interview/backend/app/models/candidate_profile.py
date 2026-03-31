import uuid

from sqlalchemy import Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin
from app.models.base import Base


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_profile: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    user = relationship("User", back_populates="candidate_profile")
