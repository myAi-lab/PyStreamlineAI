from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, event: AuditLog) -> AuditLog:
        self.session.add(event)
        await self.session.flush()
        return event

