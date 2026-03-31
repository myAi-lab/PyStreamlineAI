import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin
from app.models.base import Base
from app.models.enums import UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    role_contact_email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=UserRole.CANDIDATE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    candidate_profile = relationship(
        "CandidateProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("PlatformJob", back_populates="user", cascade="all, delete-orphan")
    oauth_identities = relationship(
        "OAuthIdentity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workspace_sessions = relationship(
        "WorkspaceSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
