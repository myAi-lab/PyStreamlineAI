from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.interview_repository import InterviewRepository
from app.services.ai_service import AIService
from app.services.interview_service import InterviewService

ai_service = AIService()


async def get_interview_service(db: AsyncSession = Depends(get_db)) -> InterviewService:
    repository = InterviewRepository(db)
    return InterviewService(repository=repository, ai_service=ai_service)


def get_ai_service() -> AIService:
    return ai_service
