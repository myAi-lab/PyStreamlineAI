from uuid import UUID

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import WorkspaceMessage, WorkspaceSession
from app.utils.time import utcnow


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, workspace_session: WorkspaceSession) -> WorkspaceSession:
        self.session.add(workspace_session)
        await self.session.flush()
        return workspace_session

    async def list_sessions_for_user(self, user_id: UUID) -> list[WorkspaceSession]:
        stmt: Select[tuple[WorkspaceSession]] = (
            select(WorkspaceSession)
            .where(WorkspaceSession.user_id == user_id)
            .order_by(desc(WorkspaceSession.updated_at))
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_session_for_user(self, *, user_id: UUID, session_id: UUID) -> WorkspaceSession | None:
        stmt: Select[tuple[WorkspaceSession]] = select(WorkspaceSession).where(
            WorkspaceSession.id == session_id,
            WorkspaceSession.user_id == user_id,
        )
        return await self.session.scalar(stmt)

    async def create_message(self, message: WorkspaceMessage) -> WorkspaceMessage:
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, session_id: UUID, *, limit: int | None = None) -> list[WorkspaceMessage]:
        stmt: Select[tuple[WorkspaceMessage]] = (
            select(WorkspaceMessage)
            .where(WorkspaceMessage.session_id == session_id)
            .order_by(WorkspaceMessage.created_at.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_last_message(self, session_id: UUID) -> WorkspaceMessage | None:
        stmt: Select[tuple[WorkspaceMessage]] = (
            select(WorkspaceMessage)
            .where(WorkspaceMessage.session_id == session_id)
            .order_by(WorkspaceMessage.created_at.desc())
        )
        return await self.session.scalar(stmt)

    async def count_messages(self, session_id: UUID) -> int:
        stmt = select(func.count(WorkspaceMessage.id)).where(WorkspaceMessage.session_id == session_id)
        value = await self.session.scalar(stmt)
        return int(value or 0)

    async def touch_session(self, workspace_session: WorkspaceSession) -> None:
        workspace_session.updated_at = utcnow()
        await self.session.flush()
