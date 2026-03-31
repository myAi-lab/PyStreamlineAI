from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.user_repository import UserRepository
from app.schemas.candidate import CandidateProfileResponse, CandidateProfileUpdateRequest


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CandidateRepository(session)
        self.users = UserRepository(session)

    async def get_profile(self, user_id: UUID) -> CandidateProfileResponse:
        profile = await self.repo.get_by_user_id(user_id)
        if profile is None:
            profile = await self.repo.create_for_user(user_id)
            await self.session.commit()
            await self.session.refresh(profile)
        user = await self.users.get_by_id(user_id)
        role_contact_email = user.role_contact_email if user else None
        return CandidateProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            headline=profile.headline,
            years_experience=profile.years_experience,
            target_roles=profile.target_roles,
            location=profile.location,
            role_profile=profile.role_profile or {},
            role_contact_email=role_contact_email,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def update_profile(
        self,
        *,
        user_id: UUID,
        payload: CandidateProfileUpdateRequest,
    ) -> CandidateProfileResponse:
        profile = await self.repo.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Candidate profile not found")

        profile.headline = payload.headline
        profile.years_experience = payload.years_experience
        profile.target_roles = payload.target_roles
        profile.location = payload.location
        profile.role_profile = payload.role_profile
        user = await self.users.get_by_id(user_id)
        if user is not None:
            normalized_role_contact_email = payload.role_contact_email.lower() if payload.role_contact_email else None
            if normalized_role_contact_email:
                existing_primary = await self.users.get_by_email(normalized_role_contact_email)
                if existing_primary and existing_primary.id != user_id:
                    raise ConflictError("Role contact email is already in use")
                existing_role_contact = await self.users.get_by_role_contact_email(normalized_role_contact_email)
                if existing_role_contact and existing_role_contact.id != user_id:
                    raise ConflictError("Role contact email is already in use")
            user.role_contact_email = normalized_role_contact_email
        await self.session.commit()
        await self.session.refresh(profile)
        return CandidateProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            headline=profile.headline,
            years_experience=profile.years_experience,
            target_roles=profile.target_roles,
            location=profile.location,
            role_profile=profile.role_profile or {},
            role_contact_email=user.role_contact_email if user else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
