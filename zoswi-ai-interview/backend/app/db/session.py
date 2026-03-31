from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine_kwargs: dict = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
}

if settings.database_url.startswith("postgresql+asyncpg") and settings.database_schema:
    engine_kwargs["connect_args"] = {"server_settings": {"search_path": settings.database_schema}}

engine = create_async_engine(settings.database_url, **engine_kwargs)

SessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
