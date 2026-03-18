from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()


def _normalize_database_url(database_url: str) -> str:
    normalized = str(database_url or "").strip()

    # Render/Supabase often provide postgres:// or postgresql:// URLs.
    # This backend uses psycopg v3, so force the compatible SQLAlchemy driver.
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)
    if normalized.startswith("postgresql+psycopg2://"):
        normalized = normalized.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    elif normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

    return normalized


engine = create_async_engine(
    _normalize_database_url(settings.database_url),
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _run_lightweight_migrations(connection)


async def _run_lightweight_migrations(connection) -> None:
    dialect_name = str(connection.dialect.name).strip().lower()
    if dialect_name == "sqlite":
        pragma_result = await connection.execute(text("PRAGMA table_info(interview_sessions)"))
        columns = {str(row[1]) for row in pragma_result.fetchall()}
        if "interview_type" not in columns:
            await connection.execute(
                text("ALTER TABLE interview_sessions ADD COLUMN interview_type VARCHAR(32) NOT NULL DEFAULT 'mixed'")
            )
        return

    if dialect_name in {"postgresql", "postgres"}:
        exists_result = await connection.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'interview_sessions'
                  AND column_name = 'interview_type'
                LIMIT 1
                """
            )
        )
        if exists_result.first() is None:
            await connection.execute(
                text(
                    "ALTER TABLE interview_sessions "
                    "ADD COLUMN IF NOT EXISTS interview_type VARCHAR(32) NOT NULL DEFAULT 'mixed'"
                )
            )
