from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.email == email)
        return await self.session.scalar(stmt)

    async def get_by_role_contact_email(self, role_contact_email: str) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.role_contact_email == role_contact_email)
        return await self.session.scalar(stmt)

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.id == user_id)
        return await self.session.scalar(stmt)

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
